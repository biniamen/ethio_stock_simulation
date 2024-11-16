from django.contrib import admin
from .models import (
    UsersPortfolio,
    ListedCompany,
    Stocks,
    Orders,
    Trade,
    TransactionLog,
    Dividend,
)


# Admin class to manage UsersPortfolio
@admin.register(UsersPortfolio)
class UsersPortfolioAdmin(admin.ModelAdmin):
    """
    Admin configuration for UsersPortfolio model.
    Displays portfolio details such as user, quantity of stocks, average purchase price, and total investment.
    Provides search functionality and role-based filtering.
    """
    list_display = ('user', 'quantity', 'average_purchase_price', 'total_investment')  # Fields shown in the list view
    search_fields = ('user__username',)  # Enables searching by username
    list_filter = ('user__role',)  # Filters by user roles


# Admin class to manage ListedCompany
@admin.register(ListedCompany)
class ListedCompanyAdmin(admin.ModelAdmin):
    """
    Admin configuration for ListedCompany model.
    Displays company details such as name, sector, and last updated time.
    Enables search by company name and filtering by sector.
    """
    list_display = ('id', 'company_name', 'sector', 'last_updated')  # Fields shown in the list view
    search_fields = ('company_name', 'sector')  # Enables search by company name and sector
    list_filter = ('sector',)  # Filters by sector
    ordering = ('-last_updated',)  # Orders by the most recently updated company


# Admin class to manage Stocks
@admin.register(Stocks)
class StocksAdmin(admin.ModelAdmin):
    """
    Admin configuration for Stocks model.
    Displays stock details such as ticker symbol, company, total shares, and current price.
    Enables search by stock symbol or company name and filtering by sector or creation date.
    """
    list_display = ('ticker_symbol', 'company', 'total_shares', 'current_price', 'available_shares', 'created_at')
    search_fields = ('ticker_symbol', 'company__company_name')  # Enables search by stock symbol and company name
    list_filter = ('company__sector', 'created_at')  # Filters by company sector and stock creation date
    ordering = ('-created_at',)  # Orders by the most recently created stock


# Admin class to manage Orders
@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    """
    Admin configuration for Orders model.
    Displays order details such as user, stock, order type, action, and status.
    Enables search by username or stock symbol and filtering by order type, action, and status.
    """
    list_display = ('id', 'user', 'stock', 'stock_symbol', 'order_type', 'action', 'price', 'quantity', 'status', 'created_at')
    search_fields = ('user__username', 'stock__ticker_symbol', 'stock_symbol')  # Enables search by username and stock symbol
    list_filter = ('order_type', 'action', 'status', 'created_at')  # Filters by order type, action, and status
    ordering = ('-created_at',)  # Orders by the most recently created order


# Admin class to manage Trades
@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    """
    Admin configuration for Trade model.
    Displays trade details such as user, stock, associated order, quantity, price, and profit/loss.
    Enables search by username or stock ticker symbol and filtering by trade time.
    """
    list_display = ('id', 'user', 'stock', 'order', 'quantity', 'price', 'profit_loss', 'trade_time')
    search_fields = ('user__username', 'stock__ticker_symbol')  # Enables search by username and stock ticker symbol
    list_filter = ('trade_time',)  # Filters by trade execution time
    ordering = ('-trade_time',)  # Orders by the most recent trade


# Admin class to manage TransactionLogs
@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for TransactionLog model.
    Displays transaction details such as user, related order, amount, and description.
    Enables search by user or related entity and filtering by order type and creation date.
    """
    list_display = ('id', 'user', 'order', 'related_entity_id', 'order_type', 'amount', 'description', 'created_at')
    search_fields = ('user__username', 'order__id', 'related_entity_id')  # Enables search by user and related entity
    list_filter = ('order_type', 'created_at')  # Filters by order type and creation date
    ordering = ('-created_at',)  # Orders by the most recent transaction


# Admin class to manage Dividends
@admin.register(Dividend)
class DividendAdmin(admin.ModelAdmin):
    """
    Admin configuration for Dividend model.
    Displays dividend details such as company, budget year, ratio, and total dividend amount.
    Enables search by company name or budget year and filtering by budget year or status.
    """
    list_display = ('id', 'company', 'budget_year', 'dividend_ratio', 'total_dividend_amount', 'status')
    search_fields = ('company__company_name', 'budget_year')  # Enables search by company name and budget year
    list_filter = ('budget_year', 'status')  # Filters by budget year and status
    ordering = ('-budget_year',)  # Orders by the most recent budget year
