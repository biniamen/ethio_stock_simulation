from decimal import Decimal
from django.db import models, transaction
from django.utils.timezone import timezone, localtime, localdate
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
import logging
from regulations.models import StockSuspension
from regulations.utils import get_regulation_value

# Configure logging
logger = logging.getLogger(__name__)
User = get_user_model()

class UsersPortfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    quantity = models.IntegerField(default=0)
    average_purchase_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_investment = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Portfolio of {self.user.username}"


class ListedCompany(models.Model):
    company_name = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name


class Stocks(models.Model):
    company = models.ForeignKey(ListedCompany, on_delete=models.CASCADE, related_name='stocks')
    ticker_symbol = models.CharField(max_length=10, unique=True)
    total_shares = models.IntegerField()
    current_price = models.DecimalField(max_digits=15, decimal_places=2)
    available_shares = models.IntegerField()
    max_trader_buy_limit = models.IntegerField(default=1000)  # Maximum shares a trader can buy directly from the company
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.ticker_symbol} ({self.company.company_name})"

    def clean(self):
        # Ensure max_trader_buy_limit does not exceed available shares
        if self.max_trader_buy_limit > self.total_shares:
            raise ValueError("Trader buy limit cannot exceed the total shares of the company.")



class Orders(models.Model):
    ORDER_TYPE_CHOICES = [
        ('Market', 'Market'),
        ('Limit', 'Limit'),
    ]
    ACTION_CHOICES = [
        ('Buy', 'Buy'),
        ('Sell', 'Sell'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Partially Completed', 'Partially Completed'),
        ('Fully Completed', 'Fully Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    stock = models.ForeignKey('stock.Stocks', on_delete=models.CASCADE, related_name='orders')
    stock_symbol = models.CharField(max_length=10)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES)
    action = models.CharField(max_length=4, choices=ACTION_CHOICES)
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.action} Order for {self.stock_symbol}"

    def save(self, *args, **kwargs):
        # Check for specific stock suspension
        stock_suspension = StockSuspension.objects.filter(
            trader=self.user, stock=self.stock, is_active=True, suspension_type='Specific Stock'
        ).exists()

        # Check for global suspension
        global_suspension = StockSuspension.objects.filter(
            trader=self.user, is_active=True, suspension_type='All Stocks'
        ).exists()

        if stock_suspension or global_suspension:
            raise ValidationError("Trading for this user is suspended.")

        # Check working hours
        working_hours = get_regulation_value("Working Hours")
        if working_hours:
            start, end = map(int, working_hours.split('-'))
            current_hour = localtime().hour
            if not (start <= current_hour < end):
                raise ValidationError("Orders cannot be created outside working hours.")

        # Check daily trade limit
        daily_trade_limit = get_regulation_value("Daily Trade Limit")
        if daily_trade_limit:
            user_trades_today = Orders.objects.filter(
                user=self.user, created_at__date=localdate()
            ).count()
            if user_trades_today >= int(daily_trade_limit):
                raise ValidationError("Daily trade limit reached.")

        # Save the order and execute logic
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            Orders.match_and_execute_orders(self)

    @classmethod
    def match_and_execute_orders(cls, new_order):
        with transaction.atomic():
            if new_order.action == 'Buy':
                cls._handle_buy_order(new_order)

    @classmethod
    def _handle_buy_order(cls, buy_order):
        stock = buy_order.stock
        trade_quantity = 0

        # Step 1: Check if the company has enough available shares
        if stock.available_shares > 0:
            # Fetch the total quantity of shares already traded by the user for this stock
            total_traded_quantity = Trade.objects.filter(user=buy_order.user, stock=stock).aggregate(
                total_quantity=models.Sum('quantity')
            )['total_quantity'] or 0  # Default to 0 if no trade history exists

            # Calculate the total shares if this order is executed
            total_quantity = total_traded_quantity + buy_order.quantity

            # Check if the total shares exceed the limit
            if total_quantity > stock.max_trader_buy_limit:
                # Delete the saved order
                buy_order.delete()
                raise ValidationError({
                    "error": "Order exceeds the allowed limit.",
                    "details": {
                        "max_limit": stock.max_trader_buy_limit,
                        "current_traded_quantity": total_traded_quantity,
                        "requested_quantity": buy_order.quantity,
                        "total_quantity": total_quantity
                    }
                })

            trade_quantity = min(buy_order.quantity, stock.available_shares)
            stock.available_shares -= trade_quantity
            stock.save()

            cls._update_portfolio(buy_order, trade_quantity, stock.current_price, is_company=True)

            buy_order.quantity -= trade_quantity
            if buy_order.quantity == 0:
                buy_order.status = 'Fully Completed'
            else:
                buy_order.status = 'Partially Completed'
            buy_order.save()

        # Step 2: Match with trader sell orders if stock from the company is insufficient
        if buy_order.quantity > 0:
            sell_orders = cls.objects.filter(
                stock=stock,
                action='Sell',
                status='Pending',
                price__lte=buy_order.price,
            ).order_by('price', 'created_at')

            for sell_order in sell_orders:
                if buy_order.quantity == 0:
                    break

                if sell_order.stock == stock:
                    trade_quantity = min(buy_order.quantity, sell_order.quantity)
                    trade_price = sell_order.price

                    Trade.execute_trade(buy_order, sell_order, trade_quantity, trade_price)

                    cls._update_portfolio(buy_order, trade_quantity, trade_price)
                    cls._update_portfolio(sell_order, trade_quantity, trade_price)

                    buy_order.quantity -= trade_quantity
                    sell_order.quantity -= trade_quantity

                    if buy_order.quantity == 0:
                        buy_order.status = 'Fully Completed'
                    else:
                        buy_order.status = 'Partially Completed'

                    if sell_order.quantity == 0:
                        sell_order.status = 'Fully Completed'
                    else:
                        sell_order.status = 'Partially Completed'

                    buy_order.save()
                    sell_order.save()

    @staticmethod
    def _update_portfolio(order, quantity, price, is_company=False):
        """
        Update the user's portfolio based on the order.
        """
        from decimal import Decimal

        portfolio, _ = UsersPortfolio.objects.get_or_create(user=order.user)
        quantity = Decimal(quantity)  # Ensure quantity is a Decimal
        price = Decimal(price)        # Ensure price is a Decimal

        if order.action == 'Buy':
            portfolio.quantity += quantity
            portfolio.total_investment += quantity * price
            if portfolio.quantity > 0:
                portfolio.average_purchase_price = portfolio.total_investment / portfolio.quantity
        elif order.action == 'Sell' and not is_company:
            portfolio.quantity -= quantity
            portfolio.total_investment -= quantity * price
            if portfolio.quantity > 0:
                portfolio.average_purchase_price = portfolio.total_investment / portfolio.quantity
            else:
                portfolio.average_purchase_price = Decimal('0.00')  # Reset to 0 if no stocks remain
        portfolio.save()



class Trade(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades')
    stock = models.ForeignKey(Stocks, on_delete=models.CASCADE, related_name='trades')
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    trade_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Trade by {self.user.username}"

    @classmethod
    def execute_trade(cls, buy_order, sell_order, quantity, price=None):
        if price is None:
            price = sell_order.stock.current_price
        cls.objects.create(user=buy_order.user, stock=buy_order.stock, quantity=quantity, price=price)
        cls.objects.create(user=sell_order.user, stock=sell_order.stock, quantity=quantity, price=price)


class Dividend(models.Model):
    company = models.ForeignKey(ListedCompany, on_delete=models.CASCADE, related_name='dividends')
    budget_year = models.CharField(max_length=4)
    dividend_ratio = models.DecimalField(max_digits=5, decimal_places=2)
    total_dividend_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=15, choices=[('Paid', 'Paid'), ('Pending', 'Pending')], default='Pending')

    def __str__(self):
        return f"Dividend for {self.company.company_name} ({self.budget_year})"
