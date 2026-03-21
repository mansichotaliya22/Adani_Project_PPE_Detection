# src/detection/model_loader.py
from ultralytics import YOLO
import os

def load_model(model_path="yolov8n.pt"):
    """
    Load a YOLO model from a local file or download from Ultralytics.
    """
    try:
        model = YOLO(model_path)
        return model
    except Exception as e:
        print(f"Error loading model {model_path}: {e}")
        # Re-raise or handle as needed
        raise e
