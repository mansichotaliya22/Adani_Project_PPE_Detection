# main.py
import streamlit as st
import cv2
import os
import time
from datetime import datetime
from dotenv import load_dotenv

from src.detection.video_source import VideoSource
from src.detection.detector import SafetyDetector
from src.utils.logger import SafetyLogger
from src.utils.alert import Alerter
from src.utils.mailer import SafetyMailer
from src.utils.video_utils import get_available_cameras

# Load environment variables
load_dotenv()

# App Configuration
st.set_page_config(page_title="SafeSight AI", layout="wide")

# Initialize Modular Components
MODEL_PATH = os.path.join("models", "ppe_yolov8s.pt")
DB_PATH = os.path.join("data", "logs", "safesight.db")

# Sidebar - Configuration
st.sidebar.title("🦺 SafeSight AI Control")
source_type = st.sidebar.radio("Input Source", ["Webcam", "Video File"])

source_path = 0
if source_type == "Webcam":
    with st.sidebar.expander("Webcam Settings", expanded=True):
        if st.button("Scan for Cameras"):
            st.session_state.available_cams = get_available_cameras()
        
        cams = st.session_state.get('available_cams', [0])
        source_path = st.selectbox("Select Camera Index", cams, index=0)
elif source_type == "Video File":
    uploaded_file = st.sidebar.file_uploader("Upload Video", type=['mp4', 'avi', 'mov'])
    if uploaded_file is not None:
        # Save temp file
        temp_video_path = os.path.join("data", "temp_video.mp4")
        os.makedirs("data", exist_ok=True)
        with open(temp_video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        source_path = temp_video_path
    else:
        st.info("Please upload a video file.")
        st.stop()

conf_threshold = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.5)
speed_threshold = st.sidebar.slider("Movement Speed Threshold", 10, 200, 50)

st.sidebar.subheader("Danger Zone (ROI)")
enable_roi = st.sidebar.checkbox("Enable ROI Monitoring", value=True)
roi_x1 = st.sidebar.slider("ROI Left %", 0, 100, 20)
roi_y1 = st.sidebar.slider("ROI Top %", 0, 100, 20)
roi_x2 = st.sidebar.slider("ROI Right %", 0, 100, 80)
roi_y2 = st.sidebar.slider("ROI Bottom %", 0, 100, 80)

work_area = st.sidebar.selectbox("Work Area Type", ["Factory", "Construction", "Warehouse", "Office"])

# Main Dashboard View
st.title("Live Safety Monitoring Dashboard")
st.write(f"Active Monitoring for: **{work_area}**")

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Live Feed")
    stframe = st.empty()

with col2:
    st.subheader("Safety Metrics")
    m1 = st.metric("Total People", 0)
    m2 = st.metric("Violations Detected", 0, delta_color="inverse")
    
    st.subheader("Violation Log")
    v_ui_log = st.empty()
    v_ui_log.info("No violations detected yet.")

# Main Control Buttons
start_btn = st.sidebar.button("Start Monitoring")
stop_btn = st.sidebar.button("Stop")

if 'monitoring' not in st.session_state:
    st.session_state.monitoring = False

if start_btn:
    st.session_state.monitoring = True
if stop_btn:
    st.session_state.monitoring = False

def main():
    if st.session_state.monitoring:
        # Initialize components within the session
        source = None
        frame = None
        try:
            # Initialize Alerter and Mailer
            alerter = Alerter(sound_file="assets/alert.mp3") 
            mailer = SafetyMailer(
                sender=os.getenv("EMAIL_SENDER"),
                receiver=os.getenv("EMAIL_RECEIVER"),
                password=os.getenv("EMAIL_PASSWORD")
            )
            logger = SafetyLogger(db_path=DB_PATH)
            detector = SafetyDetector(model_path=MODEL_PATH, conf_threshold=conf_threshold)
            source = VideoSource(source_type.lower().replace(" ", ""), source_path)
            
            st.info("Monitoring started...")
            
            last_log_time = 0
            last_email_time = 0
            total_violations = 0
            
            while st.session_state.monitoring:
                frame = source.get_frame()
                if frame is None:
                    st.warning("Stream ended or failed.")
                    st.session_state.monitoring = False
                    break
                
                h, w = frame.shape[:2]
                
                # Define ROI in pixels
                roi_px = None
                if enable_roi:
                    rx1 = int(roi_x1/100 * w)
                    ry1 = int(roi_y1/100 * h)
                    rx2 = int(roi_x2/100 * w)
                    ry2 = int(roi_y2/100 * h)
                    roi_px = (rx1, ry1, rx2, ry2)

                # Inference & Detection
                result = detector.detect(frame)
                annotated_frame = detector.plot_results(result, frame)
                
                # Check for Violations
                violations = detector.check_violations(result, frame, roi=roi_px, speed_threshold=speed_threshold)
                
                # Draw ROI on annotated frame
                if enable_roi:
                    cv2.rectangle(annotated_frame, (rx1, ry1), (rx2, ry2), (0, 0, 255), 2)
                    cv2.putText(annotated_frame, "DANGER ZONE", (rx1, ry1-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

                # Count people
                people_count = 0
                if result.boxes is not None:
                    for box in result.boxes:
                        if result.names[int(box.cls[0])] == "person":
                            people_count += 1

                # Alerting & Logging Logic
                current_time = time.time()
                if violations:
                    total_violations += len(violations)
                    # Throttled Logging (every 5 seconds)
                    if current_time - last_log_time > 5:
                        v_type_str = ", ".join(violations)
                        
                        # Trigger Alerter (Save Snapshot + Audio)
                        image_path = alerter.trigger(annotated_frame, violations)
                        
                        # Log to DB
                        logger.log_violation(v_type_str, image_path)
                        
                        # Update UI Log
                        v_ui_log.error(f"Alert: {v_type_str} at {datetime.now().strftime('%H:%M:%S')}")
                        
                        last_log_time = current_time
                        
                        # Throttled Email (every 60 seconds)
                        if current_time - last_email_time > 60:
                            mailer.send_email_background(v_type_str, image_path)
                            last_email_time = current_time

                # Update Metrics
                m1.metric("Total People", people_count)
                m2.metric("Violations Detected", total_violations, delta_color="inverse")
                
                # Display Frame
                frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                stframe.image(frame_rgb, channels="RGB", use_column_width=True)
                
                # Small sleep to prevent UI freeze
                time.sleep(0.01)

            source.stop()
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            st.error(f"Error during monitoring: {e}")
            st.expander("Traceback").code(error_details)
            st.session_state.monitoring = False

if __name__ == "__main__":
    main()
