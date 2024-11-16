from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'kyc_verified', 'account_balance', 'profit_balance', 'company_id')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('role', 'kyc_document', 'kyc_verified', 'account_balance', 'profit_balance', 'company_id')
        }),
    )
