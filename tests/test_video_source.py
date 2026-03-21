# tests/test_video_source.py
import cv2
import pytest
import os
from src.detection.video_source import VideoSource

def test_video_source_webcam_init():
    # For MVP, we'll test instantiation
    source = VideoSource(source_type="webcam", source_path=0)
    assert source.cap is None # Should be None until started

def test_get_frame_invalid_file():
    with pytest.raises(ValueError):
         VideoSource(source_type="file", source_path="nonexistent.mp4")
