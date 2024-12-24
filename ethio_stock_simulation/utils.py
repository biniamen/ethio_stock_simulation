import sendgrid
from sendgrid.helpers.mail import Mail
import random
from decouple import config

from ethio_stock_simulation.settings import SENDGRID_API_KEY, SENDGRID_FROM_EMAIL

# Load environment variables (if needed; you already do this in your code)
SENDGRID_API_KEY = config('SENDGRID_API_KEY', default=SENDGRID_API_KEY)
SENDGRID_FROM_EMAIL = config('SENDGRID_FROM_EMAIL', default=SENDGRID_FROM_EMAIL)

def generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))

def send_verification_email(to_email, username, otp):
    """
    Send OTP to user's email via SendGrid.
    """
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    subject = "Your Account Verification Code"
    content = f"""
    Dear {username},

    Your verification code is: {otp}

    This code will expire in 10 minutes.

    Regards,
    Your Company Name
    """
    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )
    try:
        response = sg.send(message)
        print(f"Email sent to {to_email}. Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_order_notification(to_email, username, action, stock_symbol, quantity, price):
    """
    Send an order execution notification via SendGrid.
    to_email: recipient's email address
    username: recipient's username
    action: 'Buy' or 'Sell'
    stock_symbol: e.g., 'AAPL'
    quantity: number of shares
    price: execution price
    """
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    subject = "Order Execution Notification"
    content = f"""
    Hello {username},

    Your order has been executed successfully:
    Action: {action}
    Stock: {stock_symbol}
    Quantity: {quantity}
    Execution Price: {price}

    Thank you for trading with us.

    Regards,
    Your Stock Simulation Platform
    """
    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )
    try:
        response = sg.send(message)
        print(f"Order execution email sent to {to_email}. Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
