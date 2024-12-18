import sendgrid
from sendgrid.helpers.mail import Mail
import random
from decouple import config

from ethio_stock_simulation.settings import SENDGRID_API_KEY, SENDGRID_FROM_EMAIL  # Import the config function to load environment variables

# Load environment variables
SENDGRID_API_KEY = config('SENDGRID_API_KEY')
SENDGRID_FROM_EMAIL = config('SENDGRID_FROM_EMAIL')

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