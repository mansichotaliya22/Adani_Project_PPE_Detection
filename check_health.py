import cv2
import os
import time
from src.detection.video_source import VideoSource
from src.utils.video_utils import get_available_cameras

def check_camera_health():
    print("--- SafeSight AI Camera Health Check ---")
    
    # 1. Check for available cameras
    print("\n[1/3] Scanning for connected cameras...")
    cams = get_available_cameras()
    if not cams:
        print("!! WARNING: No cameras found. Check your connections or drivers.")
    else:
        print(f"OK: Found {len(cams)} camera(s) at indices: {cams}")

    # 2. Test first available camera (if any)
    if cams:
        index = cams[0]
        print(f"\n[2/3] Testing Camera Index {index}...")
        source = VideoSource("webcam", index)
        try:
            source.start()
            print("OK: Video capture started.")
            
            frame = source.get_frame()
            if frame is not None:
                h, w = frame.shape[:2]
                print(f"OK: Frame received (Resolution: {w}x{h}).")
            else:
                print("!! ERROR: Could not read frame from camera.")
            
            source.stop()
            print("OK: Camera released.")
        except Exception as e:
            print(f"!! ERROR: Failed to start camera index {index}: {e}")
    else:
        print("\n[2/3] Skipping camera test (None found).")

    # 3. Check for essential assets
    print("\n[3/3] Checking for essential files...")
    assets = {
        "PPE Model": "models/ppe_yolov8s.pt",
        "Alert Sound": "assets/alert.mp3"
    }
    
    for name, path in assets.items():
        if os.path.exists(path):
            print(f"OK: {name} found.")
        else:
            print(f"!! MISSING: {name} NOT found at '{path}'")

if __name__ == "__main__":
    check_camera_health()
