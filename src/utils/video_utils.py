import cv2

def get_available_cameras(max_to_test=5):
    available_indices = []
    for i in range(max_to_test):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available_indices.append(i)
            cap.release()
        else:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_indices.append(i)
                cap.release()
    return available_indices
