# src/detection/detector.py
from ultralytics import YOLO
import cv2
import numpy as np

class SafetyDetector:
    def __init__(self, model_path="yolov8n.pt", conf_threshold=0.5):
        self.model = YOLO(model_path)
        self.conf = conf_threshold
        self.track_history = {} # ID -> [last_centroid]
        
    def detect(self, frame):
        # Run inference with tracking
        results = self.model.track(frame, conf=self.conf, persist=True, verbose=False)
        return results[0] # Return first result
    
    def plot_results(self, result, frame):
        # Use built-in plotter for MVP
        return result.plot()
        
    def check_violations(self, result, frame, roi=None, speed_threshold=50):
        """
        Identify violations from detection results.
        roi: tuple (x1, y1, x2, y2) in absolute pixels
        speed_threshold: pixel displacement threshold
        """
        violations = []
        boxes = result.boxes
        
        # Current IDs in this frame
        current_ids = []
        h, w = frame.shape[:2]
        # Normalize threshold (input is 10-200, we treat it as relative to 1000px width)
        normalized_threshold = (speed_threshold / 1000.0) * w
        
        if boxes is not None:
            for box in boxes:
                cls = int(box.cls[0])
                label = result.names[cls]
                
                # Get tracking ID if available
                track_id = int(box.id[0]) if box.id is not None else None
                
                # Bbox coordinates
                x1, y1, x2, y2 = box.xyxy[0]
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                
                # PPE Logic 
                if label in ["NO-Hardhat", "NO-Safety Vest", "NO-Vest"]:
                    violations.append(f"Missing PPE: {label}")
                
                # ROI Logic
                if roi:
                    rx1, ry1, rx2, ry2 = roi
                    if rx1 < cx < rx2 and ry1 < cy < ry2:
                        if label == "person":
                            violations.append("Danger Zone Intrusion")
                
                # Speed / Movement Logic
                if track_id is not None and label == "person":
                    current_ids.append(track_id)
                    if track_id in self.track_history:
                        prev_cx, prev_cy = self.track_history[track_id]
                        # Calculate Euclidean distance
                        dist = np.sqrt((cx - prev_cx)**2 + (cy - prev_cy)**2)
                        if dist > normalized_threshold:
                            violations.append("Running Detected")
                    
                    # Update history
                    self.track_history[track_id] = (cx, cy)
        
        # Cleanup track history for IDs no longer in frame
        # (Simplified: could use a max_age but for MVP this works)
        # self.track_history = {k: v for k, v in self.track_history.items() if k in current_ids}
        
        return list(set(violations))
