from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

# Existing UserSerializer for registration
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role', 'kyc_document', 'kyc_verified')
        extra_kwargs = {'password': {'write_only': True}, 'kyc_verified': {'read_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            role=validated_data['role'],
            kyc_document=validated_data.get('kyc_document', None),
        )
        return user

# CustomTokenObtainPairSerializer for login to include additional fields
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims to the JWT token
        token['username'] = user.username
        token['role'] = user.role
        token['kyc_verified'] = user.kyc_verified
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Include additional user-specific data in the response
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['role'] = self.user.role
        data['kyc_verified'] = self.user.kyc_verified
        
        return data
