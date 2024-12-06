from decimal import Decimal
from django.db import models, transaction
from django.utils.timezone import timezone, localtime, localdate
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
import logging
from regulations.models import StockSuspension
from regulations.utils import get_regulation_value
from regulations.models import StockSuspension, WorkingHours


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
    stock = models.ForeignKey('stocks.Stocks', on_delete=models.CASCADE, related_name='orders')
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
    # Check for active stock suspensions
        stock_suspension = StockSuspension.objects.filter(
            trader=self.user, stock=self.stock, is_active=True, suspension_type='Specific Stock'
        ).exists()

        global_suspension = StockSuspension.objects.filter(
            trader=self.user, is_active=True, suspension_type='All Stocks'
        ).exists()

        if stock_suspension or global_suspension:
            raise ValidationError("Trading for this user is suspended.")

        # Check working hours using WorkingHours table
        current_time = localtime()
        current_day = current_time.strftime('%A')
        current_hour = current_time.time()

        try:
            working_hours = WorkingHours.objects.get(day_of_week=current_day)
            if not (working_hours.start_time <= current_hour <= working_hours.end_time):
                self.status = 'Cancelled'
                raise ValidationError("Orders cannot be created outside working hours.")
        except WorkingHours.DoesNotExist:
            raise ValidationError("Working hours are not configured for this day.")

        # Check daily trade limit (if applicable)
        from regulations.utils import get_regulation_value
        daily_trade_limit = get_regulation_value("Daily Trade Limit")
        if daily_trade_limit:
            user_trades_today = Orders.objects.filter(
                user=self.user, created_at__date=localdate()
            ).count()
            if user_trades_today >= int(daily_trade_limit):
                raise ValidationError("Daily trade limit reached.")

        # Ensure the user has a portfolio
        portfolio, created = UsersPortfolio.objects.get_or_create(
            user=self.user,
            defaults={
                'quantity': 0,
                'average_purchase_price': Decimal('0.00'),
                'total_investment': Decimal('0.00'),
            }
        )

        # Validate Buy Order: Ensure sufficient account balance
        if self.action == 'Buy':
            total_cost = Decimal(self.price) * Decimal(self.quantity)
            if self.user.account_balance < total_cost:
                raise ValidationError("Insufficient account balance to place a buy order.")

        # Validate Sell Order: Ensure sufficient stock ownership
        if self.action == 'Sell':
            owned_quantity = Trade.objects.filter(
                user=self.user,
                stock=self.stock,
            ).aggregate(total_quantity=models.Sum('quantity'))['total_quantity'] or 0

            if owned_quantity < self.quantity:
                raise ValidationError("You do not own enough stock to place this sell order.")

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
            elif new_order.action == 'Sell':
                cls._handle_sell_order(new_order)

    @classmethod
    def _handle_buy_order(cls, buy_order):
        """
        Handles the execution of Buy orders based on order type and price-time priority.
        """
        stock = buy_order.stock

        # Step 1: Handle Market Orders
        if buy_order.order_type == 'Market':
            # Check if the company has available stock
            if stock.available_shares > 0:
                trade_quantity = min(buy_order.quantity, stock.available_shares)
                trade_price = stock.current_price  # Market orders take the company's current price

                # Execute the trade with the company
                Trade.objects.create(
                    user=buy_order.user,
                    stock=stock,
                    quantity=trade_quantity,
                    price=trade_price,
                )

                # Deduct the cost from the user's account balance
                total_cost = trade_quantity * trade_price
                buy_order.user.update_account_balance(-total_cost)

                # Update the user's portfolio
                cls._update_portfolio(buy_order.user, stock, trade_quantity, trade_price, is_buy=True)

                # Update the company's available stock
                stock.available_shares -= trade_quantity
                stock.save()

                # Adjust the order quantity
                buy_order.quantity -= trade_quantity
                if buy_order.quantity == 0:
                    buy_order.status = 'Fully Completed'
                else:
                    buy_order.status = 'Partially Completed'

                buy_order.save()

            # If the order is not fully fulfilled, check other traders' sell orders
            if buy_order.quantity > 0:
                sell_orders = cls.objects.filter(
                    stock=stock,
                    action='Sell',
                    status='Pending'
                ).order_by('price', 'created_at')  # Lowest price first, earliest order next

                for sell_order in sell_orders:
                    if buy_order.quantity == 0:
                        break

                    trade_quantity = min(buy_order.quantity, sell_order.quantity)
                    trade_price = sell_order.price

                    # Execute the trade
                    Trade.execute_trade(buy_order, sell_order, trade_quantity, trade_price)

                    # Deduct the cost from the buyer's account balance
                    total_cost = trade_quantity * trade_price
                    buy_order.user.update_account_balance(-total_cost)

                    # Update the buyer's portfolio
                    cls._update_portfolio(buy_order.user, stock, trade_quantity, trade_price, is_buy=True)

                    # Update the seller's portfolio
                    cls._update_portfolio(sell_order.user, stock, trade_quantity, trade_price, is_buy=False)

                    # Adjust quantities and statuses
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

        # Step 2: Handle Limit Orders
        elif buy_order.order_type == 'Limit':
            # Step 2.1: Check company stock price and availability
            if stock.available_shares > 0 and stock.current_price <= buy_order.price:
                trade_quantity = min(buy_order.quantity, stock.available_shares)
                trade_price = stock.current_price  # Use the company's price for the trade

                # Execute the trade with the company
                Trade.objects.create(
                    user=buy_order.user,
                    stock=stock,
                    quantity=trade_quantity,
                    price=trade_price,
                )

                # Deduct the cost from the user's account balance
                total_cost = trade_quantity * trade_price
                buy_order.user.update_account_balance(-total_cost)

                # Update the user's portfolio
                cls._update_portfolio(buy_order.user, stock, trade_quantity, trade_price, is_buy=True)

                # Update the company's available stock
                stock.available_shares -= trade_quantity
                stock.save()

                # Adjust the order quantity
                buy_order.quantity -= trade_quantity
                if buy_order.quantity == 0:
                    buy_order.status = 'Fully Completed'
                else:
                    buy_order.status = 'Partially Completed'

                buy_order.save()

            # Step 2.2: Check other traders' sell orders
            if buy_order.quantity > 0:
                sell_orders = cls.objects.filter(
                    stock=stock,
                    action='Sell',
                    status='Pending',
                    price__lte=buy_order.price
                ).order_by('price', 'created_at')  # Lowest price first, earliest order next

                for sell_order in sell_orders:
                    if buy_order.quantity == 0:
                        break

                    trade_quantity = min(buy_order.quantity, sell_order.quantity)
                    trade_price = sell_order.price

                    # Execute the trade
                    Trade.execute_trade(buy_order, sell_order, trade_quantity, trade_price)

                    # Deduct the cost from the buyer's account balance
                    total_cost = trade_quantity * trade_price
                    buy_order.user.update_account_balance(-total_cost)

                    # Update the buyer's portfolio
                    cls._update_portfolio(buy_order.user, stock, trade_quantity, trade_price, is_buy=True)

                    # Update the seller's portfolio
                    cls._update_portfolio(sell_order.user, stock, trade_quantity, trade_price, is_buy=False)

                    # Adjust quantities and statuses
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

            # Step 2.3: Cancel unfulfilled Limit Orders at the end of the day
            if buy_order.quantity > 0:
                current_time = localtime()
                end_of_day = current_time.replace(hour=23, minute=59, second=59)

                if current_time >= end_of_day:
                    buy_order.status = 'Cancelled'
                    buy_order.save()

    @classmethod
    def _handle_sell_order(cls, sell_order):
        """
        Handles the execution of Sell orders based on order type and price-time priority.
        """
        stock = sell_order.stock

        # Step 1: Check if the user owns enough stock in the Trade table
        total_owned_quantity = Trade.objects.filter(
            user=sell_order.user,
            stock=stock
        ).aggregate(total_quantity=models.Sum('quantity'))['total_quantity'] or 0

        if total_owned_quantity < sell_order.quantity:
            sell_order.status = 'Cancelled'
            sell_order.save()
            raise ValidationError("Insufficient stock to sell.")

        # Step 2: Handle Market Orders
        if sell_order.order_type == 'Market':
            # Match with all buy orders (highest price first, then earliest time)
            buy_orders = cls.objects.filter(
                stock=stock,
                action='Buy',
                status='Pending'
            ).order_by('-price', 'created_at')  # Highest price first, earliest order next

            for buy_order in buy_orders:
                if sell_order.quantity == 0:
                    break

                # Calculate trade quantity and price
                trade_quantity = min(sell_order.quantity, buy_order.quantity)
                trade_price = buy_order.price  # Market orders take the price from the matched buy order

                # Execute the trade
                Trade.execute_trade(buy_order, sell_order, trade_quantity, trade_price)

                # Credit total proceeds to seller's account balance
                total_proceeds = trade_quantity * trade_price
                sell_order.user.update_account_balance(total_proceeds)

                # Update seller's portfolio
                cls._update_portfolio(sell_order.user, stock, trade_quantity, trade_price, is_buy=False)

                # Adjust quantities and statuses
                sell_order.quantity -= trade_quantity
                buy_order.quantity -= trade_quantity

                if sell_order.quantity == 0:
                    sell_order.status = 'Fully Completed'
                else:
                    sell_order.status = 'Partially Completed'

                if buy_order.quantity == 0:
                    buy_order.status = 'Fully Completed'
                else:
                    buy_order.status = 'Partially Completed'

                sell_order.save()
                buy_order.save()

        # Step 3: Handle Limit Orders
        elif sell_order.order_type == 'Limit':
            # Match only with buy orders priced at or above the limit price
            buy_orders = cls.objects.filter(
                stock=stock,
                action='Buy',
                status='Pending',
                price__gte=sell_order.price
            ).order_by('-price', 'created_at')  # Highest price first, earliest order next

            for buy_order in buy_orders:
                if sell_order.quantity == 0:
                    break

                # Calculate trade quantity and price
                trade_quantity = min(sell_order.quantity, buy_order.quantity)
                trade_price = buy_order.price

                # Execute the trade
                Trade.execute_trade(buy_order, sell_order, trade_quantity, trade_price)

                # Credit total proceeds to seller's account balance
                total_proceeds = trade_quantity * trade_price
                sell_order.user.update_account_balance(total_proceeds)

                # Update seller's portfolio
                cls._update_portfolio(sell_order.user, stock, trade_quantity, trade_price, is_buy=False)

                # Adjust quantities and statuses
                sell_order.quantity -= trade_quantity
                buy_order.quantity -= trade_quantity

                if sell_order.quantity == 0:
                    sell_order.status = 'Fully Completed'
                else:
                    sell_order.status = 'Partially Completed'

                if buy_order.quantity == 0:
                    buy_order.status = 'Fully Completed'
                else:
                    buy_order.status = 'Partially Completed'

                sell_order.save()
                buy_order.save()

            # If no matching orders are found, cancel the Limit order at the end of the day
            if sell_order.quantity > 0:
                # Assuming we have a scheduled job to check orders at the end of the day
                sell_order.status = 'Cancelled'
                sell_order.save()

    
    @staticmethod
    def _update_portfolio(user, stock, quantity, price, is_buy):
        """
        Updates the user's portfolio based on the trade. 
        This method is invoked after trade execution.
        """
        portfolio, _ = UsersPortfolio.objects.get_or_create(user=user)
        quantity = Decimal(quantity)
        price = Decimal(price)

        if is_buy:
            portfolio.quantity += quantity
            portfolio.total_investment += quantity * price
            if portfolio.quantity > 0:
                portfolio.average_purchase_price = portfolio.total_investment / portfolio.quantity
        else:  # Sell
            portfolio.quantity -= quantity
            portfolio.total_investment -= quantity * price
            if portfolio.quantity > 0:
                portfolio.average_purchase_price = portfolio.total_investment / portfolio.quantity
            else:
                portfolio.average_purchase_price = Decimal('0.00')  # Reset if no stocks remain

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
