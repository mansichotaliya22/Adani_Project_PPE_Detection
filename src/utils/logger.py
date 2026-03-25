# src/utils/logger.py
import sqlite3
import os
from datetime import datetime

class SafetyLogger:
    def __init__(self, db_path="data/logs/safesight.db"):
        self.db_path = db_path
        self.init_db()
        
    def init_db(self):
        # Ensure the directory for the database exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS violations
                     (timestamp TEXT, type TEXT, image_path TEXT, x INTEGER, y INTEGER)''')
        conn.commit()
        conn.close()
        
    def log_violation(self, v_type, image_path, x=None, y=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO violations VALUES (?, ?, ?, ?, ?)", (timestamp, v_type, image_path, x, y))
        conn.commit()
        conn.close()
