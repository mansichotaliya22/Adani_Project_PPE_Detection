# src/detection/detector.py
from ultralytics import YOLO
import cv2
import numpy as np

class SafetyDetector:
    def __init__(self, model_path="yolov8n.pt", conf_threshold=0.5):
        self.model = YOLO(model_path)
        self.conf = conf_threshold
        self.track_history = {} # ID -> [last_centroid]
        self.violation_counters = {} # ID -> {type: count}
        self.STABLE_FRAME_THRESHOLD = 15 # Bumped to ~1.5 seconds at 10fps
        
    def detect(self, frame):
        # Run inference with tracking
        results = self.model.track(frame, conf=self.conf, persist=True, verbose=False)
        return results[0] # Return first result
    
    def plot_results(self, result, frame):
        return result.plot()
        
    def check_violations(self, result, frame, roi=None, speed_threshold=50):
        """
        Detects safety violations by associating PPE detections with tracked persons spatially.
        """
        violations_data = []
        boxes = result.boxes
        h, w = frame.shape[:2]
        normalized_threshold = (speed_threshold / 1000.0) * w
        
        people_stats = {"total_people": 0, "safe_count": 0, "unsafe_count": 0}
        seen_this_frame = set()
        
        # Use constructor-defined confidence for PPE
        PPE_CONF_THRESHOLD = self.conf
        STABLE_FRAME_THRESHOLD = 5 # ~0.5 seconds at 10fps
        
        if boxes is not None:
            person_status = {} # track_id -> {"safe": bool, "ppe": {"Vest": T, "Mask": T, "Helmet": T}, "cx": int, "cy": int}
            person_boxes = {} # track_id -> [x1, y1, x2, y2]
            
            # 1. First pass: Identify all people
            for box in boxes:
                if box.id is None: continue
                cls = int(box.cls[0])
                label = result.names[cls].lower()
                
                if label == "person":
                    tid = int(box.id[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                    
                    people_stats["total_people"] += 1
                    person_boxes[tid] = [x1, y1, x2, y2]
                    person_status[tid] = {
                        "safe": True, 
                        "ppe": {"Vest": True, "Mask": True, "Helmet": True},
                        "cx": cx, "cy": cy
                    }

            # 2. Second pass: Associate PPE violations with people spatially
            for box in boxes:
                cls = int(box.cls[0])
                label = result.names[cls]
                conf = float(box.conf[0])
                
                # PPE Column Mapping (Case-insensitive check)
                ppe_col = None
                if "no-hardhat" in label.lower(): ppe_col = "Helmet"
                elif "no-safety vest" in label.lower(): ppe_col = "Vest"
                elif "no-mask" in label.lower(): ppe_col = "Mask"

                if ppe_col and conf > PPE_CONF_THRESHOLD:
                    vx1, vy1, vx2, vy2 = box.xyxy[0].tolist()
                    vcx, vcy = int((vx1 + vx2) / 2), int((vy1 + vy2) / 2)
                    
                    # Find the person this violation belongs to (Spatial Overlap)
                    for tid, pbox in person_boxes.items():
                        px1, py1, px2, py2 = pbox
                        
                        # If violation center is inside person box
                        if px1 <= vcx <= px2 and py1 <= vcy <= py2:
                            person_h = py2 - py1
                            
                            # Validation based on expected body location
                            is_valid_location = False
                            if ppe_col == "Helmet" and vcy < py1 + (person_h * 0.30):
                                is_valid_location = True
                            elif ppe_col == "Mask" and vcy < py1 + (person_h * 0.45):
                                is_valid_location = True
                            elif ppe_col == "Vest" and vcy < py1 + (person_h * 0.75):
                                is_valid_location = True

                            if is_valid_location:
                                v_key = f"{tid}_{ppe_col}"
                                seen_this_frame.add(v_key)
                                self.violation_counters[v_key] = self.violation_counters.get(v_key, 0) + 1
                                
                                if self.violation_counters[v_key] >= STABLE_FRAME_THRESHOLD:
                                    violations_data.append({
                                        "type": f"Missing {ppe_col}", "x": vcx, "y": vcy, "ppe_col": ppe_col
                                    })
                                    person_status[tid]["ppe"][ppe_col] = False
                                break # Found the person, move to next box

                # 3. Third pass: ROI & Speed (Only for tracked persons)
                cls = int(box.cls[0])
                label = result.names[cls].lower()
                if label == "person" and box.id is not None:
                    tid = int(box.id[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                    
                    if roi:
                        rx1, ry1, rx2, ry2 = roi
                        if rx1 < cx < rx2 and ry1 < cy < ry2:
                            v_key = f"{tid}_ROI"
                            seen_this_frame.add(v_key)
                            self.violation_counters[v_key] = self.violation_counters.get(v_key, 0) + 1
                            if self.violation_counters[v_key] >= 3: 
                                violations_data.append({"type": "Danger Zone Intrusion", "x": cx, "y": cy, "ppe_col": None})
                                person_status[tid]["safe"] = False

                    if tid in self.track_history:
                        prev_cx, prev_cy = self.track_history[tid]
                        dist = np.sqrt((cx - prev_cx)**2 + (cy - prev_cy)**2)
                        if dist > normalized_threshold:
                            violations_data.append({"type": "Running Detected", "x": cx, "y": cy, "ppe_col": None})
                            person_status[tid]["safe"] = False
                    self.track_history[tid] = (cx, cy)

            # Clean up stale counters
            for v_key in list(self.violation_counters.keys()):
                if v_key not in seen_this_frame:
                    self.violation_counters[v_key] = 0
            
            # Final Stats Calculation
            unsafe_ids = [tid for tid, data in person_status.items() if not data["safe"] or not all(data["ppe"].values())]
            people_stats["unsafe_count"] = len(unsafe_ids)
            people_stats["safe_count"] = max(0, people_stats["total_people"] - people_stats["unsafe_count"])

        return violations_data, people_stats

