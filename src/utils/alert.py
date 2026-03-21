# src/utils/alert.py
import cv2
import os
from datetime import datetime
import pygame
import time

class Alerter:
    def __init__(self, sound_file=None):
        self.last_alert_time = 0
        try:
            pygame.mixer.init()
            if sound_file and os.path.exists(sound_file):
                self.sound = pygame.mixer.Sound(sound_file)
            else:
                self.sound = None
        except Exception as e:
            print(f"Pygame mixer init error: {e}")
            self.sound = None
            
    def trigger(self, frame, violations):
        """
        Save snapshot and play alert sound.
        """
        # 1. Save Snapshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_folder = datetime.now().strftime("%Y-%m-%d")
        save_dir = os.path.join("data", "violations", date_folder)
        os.makedirs(save_dir, exist_ok=True)
        
        v_type_slug = "_".join(violations).replace(" ", "_").replace(":", "")
        filename = os.path.join(save_dir, f"{v_type_slug}_{timestamp}.jpg")
        cv2.imwrite(filename, frame)
        
        # 2. Play Sound (Throttled to 3 seconds)
        if self.sound and (time.time() - self.last_alert_time > 3):
            try:
                self.sound.play()
                self.last_alert_time = time.time()
            except Exception as e:
                print(f"Sound play error: {e}")
            
        return filename
