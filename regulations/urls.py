from rest_framework.routers import DefaultRouter
from .views import RegulationViewSet, AuditLogViewSet, StockSuspensionViewSet

router = DefaultRouter()
router.register(r'regulations', RegulationViewSet, basename='regulation')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'suspensions', StockSuspensionViewSet, basename='suspension')

urlpatterns = router.urls
