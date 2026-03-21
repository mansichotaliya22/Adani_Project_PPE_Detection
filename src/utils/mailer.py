# src/utils/mailer.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
import threading
from datetime import datetime

class SafetyMailer:
    def __init__(self, sender=None, receiver=None, password=None):
        self.sender = sender
        self.receiver = receiver
        self.password = password
        
    def send_email_background(self, v_type, image_path):
        """
        Send email alert in a background thread.
        """
        if not (self.sender and self.receiver and self.password):
            return
            
        thread = threading.Thread(target=self._send_email, args=(v_type, image_path))
        thread.start()
        
    def _send_email(self, v_type, image_path):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = self.receiver
            msg['Subject'] = f"SafeSight AI Alert: {v_type}"
            
            body = f"A safety violation ({v_type}) was detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
            msg.attach(MIMEText(body, 'plain'))
            
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    img_data = f.read()
                    image = MIMEImage(img_data, name=os.path.basename(image_path))
                    msg.attach(image)
            
            # Note: Hardcoded to Gmail for MVP as per design.md
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.sender, self.password)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Email sending failed: {e}")
