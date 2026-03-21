import streamlit as st
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
import time
import os
from dotenv import load_dotenv

from utils import init_db, log_violation, send_email_alert
from src.utils.video_utils import get_available_cameras

# Load environment variables
load_dotenv()
init_db()

# App Page Config
st.set_page_config(page_title="SafeSight AI", layout="wide")

# Sidebar
st.sidebar.title("SafeSight AI - Monitoring Control")
source = st.sidebar.selectbox("Input Source", ["Webcam", "Video File"])
cam_index = 0
video_path = None
if source == "Webcam":
    with st.sidebar.expander("Webcam Settings", expanded=True):
        if st.button("Scan for Cameras"):
            st.session_state.available_cams_app = get_available_cameras()
        
        cams = st.session_state.get('available_cams_app', [0])
        cam_index = st.selectbox("Select Camera Index", cams, index=0)
elif source == "Video File":
    uploaded_file = st.sidebar.file_uploader("Upload Video", type=['mp4', 'avi', 'mov'])
    if uploaded_file is not None:
        video_path = os.path.join("data", "temp_app_video.mp4")
        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    else:
        st.info("Please upload a video file.")
        st.stop()
conf_threshold = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.5)

st.sidebar.subheader("Danger Zone (ROI)")
roi_x1 = st.sidebar.slider("ROI Left %", 0, 100, 20)
roi_y1 = st.sidebar.slider("ROI Top %", 0, 100, 20)
roi_x2 = st.sidebar.slider("ROI Right %", 0, 100, 80)
roi_y2 = st.sidebar.slider("ROI Bottom %", 0, 100, 80)

work_area = st.sidebar.selectbox("Work Area Type", ["Factory", "Construction", "Warehouse", "Office"])

# Main View
st.title("Live Safety Monitoring Dashboard")
st.write(f"Monitoring Area: **{work_area}**")

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Live Feed")
    placeholder = st.empty()

with col2:
    st.subheader("Safety Metrics")
    m1 = st.metric("Total People", 0)
    m2 = st.metric("PPE Violations", 0, delta_color="inverse")
    m3 = st.metric("ROI Violations", 0, delta_color="inverse")
    
    st.subheader("Recent Violations")
    v_log = st.empty()
    v_log.info("No violations detected yet.")

def main():
    if st.sidebar.button("Start Monitoring"):
        # Check for weights
        MODEL_PATH = os.path.join("models", "ppe_yolov8s.pt")
        if not os.path.exists(MODEL_PATH):
            st.error(f"Model file not found at {MODEL_PATH}. Please run download_model.py first.")
            return
            
        # Load Model
        try:
            model = YOLO(MODEL_PATH)
        except Exception as e:
            st.error(f"Error loading model: {e}")
            return
            
        CLASSES = model.names
        
        # Open Stream
        if source == "Webcam":
            cap = cv2.VideoCapture(int(cam_index), cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(int(cam_index))
        else:
            cap = cv2.VideoCapture(video_path)
        
        if not cap or not cap.isOpened():
            st.error("Failed to open video source.")
            return

        st.info("Monitoring started...")
        
        # Throttling
        last_log_time = 0
        last_email_time = 0
        total_ppe_violations = 0
        total_roi_violations = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            h, w, _ = frame.shape
            
            # Draw ROI on frame
            rx1, ry1 = int(roi_x1 * w / 100), int(roi_y1 * h / 100)
            rx2, ry2 = int(roi_x2 * w / 100), int(roi_y2 * h / 100)
            cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), (255, 255, 0), 2)
            cv2.putText(frame, "DANGER ZONE", (rx1, ry1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # Inference
            results = model.predict(frame, conf=conf_threshold, verbose=False)
            annotated_frame = results[0].plot()
            
            # Safety Logic
            violations = []
            people_count = 0
            
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                label = CLASSES[cls_id]
                
                # Bbox coordinates
                x1, y1, x2, y2 = box.xyxy[0]
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                
                if label == "Person":
                    people_count += 1
                    # ROI Check
                    if rx1 < cx < rx2 and ry1 < cy < ry2:
                        violations.append("ROI_BREACH")
                        total_roi_violations += 1
                        cv2.circle(annotated_frame, (cx, cy), 10, (0, 0, 255), -1)
                        cv2.putText(annotated_frame, "DANGER!", (cx, cy - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                if label in ["NO-Hardhat", "NO-Safety Vest"]:
                    violations.append(label)
                    total_ppe_violations += 1
                    cv2.putText(annotated_frame, f"VIOLATION: {label}", (50, 50 + len(violations)*30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Logging & Alerts (Throttled to 5 seconds for logging, 60 for email)
            current_time = time.time()
            if violations and (current_time - last_log_time > 5):
                v_type = ", ".join(set(violations))
                img_path = log_violation(v_type, work_area, annotated_frame)
                v_log.success(f"Log Saved: {v_type} at {datetime.datetime.now().strftime('%H:%M:%S')}")
                last_log_time = current_time
                
                # Email Alert (Throttled to 1 minute)
                if current_time - last_email_time > 60:
                    sender = os.getenv("EMAIL_SENDER")
                    receiver = os.getenv("EMAIL_RECEIVER")
                    pwd = os.getenv("EMAIL_PASSWORD")
                    if sender and receiver and pwd:
                        send_email_alert(sender, receiver, pwd, v_type, img_path)
                    last_email_time = current_time

            # Update Metrics
            m1.metric("Total People", people_count)
            m2.metric("PPE Violations", total_ppe_violations, delta_color="inverse")
            m3.metric("ROI Violations", total_roi_violations, delta_color="inverse")
            
            # Display
            annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            placeholder.image(annotated_frame, channels="RGB")
            
            # Slow down slightly to prevent UI lag
            time.sleep(0.01)

        cap.release()

if __name__ == "__main__":
    main()
