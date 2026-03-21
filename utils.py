import sqlite3
import datetime
import os
import cv2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

DB_PATH = "safesight.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            violation_type TEXT,
            work_area TEXT,
            image_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_violation(v_type, work_area, frame):
    timestamp = datetime.datetime.now().strftime("%Y-%m-d_%H-%M-%S")
    date_folder = datetime.datetime.now().strftime("%Y-%m-%d")
    save_dir = os.path.join("data", "violations", date_folder)
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    image_path = os.path.join(save_dir, f"{v_type}_{timestamp}.jpg")
    cv2.imwrite(image_path, frame)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO violations (timestamp, violation_type, work_area, image_path)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, v_type, work_area, image_path))
    conn.commit()
    conn.close()
    
    return image_path

def send_email_alert(sender, receiver, password, v_type, image_path):
    # Throttling should be handled in app.py
    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = f"SafeSight AI Alert: {v_type}"
        
        body = f"A safety violation ({v_type}) was detected at {datetime.datetime.now()}."
        msg.attach(MIMEText(body, 'plain'))
        
        with open(image_path, 'rb') as f:
            img_data = f.read()
            image = MIMEImage(img_data, name=os.path.basename(image_path))
            msg.attach(image)
            
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False
