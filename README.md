# Face Authentication Desktop Application (PyQt5 + Deep Learning)
This project is a standalone desktop-based face authentication system built using Python, PyQt5, OpenCV, and Deep Learning (DeepFace/FaceNet). The application uses the computer’s local webcam to capture real-time images and compares them with the stored enrolled faces to verify the identity of the user.

Once a valid and authorized face is detected, the system unlocks a Confidential Dashboard Window inside the application. This dashboard represents any private or restricted resource that only authenticated users can access. Unauthorized users are denied access instantly.

The system does not require any IoT hardware , works completely offline, and performs all processing locally on the user’s machine. It is ideal for desktop security systems, confidential file access, or personal identity-based restrictions.

## Key Features:
- PyQt5 graphical interface with live webcam feed
- Deep learning–based face recognition using DeepFace (ArcFace + MTCNN)
- Secure authentication flow
- Confidential dashboard unlock upon successful recognition
- Pure Python implementation with no external IoT devices
- Optional enrollment script for adding new authorized faces
## How to run Project (setup):
1. Create and activate a virtual environment (recommended).
     - ## Commands
         - `python -m venv file_name` (create the virtual environment)
         - `fiole_name\Scripts\activate` (actvate the created venv)
2. use python version 3.9 .
3. `pip install -r requirements.txt.`
     - This command will install the requirements needs (cuz all the local lib link already being saved in "requirements.txt")
5. Create the known_faces/ directory and add enrollment images (one per user; file named username.jpg).
   - ## Commands
     - `python enroll.py` (it will open the camera module form you pc automatically , clicking the space button will captured pic as an enrollement and then named that .jpg file afterwards it will save your pics at the "known_faces" ).
     - `python app.py` (This is for authentication of the you have saved then it will give you the access of your dashboard and if image get missmatch then it wi9ll give alerting sound ) 
