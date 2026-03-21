# SafeSight AI - PPE & Safety Monitoring System (MVP) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real-time computer vision system to detect PPE violations and unsafe behaviors on a laptop.

**Architecture:** Python-based application using YOLOv8 for detection, Streamlit for the UI, and SQLite for logging.

**Tech Stack:** Python 3.9+, Ultralytics YOLOv8, Streamlit, OpenCV, SQLite, Pygame/Playsound.

---

## Phase 1: Environment & Core AI (Day 1)

### Task 1: Project Initialization & Environment Setup
**Goal:** Set up the Python environment, directory structure, and install dependencies.

**Files:**
- Create: `requirements.txt`
- Create: `main.py` (placeholder)
- Create: `README.md`
- Create: `.gitignore`


- [ ] **Step 1: Create directory structure**
  ```bash
  mkdir -p data/models data/logs data/violations
  mkdir -p src/detection src/ui src/utils
  mkdir tests
  ```

- [ ] **Step 2: Create `requirements.txt`**
  ```text
  ultralytics==8.0.196
  streamlit==1.27.0
  opencv-python-headless==4.8.0.76
  playsound==1.3.0
  pygame==2.5.2
  pandas==2.1.1
  Pillow==10.0.1
  watchdog==3.0.0
  pytest==7.4.2
  ```

- [ ] **Step 3: Create `.gitignore`**
  ```text
  __pycache__/
  *.pyc
  .env
  .venv
  data/logs/*.db
  data/violations/*
  !data/violations/.gitkeep
  data/models/*.pt
  !data/models/.gitkeep
  ```

- [ ] **Step 4: Install dependencies**
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **Step 5: Verify installation**
  ```bash
  python -c "import ultralytics; import streamlit; import cv2; print('Setup Complete')"
  ```

### Task 2: Model Acquisition & Verification
**Goal:** Download a pre-trained PPE model (or standard YOLOv8n for testing) and verify it works. *Note: Actual custom training happens in Colab, this task assumes the model file `best.pt` is obtained.*

**Files:**
- Create: `src/detection/model_loader.py`
- Create: `tests/test_model_loader.py`

- [ ] **Step 1: Write test for model loading**
  ```python
  # tests/test_model_loader.py
  import os
  from src.detection.model_loader import load_model
  
  def test_model_download_and_load():
      model = load_model("yolov8n.pt") # Use standard model for initial test
      assert model is not None
      assert model.names is not None
  ```

- [ ] **Step 2: Implement `load_model`**
  ```python
  # src/detection/model_loader.py
  from ultralytics import YOLO
  import os
  
  def load_model(model_path="yolov8n.pt"):
      if not os.path.exists(model_path) and not model_path.endswith('.pt'):
          raise FileNotFoundError(f"Model not found at {model_path}")
      
      model = YOLO(model_path)
      return model
  ```

- [ ] **Step 3: Run test**
  ```bash
  pytest tests/test_model_loader.py -v
  ```

### Task 3: Video Stream Processor (Core Logic)
**Goal:** Create a class that captures video frames from Webcam or File and yields them for processing.

**Files:**
- Create: `src/detection/video_source.py`
- Create: `tests/test_video_source.py`

- [ ] **Step 1: Write test for VideoSource**
  ```python
  # tests/test_video_source.py
  import cv2
  import pytest
  from src.detection.video_source import VideoSource

  def test_video_source_webcam_init():
      # We can't easily test actual webcam in CI/headless, so we mock or test file
      # For MVP, we'll test instantiation
      source = VideoSource(source_type="webcam", source_path=0)
      assert source.cap is None # Should be None until started

  def test_get_frame_invalid_file():
      with pytest.raises(ValueError):
           VideoSource(source_type="file", source_path="nonexistent.mp4")
  ```

- [ ] **Step 2: Implement `VideoSource`**
  ```python
  # src/detection/video_source.py
  import cv2
  import os
  
  class VideoSource:
      def __init__(self, source_type="webcam", source_path=0):
          self.source_type = source_type
          self.source_path = source_path
          self.cap = None

          if source_type == "file" and not os.path.exists(str(source_path)):
              raise ValueError(f"File not found: {source_path}")

      def start(self):
          if self.source_type == "webcam":
              self.cap = cv2.VideoCapture(int(self.source_path))
          else:
              self.cap = cv2.VideoCapture(self.source_path)
          
          if not self.cap.isOpened():
              raise RuntimeError("Could not open video source")

      def get_frame(self):
          if self.cap is None:
              self.start()
          ret, frame = self.cap.read()
          if not ret:
              return None
          return frame
      
      def stop(self):
          if self.cap:
              self.cap.release()
  ```

