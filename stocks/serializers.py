from rest_framework import serializers
from .models import UsersPortfolio, ListedCompany, Stocks, Orders, Trade, Dividend


class UsersPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersPortfolio
        fields = '__all__'


class ListedCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = ListedCompany
        fields = '__all__'


class StocksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stocks
        fields = '__all__'


class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = '__all__'


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = '__all__'


class DividendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dividend
        fields = '__all__'
