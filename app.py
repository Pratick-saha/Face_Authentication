# app.py
import sys
import os
import tempfile
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QBuffer, QIODevice 
import cv2
from deepface import DeepFace
import numpy as np
import smtplib
from email.message import EmailMessage
import io

KNOWN_DIR = 'known_faces'
THRESHOLD = 1.0  # cosine distance threshold — tune as needed

CONFIDENTIAL_FOLDER_PATH = "give the path where your Known folder is shown "

# 1. email (CONFIGURATION)
SENDER_EMAIL = "sender email addr"       
SENDER_PASSWORD = "generate the (app passward) form google account "    
RECEIVER_EMAIL = ["abc@gmail.com", "xyzg@gmail.com", "kjh@gmail.com", "poi@gmail.com"]
SMTP_SERVER = "smtp.gmail.com" 
SMTP_PORT = 587

# ---------------- EMAIL IMAGE CONVERSION ----------------
def pixmap_to_bytes(pixmap):
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    pixmap.save(buffer, "JPEG", 90) 
    return buffer.data().data() 

# ---------------- SUCCESS EMAIL FUNCTION ----------------
def send_login_alert(user_label, image_bytes):
    msg = EmailMessage()
    msg['Subject'] = 'Successful Login Alert: Face Authentication'
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    
    body = f"User *{user_label}* successfully logged in to the confidential system via face authentication. Time: {QtCore.QDateTime.currentDateTime().toString()}."
    msg.set_content(body)

    msg.add_attachment(
        image_bytes, 
        maintype='image', 
        subtype='jpeg', 
        filename='login_image.jpg'
    )
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print("Login alert email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

# ---------------- FAILED ATTEMPT EMAIL FUNCTION ----------------
def send_failed_alert(image_bytes):
    msg = EmailMessage()
    msg['Subject'] = '⚠ Unauthorized Face Login Attempt Detected'
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    body = f"An unauthorized person tried to login.\nTime: {QtCore.QDateTime.currentDateTime().toString()}"
    msg.set_content(body)

    msg.add_attachment(
        image_bytes,
        maintype='image',
        subtype='jpeg',
        filename='failed_attempt.jpg'
    )

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print("⚠ Unauthorized login alert sent!")
    except Exception as e:
        print(f"Email Error (failed attempt): {e}")


# ---------------- CAMERA THREAD ----------------
class CameraThread(QtCore.QThread):
    frame_ready = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cap = cv2.VideoCapture(0)
        self.running = True


    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame_ready.emit(rgb)
            self.msleep(30)

    def stop(self):
        self.running = False
        self.cap.release()


# ---------------- MAIN WINDOW ----------------
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Face Auth — Desktop (PyQt5)')
        self.resize(800, 600)

        self.video_label = QtWidgets.QLabel()
        self.video_label.setFixedSize(640, 480)

        self.auth_btn = QtWidgets.QPushButton('Authenticate')
        self.auth_btn.clicked.connect(self.authenticate)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.video_label, alignment=QtCore.Qt.AlignCenter)
        layout.addWidget(self.auth_btn, alignment=QtCore.Qt.AlignCenter)

        self.cam_thread = CameraThread()
        self.cam_thread.frame_ready.connect(self.update_frame)
        self.cam_thread.start()

    def update_frame(self, rgb_frame):
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qimg = QtGui.QImage(rgb_frame.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(qimg).scaled(self.video_label.size(), QtCore.Qt.KeepAspectRatio)
        self.video_label.setPixmap(pix)

    def authenticate(self):

        pix = self.video_label.pixmap()
        if pix is None:
            QtWidgets.QMessageBox.warning(self, 'Error', 'No camera frame available')
            return

        tmp = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        tmp_path = tmp.name
        tmp.close()
        pix.save(tmp_path)

        try:
            df = DeepFace.find(
                img_path = tmp_path, 
                db_path = KNOWN_DIR, 
                model_name='ArcFace', 
                detector_backend='mtcnn',
                distance_metric='cosine', 
                enforce_detection=False
            )
            
            authorized_label = None

            if isinstance(df, list):
                df = df[0]
            if df is None or df.empty:
                authorized_label = None
            else:
                top_identity = df['identity'].iloc[0]
                label = os.path.splitext(os.path.basename(top_identity))[0]
                
                dist_col = None
                for c in df.columns:
                    if any(x in c.lower() for x in ['cosine', 'distance', 'l2', 'euclidean']):
                        dist_col = c
                        break
                if dist_col is not None:
                    dist = df[dist_col].iloc[0]
                    print('Top match:', label, 'dist=', dist)
                    if dist <= THRESHOLD:
                        authorized_label = label
                else:
                    authorized_label = label

            # ---------------- SUCCESS OR FAILURE EMAIL ----------------
            if authorized_label:
                image_bytes = pixmap_to_bytes(pix)
                send_login_alert(authorized_label, image_bytes)

                self.open_dashboard(authorized_label)

            else:
                image_bytes = pixmap_to_bytes(pix)
                send_failed_alert(image_bytes)

                QtWidgets.QMessageBox.critical(self, 'Access Denied', 'Face not recognized or not authorized')

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Error during face recognition:\n{e}')
        finally:
            try:
                os.remove(tmp_path)
            except:
                pass

    def open_dashboard(self, user_label):
        QtWidgets.QMessageBox.information(self, 'Access Granted', f'Welcome, {user_label}! Opening confidential folder.')
        
        try:
            if sys.platform == 'win32':
                os.startfile(CONFIDENTIAL_FOLDER_PATH) 
            elif sys.platform == 'darwin':
                os.system(f'open "{CONFIDENTIAL_FOLDER_PATH}"') 
            else:
                os.system(f'xdg-open "{CONFIDENTIAL_FOLDER_PATH}"') 
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Could not open folder:\n{e}')    

    def closeEvent(self, event):
        self.cam_thread.stop()
        self.cam_thread.wait(1000)
        event.accept()


# ---------------- RUN APP ----------------
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

