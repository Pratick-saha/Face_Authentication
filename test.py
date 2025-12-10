# Test camera indices
import cv2

for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i} is available")
    cap.release()

# Run this → it will tell you which number is camera index (which is detected)
# Then set your PyQt5 app to use that index:
# Example:
# " self.cap = cv2.VideoCapture(1) "  # replace 1 with the Camera index
