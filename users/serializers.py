from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'role',
            'kyc_document',
            'kyc_verified',
            'account_balance',
            'profit_balance',
            'company_id',
            'date_registered',
            'last_login',
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'kyc_verified': {'read_only': True},
            'account_balance': {'read_only': True},
            'profit_balance': {'read_only': True},
            'company_id': {'read_only': True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            role=validated_data['role'],
            kyc_document=validated_data.get('kyc_document', None),
        )
        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.role != 'trader':
            representation.pop('account_balance', None)
            representation.pop('profit_balance', None)
        if instance.role != 'company_admin':
            representation.pop('company_id', None)
        return representation


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['username'] = user.username
        token['role'] = user.role
        token['kyc_verified'] = user.kyc_verified

        if user.role == 'trader':
            token['account_balance'] = str(user.account_balance)
            token['profit_balance'] = str(user.profit_balance)
        if user.role == 'company_admin':
            token['company_id'] = user.company_id

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['role'] = self.user.role
        data['kyc_verified'] = self.user.kyc_verified

        if self.user.role == 'trader':
            data['account_balance'] = str(self.user.account_balance)
            data['profit_balance'] = str(self.user.profit_balance)
        if self.user.role == 'company_admin':
            data['company_id'] = self.user.company_id

        return data
