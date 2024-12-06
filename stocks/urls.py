from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    TraderOrdersView,
    UsersPortfolioViewSet,
    ListedCompanyViewSet,
    StocksViewSet,
    OrdersViewSet,
    TradeViewSet,
    DividendViewSet,
)

router = DefaultRouter()
router.register(r'portfolios', UsersPortfolioViewSet, basename='portfolio')
router.register(r'companies', ListedCompanyViewSet, basename='company')
router.register(r'stocks', StocksViewSet, basename='stock')
router.register(r'orders', OrdersViewSet, basename='order')
router.register(r'trades', TradeViewSet, basename='trade')
router.register(r'dividends', DividendViewSet, basename='dividend')

# Add the custom endpoint for fetching trader orders
urlpatterns = [
    path('trader/orders/', TraderOrdersView.as_view(), name='trader-orders'),
]

# Combine router URLs with the custom URLs
urlpatterns += router.urls
