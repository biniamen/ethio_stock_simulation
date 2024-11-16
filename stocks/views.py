from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import UsersPortfolio, ListedCompany, Stocks, Orders, Trade, TransactionLog, Dividend
from .serializers import (
    UsersPortfolioSerializer,
    ListedCompanySerializer,
    StocksSerializer,
    OrdersSerializer,
    TradeSerializer,
    TransactionLogSerializer,
    DividendSerializer,
)


class UsersPortfolioViewSet(viewsets.ModelViewSet):
    queryset = UsersPortfolio.objects.all()
    serializer_class = UsersPortfolioSerializer


class ListedCompanyViewSet(viewsets.ModelViewSet):
    queryset = ListedCompany.objects.all()
    serializer_class = ListedCompanySerializer


class StocksViewSet(viewsets.ModelViewSet):
    queryset = Stocks.objects.all()
    serializer_class = StocksSerializer


class OrdersViewSet(viewsets.ModelViewSet):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new order and automatically execute matching orders.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()  # This will also trigger match_and_execute_orders
        return Response(
            {"message": "Order created and matching executed successfully.", "order": serializer.data},
            status=status.HTTP_201_CREATED
        )


class TradeViewSet(viewsets.ModelViewSet):
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer


class TransactionLogViewSet(viewsets.ModelViewSet):
    queryset = TransactionLog.objects.all()
    serializer_class = TransactionLogSerializer


class DividendViewSet(viewsets.ModelViewSet):
    queryset = Dividend.objects.all()
    serializer_class = DividendSerializer
