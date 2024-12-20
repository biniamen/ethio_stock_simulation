from django.forms import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import UsersPortfolio, ListedCompany, Stocks, Orders, Trade, Dividend
from .serializers import (
    DirectStockPurchaseSerializer,
    UsersPortfolioSerializer,
    ListedCompanySerializer,
    StocksSerializer,
    OrdersSerializer,
    TradeSerializer,
    DividendSerializer,
)


class UsersPortfolioViewSet(viewsets.ModelViewSet):
    queryset = UsersPortfolio.objects.all()
    serializer_class = UsersPortfolioSerializer


class ListedCompanyViewSet(viewsets.ModelViewSet):
    queryset = ListedCompany.objects.all()
    serializer_class = ListedCompanySerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new listed company and return the serialized data.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
        order = serializer.save()  # Automatically triggers matching logic
        return Response(
            {
                "message": "Order created and matching executed successfully.",
                "order": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

class TraderOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Ensure the user is a trader
        if request.user.role != 'trader':
            return Response({"detail": "Only traders can view this resource."}, status=403)
        
        # Fetch orders belonging to the logged-in trader
        orders = Orders.objects.filter(trader=request.user)
        serializer = OrdersSerializer(orders, many=True)
        return Response(serializer.data)

class TradeViewSet(viewsets.ModelViewSet):
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer


class UserOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch orders belonging to the logged-in user
        orders = Orders.objects.filter(user=request.user)
        serializer = OrdersSerializer(orders, many=True)
        return Response(serializer.data)

class UserTradesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch trades belonging to the logged-in user
        trades = Trade.objects.filter(user=request.user)
        serializer = TradeSerializer(trades, many=True)
        return Response(serializer.data)

class DividendViewSet(viewsets.ModelViewSet):
    queryset = Dividend.objects.all()
    serializer_class = DividendSerializer


class DirectStockPurchaseView(APIView):
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        stock_id = request.data.get("stock_id")
        quantity = request.data.get("quantity")

        if user_id is None or stock_id is None or quantity is None:
            return Response({"detail": "user_id, stock_id, and quantity are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid quantity value."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order, trade = Stocks.execute_direct_purchase(user_id, stock_id, quantity)
            return Response({
                "message": "Direct purchase completed successfully.",
                "order_id": order.id,
                "trade_id": trade.id,
                "stock_symbol": order.stock_symbol,
                "quantity": order.quantity,
                "price": str(order.price),
                "total_cost": str(order.price * order.quantity),
                "status": order.status
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class UserSpecificTradesView(APIView):
    """
    GET /api/stocks/user/<user_id>/trades/
    Returns all trades for the specified user.
    """
    def get(self, request, user_id, *args, **kwargs):
        # Fetch all trades for the given user_id
        trades = Trade.objects.filter(user_id=user_id)
        serializer = TradeSerializer(trades, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)