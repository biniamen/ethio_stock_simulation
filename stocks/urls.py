from rest_framework.routers import DefaultRouter
from .views import (
    UsersPortfolioViewSet,
    ListedCompanyViewSet,
    StocksViewSet,
    OrdersViewSet,
    TradeViewSet,
    TransactionLogViewSet,
    DividendViewSet,
)

router = DefaultRouter()
router.register(r'portfolios', UsersPortfolioViewSet, basename='portfolio')
router.register(r'companies', ListedCompanyViewSet, basename='company')
router.register(r'stocks', StocksViewSet, basename='stock')
router.register(r'orders', OrdersViewSet, basename='order')
router.register(r'trades', TradeViewSet, basename='trade')
router.register(r'transactions', TransactionLogViewSet, basename='transaction')
router.register(r'dividends', DividendViewSet, basename='dividend')

urlpatterns = router.urls
