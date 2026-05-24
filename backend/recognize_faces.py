import face_recognition
import cv2
import pickle
import numpy as np
from attendance_manager import mark_attendance
from datetime import datetime

ENCODINGS_FILE = "../models/encodings.pkl"
TOLERANCE = 0.5
CURRENT_SEMESTER = None

print("[INFO] Encoding লোড হচ্ছে...")
with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.load(f)

known_encodings = data["encodings"]
known_names = data["names"]
known_roles = data["roles"]

ROLE_COLORS = {
    "students": (0, 255, 0),
    "teachers": (255, 165, 0),
    "Unknown":  (0, 0, 255)
}

already_marked = set()
already_printed = set()

cap = cv2.VideoCapture(0)
print("[INFO] ক্যামেরা চালু। বন্ধ করতে 'q' চাপো।")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    face_names = []
    face_roles = []
    face_statuses = []

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=TOLERANCE)
        name = "Unknown"
        role = "Unknown"

        face_distances = face_recognition.face_distance(known_encodings, face_encoding)

        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_names[best_match_index]
                role = known_roles[best_match_index]

        # Attendance নাও
        status = "Already Marked" if name in already_marked else ""

        if name != "Unknown" and name not in already_marked:
            result = mark_attendance(
                name=name,
                role=role.rstrip("s"),
                semester=None
            )
            if result == "duplicate":
                status = "Already Marked"
                already_marked.add(name)
            elif result:
                status = result
                already_marked.add(name)

        # Terminal এ একবারই print করো
        if name not in already_printed and name != "Unknown":
            print(f"[INFO] {name} | {status}")
            already_printed.add(name)

        face_names.append(name)
        face_roles.append(role)
        face_statuses.append(status)

    # বক্স ও নাম সবসময় দেখাও
    for (top, right, bottom, left), name, role, status in zip(
            face_locations, face_names, face_roles, face_statuses):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        color = ROLE_COLORS.get(role, (0, 0, 255))
        label = f"{name} | {status}" if status else name

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
        cv2.putText(frame, label, (left + 6, bottom - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # উপরে date ও time দেখাও
    now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    cv2.putText(frame, now_str, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Face Recognition Attendance", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()