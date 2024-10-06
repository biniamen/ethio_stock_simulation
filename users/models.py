from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('trader', 'Trader'),
        ('regulator', 'Regulator'),
        ('company_admin', 'Company Admin'),
    ]
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='trader')

    # New KYC fields
    kyc_document = models.FileField(upload_to='kyc_documents/', blank=True, null=True)
    kyc_verified = models.BooleanField(default=False)  # Admin can verify documents

    def __str__(self):
        return self.username
