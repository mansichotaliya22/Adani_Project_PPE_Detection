import sqlite3
import asyncio
import datetime
import os
import cv2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

DB_PATH = "safesight.db"
# Global queue for violation processing
violation_queue = asyncio.Queue()

async def init_db():
    def _sync_init():
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
    await asyncio.to_thread(_sync_init)

async def log_violation_async(v_type, work_area, frame):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # ✅ fixed typo
    date_folder = datetime.datetime.now().strftime("%Y-%m-%d")
    save_dir = os.path.join("data", "violations", date_folder)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Clean violation type for filename (remove special chars)
    safe_vtype = v_type.replace(" ", "_").replace(",", "").replace("/", "_")
    filename = f"{safe_vtype}_{timestamp}.jpg"

    local_path = os.path.join(save_dir, filename)          # For cv2.imwrite
    web_url = f"/data/violations/{date_folder}/{filename}"  # For DB + React

    def _sync_save():
        cv2.imwrite(local_path, frame)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO violations (timestamp, violation_type, work_area, image_path)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, v_type, work_area, web_url))  # ✅ save web_url not local_path
        conn.commit()
        conn.close()

    await asyncio.to_thread(_sync_save)
    return web_url  # ✅ return web_url not local_path

def send_email_sync(sender, receiver, password, v_type, frame):
    """Blocking SMTP logic."""
    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = f"SafeSight AI Alert: {v_type}"
        
        body = f"A safety violation ({v_type}) was detected at {datetime.datetime.now()}."
        msg.attach(MIMEText(body, 'plain'))
        
        _, buffer = cv2.imencode('.jpg', frame)
        image = MIMEImage(buffer.tobytes(), name=f"violation.jpg")
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

async def violation_worker_task():
    """
    The background worker that drains the queue and handles all I/O.
    """
    print("Violation Worker Started.")
    while True:
        event = await violation_queue.get()
        try:
            v_type = event['type']
            work_area = event['area']
            frame = event['frame']
            email_alerts = event.get('email_alerts', False)

            # 1. Log to DB and Disk (Async thread)
            await log_violation_async(v_type, work_area, frame)
            
            # 2. Email Alert (Run in thread pool)
            if email_alerts:
                sender = os.getenv("EMAIL_SENDER")
                receiver = os.getenv("EMAIL_RECEIVER")
                pwd = os.getenv("EMAIL_PASSWORD")
                if sender and receiver and pwd:
                    await asyncio.to_thread(send_email_sync, sender, receiver, pwd, v_type, frame)

        except Exception as e:
            print(f"Worker Error: {e}")
        finally:
            violation_queue.task_done()
