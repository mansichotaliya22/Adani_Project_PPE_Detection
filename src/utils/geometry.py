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
