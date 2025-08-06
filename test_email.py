#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Add the project directory to the Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Email Configuration Test ===")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'None'}")
print(f"ADMIN_EMAIL: {settings.ADMIN_EMAIL}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")

print("\n=== Sending Test Email ===")

try:
    result = send_mail(
        subject='Test Email from Amity Portal',
        message='This is a test email to verify email configuration is working.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=False,
    )
    print(f"✅ Email sent successfully! Return value: {result}")
    print(f"Check your inbox at: {settings.ADMIN_EMAIL}")
    
except Exception as e:
    print(f"❌ Email sending failed!")
    print(f"Error: {e}")
    print(f"Error type: {type(e).__name__}")
