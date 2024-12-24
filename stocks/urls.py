from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    DirectStockPurchaseView,
    DisclosureViewSet,
    TraderOrdersView,
    UserOrdersView,
    UserSpecificTradesView,
    UserTradesView,
    UsersPortfolioViewSet,
    ListedCompanyViewSet,
    StocksViewSet,
    OrdersViewSet,
    TradeViewSet,
    DividendViewSet,
    suspicious_activities,
)

router = DefaultRouter()
router.register(r'portfolios', UsersPortfolioViewSet, basename='portfolio')
router.register(r'companies', ListedCompanyViewSet, basename='company')
router.register(r'stocks', StocksViewSet, basename='stock')
router.register(r'orders', OrdersViewSet, basename='order')
router.register(r'trades', TradeViewSet, basename='trade')
router.register(r'dividends', DividendViewSet, basename='dividend')
router.register(r'disclosures', DisclosureViewSet, basename='disclosure')

# Add the custom endpoint for fetching trader orders
urlpatterns = [
    path('trader/orders/', TraderOrdersView.as_view(), name='trader-orders'),
    path('user/orders/', UserOrdersView.as_view(), name='user-orders'),
    path('user/trades/', UserTradesView.as_view(), name='user-trades'),
    path('direct_buy/', DirectStockPurchaseView.as_view(), name='direct-buy'),
    path('user/<int:user_id>/trades/', UserSpecificTradesView.as_view(), name='user-specific-trades'),
    path('surveillance/activities/', suspicious_activities, name='suspicious_activities'),


]

# Combine router URLs with the custom URLs
urlpatterns += router.urls
