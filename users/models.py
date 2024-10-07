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

    # Financial Information for Trader role only
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=100000.00, null=True, blank=True)
    portfolio_value = models.DecimalField(max_digits=15, decimal_places=2, default=100000.00, null=True, blank=True)
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=100000.00, null=True, blank=True)

    # Timestamps
    date_registered = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # Override the save method to handle different roles
    def save(self, *args, **kwargs):
        # Remove financial information for regulators and company admins
        if self.role == 'regulator' or self.role == 'company_admin':
            self.balance = None
            self.portfolio_value = None
            self.initial_balance = None
        super(CustomUser, self).save(*args, **kwargs)

    # Methods for Trader financial updates
    def update_balance(self, amount):
        if self.role == 'trader':
            self.balance += amount
            self.save()

    def update_portfolio_value(self, new_value):
        if self.role == 'trader':
            self.portfolio_value = new_value
            self.save()

    def calculate_total_value(self):
        if self.role == 'trader':
            return self.balance + self.portfolio_value
        return None

    # KYC Approval and Rejection for Regulator role
    def approve_kyc(self):
        if self.kyc_document:
            self.kyc_verified = True
            self.save()

    def reject_kyc(self):
        self.kyc_verified = False
        self.save()

    # Company Admin-specific methods (example: disburse profit)
    def set_profit_disbursement(self, company, profit_amount):
        if self.role == 'company_admin':
            # Logic for disbursing profit to shareholders
            pass
