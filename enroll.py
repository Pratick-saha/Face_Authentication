import cv2
import os

OUT_DIR = 'known_faces'
os.makedirs(OUT_DIR, exist_ok=True)

cap = cv2.VideoCapture(0)
print('Press SPACE to capture, ESC to exit')
while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow('Enroll - Press SPACE to capture', frame)
    k = cv2.waitKey(1)
    if k % 256 == 27:  # ESC
        break
    elif k % 256 == 32:  # SPACE
        name = input('Enter label for this face (e.g. alice): ').strip()
        if name:
            path = os.path.join(OUT_DIR, f"{name}.jpg")
            cv2.imwrite(path, frame)
            print('Saved', path)
            break

cap.release()
cv2.destroyAllWindows()