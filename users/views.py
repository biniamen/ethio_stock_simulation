from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterUser(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'kyc_verified': user.kyc_verified,
            },
            status=status.HTTP_201_CREATED
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
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
@permission_classes([IsAuthenticated])
def update_kyc_status(request, user_id):
    if request.user.role != 'regulator':
        return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    action = request.data.get('action')
    if action == 'approve':
        user.approve_kyc()
    elif action == 'reject':
        user.reject_kyc()
    else:
        return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": f"KYC status updated to {user.kyc_verified} for user {user.username}."}, status=status.HTTP_200_OK)
