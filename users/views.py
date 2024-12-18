from django.utils import timezone
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.mail import send_mail
from django.conf import settings

from ethio_stock_simulation.utils import generate_otp, send_verification_email
from users.models import CustomUser
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from django.core.mail import EmailMessage
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

class RegisterUser(generics.CreateAPIView):
    """
    API endpoint to register a new user.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        # Check for uniqueness of username and email
        if User.objects.filter(username=request.data.get('username')).exists():
            return Response(
                {"detail": "Username already exists. Please choose a different username."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=request.data.get('email')).exists():
            return Response(
                {"detail": "Email already exists. Please use a different email."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate and send OTP
        otp = generate_otp()
        user.otp_code = otp
        user.otp_sent_at = timezone.now()
        user.save()

        email_sent = send_verification_email(user.email, user.username, otp)

        if email_sent:
            return Response(
                {
                    "detail": "Registration successful. OTP sent to your email.",
                    "redirect_url": f"/verify-otp/?email={user.email}"
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"detail": "Failed to send OTP. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login endpoint using SimpleJWT.
    Blocks login if the user's KYC is not verified.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            # Check if KYC is verified
            if not serializer.user.kyc_verified:
                return Response(
                    {"detail": "KYC not verified. Please wait for approval."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    """
    API endpoint to list all users (accessible by regulators only).
    """
    if request.user.role != 'regulator':
        return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

    users = User.objects.all().values(
        'id',
        'username',
        'email',
        'role',
        'kyc_verified',
        'kyc_document',
        'account_balance',
        'profit_balance',
        'company_id',
    )
    return Response(users, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_kyc_status(request, user_id):
    """
    Public API endpoint to approve or reject user KYC.
    Logs email content using the console or file-based backend.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    action = request.data.get('action')
    if action == 'approve':
        user.approve_kyc()
        
        # Simulated email for KYC approval
        email_subject = "KYC Approved"
        email_message = f"""
        Dear {user.username},

        Your KYC has been approved. You can now log in to the system.

        Thank you!
        """
        email = EmailMessage(
            subject=email_subject,
            body=email_message,
            from_email='noreply@yourapp.com',  # Placeholder email address
            to=[user.email],
        )
        email.send()  # Logs email content to the console or file
    elif action == 'reject':
        user.reject_kyc()
    else:
        return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {"message": f"KYC status updated to {user.kyc_verified} for user {user.username}."},
        status=status.HTTP_200_OK,
    )
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not user.check_password(old_password):
            return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
    
class ListUsersView(APIView):
    permission_classes = [IsAuthenticated]  # Optional: Ensure only authenticated users can access this

    def get(self, request):
        users = CustomUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class VerifyOTPView(APIView):
    """
    Verify OTP for user registration.
    """
    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp_code')

        if not email or not otp_code:
            return Response({"detail": "Email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            if user.otp_verified:
                return Response({"detail": "OTP already verified."}, status=status.HTTP_200_OK)

            # Check if maximum attempts have been reached
            if user.otp_attempts >= 5:
                return Response({"detail": "Maximum OTP attempts exceeded. Request a new OTP.",
                                 "resend_required": True}, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # Verify OTP
            if user.otp_code == otp_code and user.otp_sent_at + timezone.timedelta(minutes=10) > timezone.now():
                user.otp_verified = True
                user.otp_code = None
                user.otp_attempts = 0  # Reset attempts
                user.save()
                return Response({"detail": "OTP verified successfully.", "verified": True}, status=status.HTTP_200_OK)
            else:
                user.otp_attempts += 1
                user.save()
                return Response({"detail": "Invalid or expired OTP.", "resend_required": False},
                                status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
class ResendOTPView(APIView):
    """
    Resend OTP to the user's email.
    """
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            # Add a cooldown period
            if user.otp_sent_at and timezone.now() - user.otp_sent_at < timezone.timedelta(minutes=2):
                return Response({"detail": "Please wait before requesting a new OTP."},
                                status=status.HTTP_429_TOO_MANY_REQUESTS)

            # Generate and send a new OTP
            otp = generate_otp()
            user.otp_code = otp
            user.otp_sent_at = timezone.now()
            user.otp_attempts = 0  # Reset OTP attempts
            user.save()
            send_verification_email(user.email, user.username, otp)
            return Response({"detail": "A new OTP has been sent to your email."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)