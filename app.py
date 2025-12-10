


# app.py
import sys
import os
import tempfile
from PyQt5 import QtCore, QtGui, QtWidgets
import cv2
from deepface import DeepFace
import numpy as np

KNOWN_DIR = 'known_faces'
THRESHOLD = 1.0  # cosine distance threshold — tune as needed

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
            # convert BGR->RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame_ready.emit(rgb)
            self.msleep(30)

    def stop(self):
        self.running = False
        self.cap.release()

class DashboardWindow(QtWidgets.QWidget):
    def __init__(self, user_label):
        super().__init__()
        self.setWindowTitle(f'Confidential Dashboard — {user_label}')
        self.resize(500, 300)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(f'Welcome, {user_label}! This is the confidential dashboard.')
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet('font-size: 18px;')
        layout.addWidget(label)

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
        # grab current pixmap and save to temp file
        pix = self.video_label.pixmap()
        if pix is None:
            QtWidgets.QMessageBox.warning(self, 'Error', 'No camera frame available')
            return
        tmp = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        tmp_path = tmp.name
        tmp.close()
        pix.save(tmp_path)

        try:
            # use DeepFace.find to search known faces
            df = DeepFace.find(img_path = tmp_path, db_path = KNOWN_DIR, model_name='ArcFace', detector_backend='mtcnn',distance_metric='cosine', enforce_detection=False)
            # DeepFace.find returns a pandas DataFrame with columns like identity and VGGFace2_cosine or distance column names
            # We'll inspect returned dataframe(s)
            authorized_label = None
            # If df is a list of dataframes (older versions) handle accordingly
            if isinstance(df, list):
                df = df[0]
            if df is None or df.empty:
                authorized_label = None
            else:
                # The identity column contains path to matched image; take top match
                top_identity = df['identity'].iloc[0]
                # extract label (filename without ext)
                label = os.path.splitext(os.path.basename(top_identity))[0]
                # distance or VGGFace2_cosine column — find numeric columns that look like distances
                dist_col = None
                for c in df.columns:
                    if any(x in c.lower() for x in ['cosine', 'distance', 'l2', 'euclidean']):
                        dist_col = c
                        break
                if dist_col is not None:
                    dist = df[dist_col].iloc[0]
                    print('Top match:', label, 'dist=', dist)
                    # choose threshold depending on metric
                    if dist <= THRESHOLD:
                        authorized_label = label
                else:
                    # if no dist column, assume match (conservative)
                    authorized_label = label

            if authorized_label:
                self.open_dashboard(authorized_label)
            else:
                QtWidgets.QMessageBox.critical(self, 'Access Denied', 'Face not recognized or not authorized')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Error during face recognition:\n{e}')
        finally:
            try:
                os.remove(tmp_path)
            except:
                pass

    def open_dashboard(self, user_label):
        self.dashboard = DashboardWindow(user_label)
        self.dashboard.show()

    def closeEvent(self, event):
        self.cam_thread.stop()
        self.cam_thread.wait(1000)
        event.accept()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
