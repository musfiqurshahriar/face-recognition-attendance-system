# 📸 Face Recognition Attendance System

A comprehensive, smart, and automated face recognition attendance system built with Python, Flask, and OpenCV. This system is designed for educational institutions to streamline the attendance process, offering role-based access (Admin, Teacher, Student), automated absent notifications, an interactive UI, and cloud backup capabilities.

## 🌟 Key Features

* **Smart Face Recognition:** Uses dlib and face_recognition for highly accurate facial mapping.
* **Anti-Spoofing Detection:** Prevents fake attendance using photos/videos by analyzing Laplacian variance and Sobel gradients.
* **Multi-Camera Support:** Supports laptop webcam, IP Cameras (Phone), and ESP32-CAM simultaneously.
* **Offline Synchronization:** Continues to mark attendance locally if the server is down and syncs automatically when the connection is restored.
* **Role-Based Dashboards:** Separate secure and interactive portals for Admins, Teachers, and Students.
* **Modern UI/UX:** Responsive design with native Dark/Light mode toggle and real-time data visualization using Chart.js.
* **Automated Email Alerts:** Integrates with Brevo API to send automated absence notifications to guardians.
* **Bulk Data Management:** Upload students and teachers seamlessly via .xlsx (Excel) files.
* **Automated Cloud Backup:** A built-in scheduler automatically backs up the database to Google Drive every day at 11:00 PM.

## 🛠️ Technology Stack

* **Backend:** Python, Flask, SQLAlchemy
* **Frontend:** HTML5, CSS3 (Modern UI with Dark/Light Mode), JavaScript, Chart.js, Jinja2 Templates
* **Computer Vision:** OpenCV, face_recognition, numpy, dlib
* **Database:** SQLite (Local) / PostgreSQL (Cloud Support)
* **Data Handling:** Pandas, OpenPyXL
* **APIs & Services:** Brevo SMTP API (Emails), Google Drive API (Backup)

## 🚀 How to Run Locally

**1. Clone the repository:**
> git clone https://github.com/YourUsername/Face-Recognition-Attendance-System.git
> cd Face-Recognition-Attendance-System

**2. Install dependencies:**
> pip install -r requirements-local.txt

**3. Setup Environment Variables:**
Create a `.env` file in the root directory and configure the following:
> ADMIN_EMAIL=admin@university.com
> ADMIN_PASSWORD=your_password
> SENDER_EMAIL=your_email@domain.com
> BREVO_SMTP=smtp-relay.brevo.com
> BREVO_LOGIN=your_brevo_login
> BREVO_PASSWORD=your_brevo_password
> BREVO_API_KEY=your_brevo_api_key

**4. Train the Facial Data:**
Ensure you have student/teacher images in the `dataset/` folder, then run:
> python encode_face.py

**5. Start the Application & Camera:**
Open two terminal windows.
> Terminal 1 (Run Backend): python app.py
> Terminal 2 (Run Camera): python recognize_faces.py