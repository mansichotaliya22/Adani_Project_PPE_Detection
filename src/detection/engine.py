import cv2
import numpy as np
from ultralytics import YOLO
import time
import os
import multiprocessing as mp
import threading
import torch

def ai_worker(shared_raw, shared_annotated, shape, settings_dict, stats_dict):
    """
    Dedicated AI Process. 
    Reads from raw shared memory, writes to annotated shared memory.
    """
    try:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"[AI Worker] Using device: {device}")

        model_path = "models/ppe_yolov8s.pt"
        if not os.path.exists(model_path):
            print(f"[AI Worker] FATAL: Model not found at '{model_path}'")
            return
            
        model = YOLO(model_path)
        model.to(device)
        
        raw_np = np.frombuffer(shared_raw.get_obj(), dtype=np.uint8).reshape(shape)
        annotated_np = np.frombuffer(shared_annotated.get_obj(), dtype=np.uint8).reshape(shape)

        # Cumulative counters
        total_ppe_violations = 0
        total_roi_violations = 0

        frame_count = 0
        while True:
            try:
                frame_count += 1
                frame = raw_np.copy()

                if frame_count % 2 == 0:
                    use_half = device == 'cuda'
                    results = model.predict(
                        frame,
                        conf=settings_dict['conf'],
                        verbose=False,
                        imgsz=640,
                        half=use_half,
                        device=device
                    )
                    res_frame = results[0].plot()

                    people, ppe, violations = 0, 0, []
                    for box in results[0].boxes:
                        cls_id = int(box.cls[0])
                        label = model.names[cls_id]
                        if label == "Person": people += 1
                        if label in ["NO-Hardhat", "NO-Safety Vest"]:
                            ppe += 1
                            violations.append(label)

                    # Update live stats
                    stats_dict['people_count'] = people
                    stats_dict['ppe_current'] = ppe

                    # Update cumulative stats with throttle
                    current_time = time.time()
                    if violations and (current_time - settings_dict.get('last_v_time', 0) > 5):
                        settings_dict['last_v_time'] = current_time
                        
                        # Increment cumulative totals
                        total_ppe_violations += len(set(violations))
                        stats_dict['ppe_violations'] = total_ppe_violations
                        
                        stats_dict['pending_violation'] = {
                            'type': ", ".join(set(violations)),
                            'frame': res_frame.copy()
                        }

                    np.copyto(annotated_np, res_frame)
                    stats_dict['first_frame_ready'] = True

                time.sleep(0.001)

            except Exception as e:
                time.sleep(0.1)
                
    except Exception as e:
        print(f"[AI Worker] FATAL CRASH: {e}")

class DetectionEngine:
    def __init__(self):
        self.width = 640
        self.height = 480
        self.shape = (self.height, self.width, 3)
        self.size = self.height * self.width * 3
        self.is_running = False
        
        self.shared_raw = mp.Array('B', self.size)
        self.shared_annotated = mp.Array('B', self.size)
        
        self.manager = mp.Manager()
        self.settings = self.manager.dict({'conf': 0.5})
        self.stats = self.manager.dict({
            'people_count': 0, 
            'ppe_violations': 0, 
            'ppe_current': 0,
            'roi_violations': 0, 
            'first_frame_ready': False
        })
        
        self.process = None
        
    def start(self, source=0):
        if self.is_running: return

        # Reset all counters on fresh start
        self.stats['ppe_violations'] = 0
        self.stats['ppe_current'] = 0
        self.stats['roi_violations'] = 0
        self.stats['people_count'] = 0
        self.stats['first_frame_ready'] = False

        self.cap = cv2.VideoCapture(source, cv2.CAP_MSMF)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(source)

        if not self.cap.isOpened():
            print(f"[Engine] ERROR: Could not open source {source}")
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        print("[Engine] Draining webcam buffer...")
        for _ in range(30):
            self.cap.grab()

        self.is_running = True
        
        self.process = mp.Process(target=ai_worker, args=(
            self.shared_raw, self.shared_annotated, self.shape, self.settings, self.stats
        ))
        self.process.daemon = True
        self.process.start()
        
        self.cap_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.cap_thread.start()

    def _capture_loop(self):
        raw_np = np.frombuffer(
            self.shared_raw.get_obj(), dtype=np.uint8
        ).reshape(self.shape)

        while self.is_running:
            for _ in range(3):
                self.cap.grab()

            ret, frame = self.cap.retrieve()
            if not ret:
                continue

            if frame.shape == self.shape:
                np.copyto(raw_np, frame)
            else:
                resized = cv2.resize(frame, (self.width, self.height))
                np.copyto(raw_np, resized)

    def stop(self):
        self.is_running = False
        if self.process: 
            self.process.terminate()
            self.process.join(timeout=1.0)
        if self.cap: 
            self.cap.release()

    def get_frame(self):
        try:
            if self.stats.get('first_frame_ready', False):
                annotated_np = np.frombuffer(self.shared_annotated.get_obj(), dtype=np.uint8).reshape(self.shape)
                return annotated_np.copy(), time.time()
            
            raw_np = np.frombuffer(self.shared_raw.get_obj(), dtype=np.uint8).reshape(self.shape)
            return raw_np.copy(), time.time()
        except Exception:
            return None, 0

    def get_stats(self):
        return {
            "people_count":    self.stats.get('people_count', 0),    # Live count
            "ppe_violations":  self.stats.get('ppe_violations', 0),  # Cumulative total
            "ppe_current":     self.stats.get('ppe_current', 0),     # This frame
            "roi_violations":  self.stats.get('roi_violations', 0),  # Cumulative total
            "running":         self.is_running
        }

