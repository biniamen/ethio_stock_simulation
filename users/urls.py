from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterUser, CustomTokenObtainPairView, list_users, update_kyc_status

urlpatterns = [
    path('register/', RegisterUser.as_view(), name='register'),  # Registration endpoint
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # Custom login endpoint
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh JWT tokens
    
    # New endpoints for Regulators:
    path('users/', list_users, name='list_users'),  # Endpoint to list all registered users (Regulators only)
    path('users/<int:user_id>/kyc/', update_kyc_status, name='update_kyc_status'),  # Endpoint to approve/reject KYC
]
