import face_recognition
import cv2
import pickle
import numpy as np
import requests
from datetime import datetime
import json
import os

ENCODINGS_FILE = "../models/encodings.pkl"
OFFLINE_FILE = "offline_queue.json"

TOLERANCE = 0.45
CURRENT_SEMESTER = None

SERVER_URL = "https://face-recognition-attendance-system-yuhz.onrender.com/api/mark-attendance"

# ==========================================
# Anti-Spoof Function
# ==========================================
def is_real_face(face_img):
    """
    True = real face, False = spoof (photo/screen)
    """
    try:
        if face_img is None or face_img.size == 0:
            return True

        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        if h < 20 or w < 20:
            return True  # too small to analyze

        # Laplacian variance — real face এ বেশি texture
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Gradient analysis
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_mean = np.mean(np.sqrt(grad_x**2 + grad_y**2))

        # Real face: laplacian > 30 এবং gradient > 8
        if laplacian_var < 30 or gradient_mean < 8:
            return False  # spoof detected

        return True

    except Exception as e:
        print(f"[WARNING] Anti-spoof check failed: {e}")
        return True


# ==========================================
# Camera Selection
# ==========================================
print("=" * 40)
print("  ক্যামেরা সিলেক্ট করুন:")
print("  1. PC Webcam")
print("  2. Phone Camera (IP Webcam)")
print("=" * 40)
choice = input("আপনার choice (1 বা 2): ").strip()

if choice == "2":
    ip = input("Phone এর IP address দিন (যেমন: 192.168.1.5): ").strip()
    port = input("Port দিন (default 8080, Enter চাপলে 8080): ").strip()
    if not port:
        port = "8080"
    camera_url = f"http://{ip}:{port}/video"
    print(f"[INFO] Phone camera connect হচ্ছে: {camera_url}")
    cap = cv2.VideoCapture(camera_url)
else:
    print("[INFO] PC Webcam চালু হচ্ছে...")
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("[ERROR] ক্যামেরা খুলতে পারেনি! IP বা connection চেক করুন।")
    exit()

print("[INFO] Encoding লোড হচ্ছে...")
with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.load(f)

known_encodings = data["encodings"]
known_names = data["names"]
known_roles = data["roles"]

ROLE_COLORS = {
    "students": (0, 255, 0),
    "teachers": (255, 165, 0),
    "Unknown":  (0, 0, 255),
    "Spoof":    (0, 0, 255)
}

already_marked = set()
already_printed = set()

# ==========================================
# Offline Sync Functions
# ==========================================
def save_offline(payload):
    queue = []
    if os.path.exists(OFFLINE_FILE):
        try:
            with open(OFFLINE_FILE, "r") as f:
                queue = json.load(f)
        except:
            pass

    if payload not in queue:
        queue.append(payload)
        with open(OFFLINE_FILE, "w") as f:
            json.dump(queue, f, indent=4)

def sync_offline():
    if not os.path.exists(OFFLINE_FILE):
        return
    try:
        with open(OFFLINE_FILE, "r") as f:
            queue = json.load(f)
    except:
        return
    if not queue:
        return

    print(f"\n[INFO] ইন্টারনেট পাওয়া গেছে! {len(queue)} টি অফলাইন ডেটা আপলোড হচ্ছে...")
    unsynced = []
    for payload in queue:
        try:
            res = requests.post(SERVER_URL, json=payload, timeout=10)
            if res.status_code != 200:
                unsynced.append(payload)
        except:
            unsynced.append(payload)
            break

    if unsynced:
        with open(OFFLINE_FILE, "w") as f:
            json.dump(unsynced, f, indent=4)
        print(f"[INFO] {len(unsynced)} টি ডেটা আপলোড করা যায়নি।")
    else:
        if os.path.exists(OFFLINE_FILE):
            os.remove(OFFLINE_FILE)
        print("[INFO] সব অফলাইন ডেটা সফলভাবে আপলোড হয়েছে!\n")


# ==========================================
# Main Camera Loop
# ==========================================
print("[INFO] ক্যামেরা চালু। বন্ধ করতে 'q' চাপুন।")
sync_offline()

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] ফ্রেম পাওয়া যাচ্ছে না!")
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    face_names = []
    face_roles = []
    face_statuses = []

    for face_encoding, face_location in zip(face_encodings, face_locations):

        # ==========================================
        # Anti-Spoof Check
        # ==========================================
        top, right, bottom, left = face_location
        top *= 4; right *= 4; bottom *= 4; left *= 4

        face_img = frame[top:bottom, left:right]
        real = is_real_face(face_img)

        if not real:
            face_names.append("Spoof!")
            face_roles.append("Spoof")
            face_statuses.append("FAKE DETECTED")
            print("[ALERT] ⚠️ Spoof attempt detected!")
            continue

        # ==========================================
        # Face Recognition
        # ==========================================
        matches = face_recognition.compare_faces(
            known_encodings, face_encoding, tolerance=TOLERANCE
        )
        name = "Unknown"
        role = "Unknown"

        face_distances = face_recognition.face_distance(known_encodings, face_encoding)

        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index] and face_distances[best_match_index] <= TOLERANCE:
                name = known_names[best_match_index]
                role = known_roles[best_match_index]

        status = "Already Marked" if name in already_marked else ""

        if name != "Unknown" and name not in already_marked:
            payload = {
                "name": name,
                "role": role.rstrip("s"),
                "semester": CURRENT_SEMESTER
            }
            try:
                response = requests.post(SERVER_URL, json=payload, timeout=10)
                if response.status_code == 200:
                    result_data = response.json()
                    db_status = result_data.get("status")
                    if db_status == "duplicate":
                        status = "Already Marked"
                        already_marked.add(name)
                    elif db_status == "success":
                        status = result_data.get("status_message", "Present")
                        already_marked.add(name)
                    else:
                        status = "Failed"
                    sync_offline()
                else:
                    status = f"Server Error ({response.status_code})"
            except requests.exceptions.RequestException:
                status = "Saved Offline"
                save_offline(payload)
                already_marked.add(name)

        if name not in already_printed and name != "Unknown":
            print(f"[INFO] {name} | {status}")
            already_printed.add(name)

        face_names.append(name)
        face_roles.append(role)
        face_statuses.append(status)

    # ==========================================
    # Display
    # ==========================================
    for (top, right, bottom, left), name, role, status in zip(
            face_locations, face_names, face_roles, face_statuses):
        top *= 4; right *= 4; bottom *= 4; left *= 4

        color = ROLE_COLORS.get(role, (0, 0, 255))
        label = f"{name} | {status}" if status else name

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
        cv2.putText(frame, label, (left + 6, bottom - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    cv2.putText(frame, now_str, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Face Recognition Attendance", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()