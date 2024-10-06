from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterUser, CustomTokenObtainPairView

urlpatterns = [
    path('register/', RegisterUser.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # Use custom login view
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
