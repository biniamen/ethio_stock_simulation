from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    # User roles in the simulation
    ROLE_CHOICES = [
        ('trader', 'Trader'),
        ('regulator', 'Regulator'),
        ('company_admin', 'Company Admin'),
    ]
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='trader')

    # KYC verification status for compliance
    kyc_document = models.FileField(upload_to='kyc_documents/', blank=True, null=True)
    kyc_verified = models.BooleanField(default=False)

    # Linked Company ID for company_admin role
    company_id = models.IntegerField(null=True, blank=True)

    # Financial Information for Trader role only
    account_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, null=True, blank=True)
    profit_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, null=True, blank=True)

    # Timestamps
    date_registered = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # Override the save method to handle different roles
    def save(self, *args, **kwargs):
        # If the role is regulator or company admin, remove financial fields
        if self.role in ['regulator', 'company_admin']:
            self.account_balance = None
            self.profit_balance = None
        super(CustomUser, self).save(*args, **kwargs)

    # Methods for Trader financial updates
    def update_account_balance(self, amount):
        if self.role == 'trader' and self.account_balance is not None:
            self.account_balance += amount
            self.save()

    def update_profit_balance(self, amount):
        if self.role == 'trader' and self.profit_balance is not None:
            self.profit_balance += amount
            self.save()

    # KYC Approval and Rejection for Regulator role
    def approve_kyc(self):
        if self.kyc_document:
            self.kyc_verified = True
            self.save()

    def reject_kyc(self):
        self.kyc_verified = False
        self.save()

    # Company Admin-specific methods
    def link_company(self, company_id):
        if self.role == 'company_admin':
            self.company_id = company_id
            self.save()

    def unlink_company(self):
        if self.role == 'company_admin':
            self.company_id = None
            self.save()