- [ ] **Step 3: Run tests**
  ```bash
  pytest tests/test_video_source.py -v
  ```

---

## Phase 2: Application Logic & UI (Day 2)

### Task 4: Basic Streamlit Dashboard
**Goal:** Create the Streamlit UI shell that can display the video feed (raw).

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Implement Basic UI**
  ```python
  # main.py
  import streamlit as st
  import cv2
  from src.detection.video_source import VideoSource
  
  st.set_page_config(page_title="SafeSight AI", layout="wide")
  
  st.title("🦺 SafeSight AI - Safety Monitoring")
  
  # Sidebar
  st.sidebar.header("Configuration")
  source_type = st.sidebar.radio("Input Source", ["Webcam", "Video File"])
  
  source_path = 0
  if source_type == "Video File":
      uploaded_file = st.sidebar.file_uploader("Upload Video", type=['mp4', 'avi', 'mov'])
      if uploaded_file is not None:
          # Save temp file
          with open("temp_video.mp4", "wb") as f:
              f.write(uploaded_file.getbuffer())
          source_path = "temp_video.mp4"
      else:
          st.info("Please upload a video file.")
          st.stop()
  
  # Main Control
  start_btn = st.sidebar.button("Start Monitoring")
  stop_btn = st.sidebar.button("Stop")
  
  if 'monitoring' not in st.session_state:
      st.session_state.monitoring = False
  
  if start_btn:
      st.session_state.monitoring = True
  if stop_btn:
      st.session_state.monitoring = False

  # Video Placeholder
  stframe = st.empty()
  
  if st.session_state.monitoring:
      try:
          source = VideoSource(source_type.lower().replace(" ", ""), source_path)
          
          while st.session_state.monitoring:
              frame = source.get_frame()
              if frame is None:
                  st.warning("Video ended or stream failed.")
                  st.session_state.monitoring = False
                  break
              
              # Convert BGR to RGB for Streamlit
              frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
              stframe.image(frame_rgb, channels="RGB", use_column_width=True)
              
          source.stop()
      except Exception as e:
          st.error(f"Error: {e}")
  ```

### Task 5: Integration - YOLO Inference
**Goal:** Connect the `VideoSource` frames to the `YOLO` model and display detected bounding boxes.

**Files:**
- Create: `src/detection/detector.py`
- Modify: `main.py`

- [ ] **Step 1: Implement Detector Class**
  ```python
  # src/detection/detector.py
  from ultralytics import YOLO
  import cv2
  
  class SafetyDetector:
      def __init__(self, model_path="yolov8n.pt", conf_threshold=0.5):
          self.model = YOLO(model_path)
          self.conf = conf_threshold
          
      def detect(self, frame):
          # Run inference
          results = self.model(frame, conf=self.conf, verbose=False)
          return results[0] # Return first result
      
      def plot_results(self, result, frame):
          # Use built-in plotter for MVP
          return result.plot()
  ```

- [ ] **Step 2: Update `main.py` to use Detector**
  ```python
  # main.py update
  # Add imports
  from src.detection.detector import SafetyDetector

  # In Sidebar
  conf = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.5)

  # In Main Loop
  # Initialize detector (cached ideally, but simple for now)
  detector = SafetyDetector(conf_threshold=conf) 
  
  # Inside while loop:
  result = detector.detect(frame)
  annotated_frame = detector.plot_results(result, frame)
  
  # Update stframe with annotated_frame instead of raw frame
  frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
  stframe.image(frame_rgb, channels="RGB", use_column_width=True)
  ```

### Task 6: ROI (Region of Interest) Logic
**Goal:** Allow user to define a polygon and check if detections are inside it.

**Files:**
- Create: `src/utils/geometry.py`
- Modify: `main.py`

- [ ] **Step 1: Create geometry utility**
  ```python
  # src/utils/geometry.py
  import cv2
  import numpy as np

  def is_point_in_polygon(point, polygon_points):
      """
      point: (x, y)
      polygon_points: list of (x, y) tuples
      """
      poly_array = np.array(polygon_points, dtype=np.int32)
      # pointPolygonTest returns positive if inside, negative if outside, 0 if on edge
      dist = cv2.pointPolygonTest(poly_array, point, False)
      return dist >= 0

  def draw_roi(frame, polygon_points, color=(0, 255, 255)):
      poly_array = np.array(polygon_points, dtype=np.int32)
      cv2.polylines(frame, [poly_array], True, color, 2)
      return frame
  ```

