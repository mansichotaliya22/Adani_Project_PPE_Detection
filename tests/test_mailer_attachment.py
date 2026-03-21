# tests/test_mailer_attachment.py
import os
import time
from dotenv import load_dotenv
from src.utils.mailer import SafetyMailer

def test_send_email_attachment():
    load_dotenv(override=True)
    
    sender = os.getenv("EMAIL_SENDER")
    receiver = os.getenv("EMAIL_RECEIVER")
    password = os.getenv("EMAIL_PASSWORD")
    
    image_path = r"C:\Users\Tanmay\ai smart video project\data\violations\2026-03-20\Missing_PPE_NO-Hardhat_20260320_225046.jpg"
    
    mailer = SafetyMailer(sender=sender, receiver=receiver, password=password)
    
    print(f"Testing email with attachment from {sender} to {receiver}...")
    mailer.send_email_background("PPE_VIOLATION_TEST_WITH_IMAGE", image_path)
    
    print("Email sent in background. Waiting 10 seconds...")
    time.sleep(10)
    print("Test finished.")

if __name__ == "__main__":
    test_send_email_attachment()
