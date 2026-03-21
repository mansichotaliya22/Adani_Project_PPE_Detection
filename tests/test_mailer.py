# tests/test_mailer.py
import os
import time
from dotenv import load_dotenv
from src.utils.mailer import SafetyMailer

def test_send_email():
    # Force override environment variables from .env
    load_dotenv(override=True)
    
    sender = os.getenv("EMAIL_SENDER")
    receiver = os.getenv("EMAIL_RECEIVER")
    password = os.getenv("EMAIL_PASSWORD")
    
    print(f"DEBUG: Loaded sender='{sender}', receiver='{receiver}', password='{password}'")
    
    # We use the provided app password
    mailer = SafetyMailer(sender=sender, receiver=receiver, password=password)
    
    print(f"Testing email from {sender} to {receiver}...")
    
    # We use a dummy violation and no image for initial test
    # Note: send_email_background is asynchronous
    mailer.send_email_background("TEST_VIOLATION", None)
    
    print("Email sent in background. Waiting 10 seconds for it to complete...")
    time.sleep(10)
    print("Test finished.")

if __name__ == "__main__":
    test_send_email()
