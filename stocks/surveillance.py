# stocks/surveillance.py

from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Sum

def detect_suspicious_trade(trade):
    """
    Detects suspicious trades based on predefined criteria.
    1) Unusual Trade Volume
    2) Price Manipulation
    3) Frequent Trader Activity
    If suspicious, a SuspiciousActivity record is created.
    """
    from .models import Trade  # Function-level import to avoid circular dependency
    from .models_suspicious import SuspiciousActivity  # Function-level import

    reasons = []

    # 1) Unusual Trade Volume (Example: over 10% of the stock's total + available shares)
    stock = trade.stock
    total_traded = Trade.objects.filter(stock=stock).aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_available = stock.available_shares + total_traded

    if total_available > 0:
        threshold = 0.1 * total_available  # 10% threshold
        if trade.quantity > threshold:
            reasons.append(f"Unusually high trade volume: {trade.quantity} > 10% of market float.")

    # 2) Price Manipulation (Example: ±20% of average price)
    avg_price = Trade.objects.filter(stock=stock).aggregate(Avg('price'))['price__avg']
    if avg_price:
        if trade.price > 1.2 * avg_price or trade.price < 0.8 * avg_price:
            reasons.append(f"Trade price deviates from average (${avg_price:.2f}).")

    # 3) Frequent Trader Activity (Example: >5 trades in last 10 min by same user)
    ten_minutes_ago = timezone.now() - timedelta(minutes=10)
    recent_trades = Trade.objects.filter(user=trade.user, trade_time__gte=ten_minutes_ago).count()
    if recent_trades > 1:
        reasons.append(f"High trading frequency: {recent_trades} trades in 10 minutes.")

    # Flag trade if any reasons are triggered
    if reasons:
        SuspiciousActivity.objects.create(
            trade=trade,
            reason="; ".join(reasons),
        )
