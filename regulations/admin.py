from django.contrib import admin
from .models import Regulation, AuditLog, StockSuspension

@admin.register(Regulation)
class RegulationAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'description', 'created_by', 'created_at', 'last_updated')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'performed_by', 'timestamp', 'details')


@admin.register(StockSuspension)
class StockSuspensionAdmin(admin.ModelAdmin):
    list_display = (
        'trader', 'stock', 'suspension_type', 'initiator', 'reason', 
        'is_active', 'created_at', 'released_at'
    )
    list_filter = ('suspension_type', 'initiator', 'is_active')