from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

# UserSerializer for registration and data representation
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 
            'email', 
            'password', 
            'role', 
            'kyc_document', 
            'kyc_verified', 
            'balance', 
            'portfolio_value', 
            'initial_balance', 
            'date_registered'
        )
        extra_kwargs = {
            'password': {'write_only': True}, 
            'kyc_verified': {'read_only': True},
            'balance': {'read_only': True},  # Balance is read-only unless updated internally for traders
            'portfolio_value': {'read_only': True},  # Portfolio value read-only
            'initial_balance': {'read_only': True},  # Initial balance read-only
        }

    def create(self, validated_data):
        # Handle user creation based on validated data
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            role=validated_data['role'],
            kyc_document=validated_data.get('kyc_document', None),  # Optional field
        )
        return user

    def to_representation(self, instance):
        # Customize the returned representation based on the role
        representation = super().to_representation(instance)
        if instance.role != 'trader':
            # Remove financial fields for non-trader roles (regulator and company admin)
            representation.pop('balance', None)
            representation.pop('portfolio_value', None)
            representation.pop('initial_balance', None)
        return representation


# CustomTokenObtainPairSerializer for login and JWT token generation
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims to the JWT token
        token['username'] = user.username
        token['role'] = user.role
        token['kyc_verified'] = user.kyc_verified

        # Add financial fields only for traders
        if user.role == 'trader':
            token['balance'] = str(user.balance)
            token['portfolio_value'] = str(user.portfolio_value)
            token['initial_balance'] = str(user.initial_balance)

        return token

    def validate(self, attrs):
        # Perform the base validation and obtain the token
        data = super().validate(attrs)

        # Include additional user-specific data in the response
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['role'] = self.user.role
        data['kyc_verified'] = self.user.kyc_verified

        # Include financial data only for traders
        if self.user.role == 'trader':
            data['balance'] = str(self.user.balance)
            data['portfolio_value'] = str(self.user.portfolio_value)
            data['initial_balance'] = str(self.user.initial_balance)

        return data
