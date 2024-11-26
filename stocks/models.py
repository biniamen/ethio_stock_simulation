from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
import logging

# Configure logging
logger = logging.getLogger(__name__)
User = get_user_model()


# Users Portfolio Table
class UsersPortfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    quantity = models.IntegerField(default=0)
    average_purchase_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_investment = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Portfolio of {self.user.username}"


# Listed Company Table
class ListedCompany(models.Model):
    company_name = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name


# Stocks Table
class Stocks(models.Model):
    company = models.ForeignKey(ListedCompany, on_delete=models.CASCADE, related_name='stocks')
    ticker_symbol = models.CharField(max_length=10, unique=True)
    total_shares = models.IntegerField()
    current_price = models.DecimalField(max_digits=15, decimal_places=2)
    available_shares = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.ticker_symbol} ({self.company.company_name})"


# Orders Table
class Orders(models.Model):
    ORDER_TYPE_CHOICES = [
        ('Market', 'Market'),
        ('Limit', 'Limit'),
        ('Stop', 'Stop')
    ]
    ACTION_CHOICES = [
        ('Buy', 'Buy'),
        ('Sell', 'Sell')
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Partially Completed', 'Partially Completed'),
        ('Fully Completed', 'Fully Completed'),
        ('Cancelled', 'Cancelled')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    stock = models.ForeignKey(Stocks, on_delete=models.CASCADE, related_name='orders')
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
        """
        Override save method to ensure order matching occurs upon creation.
        """
        super().save(*args, **kwargs)
        logger.info(f"Order created: {self}")
        Orders.match_and_execute_orders()

    @classmethod
    def match_and_execute_orders(cls):
        logger.info("Starting order matching process.")
        with transaction.atomic():
            buy_orders = cls.objects.filter(action='Buy', status='Pending').order_by('-price', 'created_at')
            sell_orders = cls.objects.filter(action='Sell', status='Pending').order_by('price', 'created_at')

            for buy_order in buy_orders:
                for sell_order in sell_orders:
                    if buy_order.stock == sell_order.stock and buy_order.price >= sell_order.price:
                        trade_quantity = min(buy_order.quantity, sell_order.quantity)
                        trade_price = sell_order.price

                        # Execute the trade
                        Trade.execute_trade(buy_order, sell_order, trade_quantity)

                        # Update user portfolios and balances
                        Orders.update_portfolios_and_balances(buy_order, sell_order, trade_quantity, trade_price)

                        # Update order quantities and statuses
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

                        logger.info(f"Trade executed: Buy Order ID {buy_order.id}, Sell Order ID {sell_order.id}, Quantity: {trade_quantity}")

                        # Stop matching if either order is fully completed
                        if buy_order.quantity == 0 or sell_order.quantity == 0:
                            break
        logger.info("Order matching process completed.")

    @staticmethod
    def update_portfolios_and_balances(buy_order, sell_order, quantity, price):
        """
        Update the portfolios and balances of the buyer and seller.
        """
        # Convert quantity and price to Decimal
        quantity = Decimal(quantity)
        price = Decimal(price)

        # Update buyer's portfolio and balance
        buyer_portfolio, _ = UsersPortfolio.objects.get_or_create(user=buy_order.user)
        buyer_portfolio.quantity += quantity
        buyer_portfolio.total_investment += quantity * price
        buyer_portfolio.average_purchase_price = buyer_portfolio.total_investment / buyer_portfolio.quantity
        buyer_portfolio.save()

        buy_order.user.balance = Decimal(buy_order.user.balance) - (quantity * price)  # Ensure balance is Decimal
        buy_order.user.save()

        # Update seller's portfolio and balance
        seller_portfolio, _ = UsersPortfolio.objects.get_or_create(user=sell_order.user)
        seller_portfolio.quantity -= quantity
        seller_portfolio.total_investment -= quantity * price
        if seller_portfolio.quantity > 0:
            seller_portfolio.average_purchase_price = seller_portfolio.total_investment / seller_portfolio.quantity
        else:
            seller_portfolio.average_purchase_price = Decimal('0.00')  # Set to 0 if no shares remain
        seller_portfolio.save()

        sell_order.user.balance = Decimal(sell_order.user.balance) + (quantity * price)  # Ensure balance is Decimal
        sell_order.user.save()


# Trade Table
class Trade(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades')
    stock = models.ForeignKey(Stocks, on_delete=models.CASCADE, related_name='trades')
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='trades')
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    profit_loss = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    trade_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Trade by {self.user.username}"

    @classmethod
    def execute_trade(cls, buy_order, sell_order, quantity):
        trade_price = sell_order.price
        cls.objects.create(
            user=buy_order.user,
            stock=buy_order.stock,
            order=buy_order,
            quantity=quantity,
            price=trade_price,
        )
        cls.objects.create(
            user=sell_order.user,
            stock=sell_order.stock,
            order=sell_order,
            quantity=quantity,
            price=trade_price,
        )
        stock = buy_order.stock
        stock.available_shares -= quantity
        stock.save()


# Transaction Log Table
class TransactionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='transactions')
    related_entity_id = models.IntegerField(null=True, blank=True)
    order_type = models.CharField(max_length=10, choices=Orders.ORDER_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Transaction for {self.user.username}"


# Dividend Table
class Dividend(models.Model):
    company = models.ForeignKey(ListedCompany, on_delete=models.CASCADE, related_name='dividends')
    budget_year = models.IntegerField()
    dividend_ratio = models.DecimalField(max_digits=10, decimal_places=2)
    total_dividend_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=50)

    def __str__(self):
        return f"Dividend for {self.company.company_name} ({self.budget_year})"