- [ ] **Step 2: Implement ROI Selector in UI (Simplified 4-point click)**
  *Note: Streamlit click events on images are tricky. For MVP Day 2, we will use text input or sliders for coordinates, or a pre-defined click mechanism if using `streamlit-image-coordinates`.*
  *Decision for Plan: Use Normalized Coordinates (0-100%) sliders for a Rectangle ROI for robustness.*

  ```python
  # main.py
  # Sidebar
  st.sidebar.subheader("Danger Zone (ROI)")
  enable_roi = st.sidebar.checkbox("Enable ROI")
  
  roi_x1 = st.sidebar.slider("X1 (%)", 0, 100, 10)
  roi_y1 = st.sidebar.slider("Y1 (%)", 0, 100, 10)
  roi_x2 = st.sidebar.slider("X2 (%)", 0, 100, 90)
  roi_y2 = st.sidebar.slider("Y2 (%)", 0, 100, 90)
  
  # In Main Loop
  if enable_roi:
      h, w = frame.shape[:2]
      x1 = int(roi_x1/100 * w)
      y1 = int(roi_y1/100 * h)
      x2 = int(roi_x2/100 * w)
      y2 = int(roi_y2/100 * h)
      
      cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
      cv2.putText(annotated_frame, "DANGER ZONE", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
  ```

---

## Phase 3: Advanced Features & Polish (Day 3)

### Task 7: Violation Logic & Logging
**Goal:** Detect specific violations (Missing PPE, ROI intrusion) and log them.

**Files:**
- Create: `src/utils/logger.py`
- Modify: `src/detection/detector.py`

- [ ] **Step 1: Create Database Logger**
  ```python
  # src/utils/logger.py
  import sqlite3
  import os
  from datetime import datetime
  
  class SafetyLogger:
      def __init__(self, db_path="data/logs/safesight.db"):
          self.db_path = db_path
          self.init_db()
          
      def init_db(self):
          conn = sqlite3.connect(self.db_path)
          c = conn.cursor()
          c.execute('''CREATE TABLE IF NOT EXISTS violations
                       (timestamp TEXT, type TEXT, image_path TEXT)''')
          conn.commit()
          conn.close()
          
      def log_violation(self, v_type, image_path):
          conn = sqlite3.connect(self.db_path)
          c = conn.cursor()
          timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          c.execute("INSERT INTO violations VALUES (?, ?, ?)", (timestamp, v_type, image_path))
          conn.commit()
          conn.close()
  ```

- [ ] **Step 2: Implement Violation Check Logic**
  ```python
  # src/detection/detector.py
  # Add check_violations method
  
  def check_violations(self, result, roi=None):
      violations = []
      boxes = result.boxes
      for box in boxes:
          cls = int(box.cls[0])
          conf = float(box.conf[0])
          label = result.names[cls]
          
          # PPE Logic (Assuming 'NO-Hardhat' class exists from training)
          if label == "NO-Hardhat":
              violations.append("Missing Hardhat")
          
          # ROI Logic
          if roi:
               # Check if box center is in ROI
               # x_center, y_center = ...
               # if in_roi: violations.append("Danger Zone Intrusion")
               pass
      return violations
  ```

### Task 8: Alerts (Audio & Snapshot)
**Goal:** Play sound and save image when violation occurs.

**Files:**
- Create: `src/utils/alert.py`
- Modify: `main.py`

- [ ] **Step 1: Implement Alerter**
  ```python
  # src/utils/alert.py
  import cv2
  import os
  from datetime import datetime
  import pygame
  
  class Alerter:
      def __init__(self, sound_file="assets/alert.mp3"):
          self.last_alert_time = 0
          pygame.mixer.init()
          # Load sound if exists, else silent
          
      def trigger(self, frame, violations):
          # 1. Save Snapshot
          timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
          filename = f"data/violations/{timestamp}.jpg"
          cv2.imwrite(filename, frame)
          
          # 2. Play Sound (Throttled)
          # if time.time() - self.last_alert_time > 3:
          #    play_sound()
          
          return filename
  ```

### Task 9: Email Notifications
**Goal:** Send email with attachment in background thread.

**Files:**
- Create: `src/utils/mailer.py`
- Modify: `main.py`

- [ ] **Step 1: Implement Mailer**
  ```python
  # src/utils/mailer.py
  import smtplib
  # Implement send_email_background(subject, body, image_path)
  ```

### Task 10: Final Integration & Movement Speed (Bonus)
**Goal:** Connect all pieces and add the simple speed heuristic.

**Files:**
- Modify: `src/detection/detector.py` (Add tracking)
- Modify: `main.py` (Final UI polish)

- [ ] **Step 1: Add simple centroid tracking**
  * Dictionary mapping object ID to previous (x,y) positions.
  * Calculate pixel distance between frames.
  * If distance > Threshold -> Violation "Running".

- [ ] **Step 2: Final UI Cleanup**
  * Add metrics placeholder (Total Violations Today).
  * Add "Work Area" metadata to logs.

---
