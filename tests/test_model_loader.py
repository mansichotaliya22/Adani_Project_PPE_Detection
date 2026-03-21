# tests/test_model_loader.py
import os
import pytest
from src.detection.model_loader import load_model

def test_model_download_and_load():
    # Use standard model for initial test
    model_path = "yolov8n.pt"
    model = load_model(model_path)
    assert model is not None
    assert model.names is not None
    # Verify file was downloaded/loaded
    assert os.path.exists(model_path)
