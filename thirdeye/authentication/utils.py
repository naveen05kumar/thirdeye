import random
import string
from datetime import datetime, timedelta
from django.core.mail import EmailMessage
from django.utils import timezone  # Import timezone for aware datetime handling

def generate_otp():
    """Generate a random 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=6))

def is_otp_valid(user):
    """
    Check if the OTP for the user is valid.
    OTP is valid if it exists, has been created within the last 5 minutes.
    """
    if user.otp and user.otp_created_at:
        expiry_time = user.otp_created_at + timedelta(minutes=5)
        return timezone.now() <= expiry_time  # Compare with timezone-aware current time
    return False

class Util:
    @staticmethod
    def send_email(data):
        """
        Send an email using Django's EmailMessage class.
        Requires 'email_subject', 'email_body', and 'to_email' keys in data dictionary.
        """
        email = EmailMessage(
            subject=data['email_subject'],
            body=data['email_body'],
            to=[data['to_email']]
        )
        email.send()
