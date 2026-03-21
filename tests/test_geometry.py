# tests/test_geometry.py
import pytest
from src.utils.geometry import is_point_in_polygon

def test_point_in_rectangle():
    poly = [(0,0), (100,0), (100,100), (0,100)]
    assert is_point_in_polygon((50,50), poly) is True
    assert is_point_in_polygon((150,150), poly) is False
    assert is_point_in_polygon((0,0), poly) is True # On edge
