# src/detection/video_source.py
import cv2
import os

class VideoSource:
    def __init__(self, source_type="webcam", source_path=0):
        self.source_type = source_type.lower()
        self.source_path = source_path
        self.cap = None
        self.image_frame = None

        if self.source_type in ["file", "videofile"] and not os.path.exists(str(source_path)):
            raise ValueError(f"File not found: {source_path}")

    def start(self):
        if self.source_type == "image":
            import numpy as np
            if isinstance(self.source_path, np.ndarray):
                self.image_frame = self.source_path
            else:
                self.image_frame = cv2.imread(str(self.source_path))
            
            if self.image_frame is None:
                raise RuntimeError(f"Could not load image from: {self.source_path}")
            return

        if self.source_type == "webcam":
            # On Windows, cv2.CAP_DSHOW is often more robust for webcam access
            index = int(self.source_path)
            self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                # Fallback to default if DSHOW fails
                self.cap = cv2.VideoCapture(index)
        else:
            self.cap = cv2.VideoCapture(self.source_path)
        
        if self.cap is None or not self.cap.isOpened():
            raise RuntimeError(f"Could not open video source: {self.source_type} at path/index {self.source_path}")

    def get_frame(self):
        if self.source_type == "image":
            if self.image_frame is None:
                self.start()
            return self.image_frame.copy()

        if self.cap is None:
            self.start()
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame
    
    def stop(self):
        if self.cap:
            self.cap.release()
            self.cap = None
