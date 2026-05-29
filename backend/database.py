from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv, find_dotenv

# এটি প্রজেক্টের যেকোনো জায়গা থেকে .env ফাইল ঠিকই খুঁজে নেবে
load_dotenv(find_dotenv())

# --- Cloud Database Magic Setup ---
raw_db_url = os.getenv("DATABASE_URL", "sqlite:///../database/attendance.db")

# ডাটাবেজ ঠিকমতো কানেক্ট হচ্ছে কি না, তা টার্মিনালে দেখার জন্য একটি ট্র্যাকার:
print(f"[DEBUG] Connected DB: {raw_db_url[:13]}...")

if raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url
    
# ... (ফাইলের বাকি কোড যেমন আছে তেমনই থাকবে)

EXCEL_PATH = "../database/students.xlsx"
TEACHERS_EXCEL_PATH = "../database/teachers.xlsx"

# SQLite-এর জন্য connect_args লাগে, কিন্তু Cloud Postgres-এর জন্য লাগে না
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    roll_number = Column(String, nullable=True)
    section = Column(String, nullable=True)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    status = Column(String, nullable=False)
    semester = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)
    section = Column(String, nullable=False)
    first_entry_time = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


def load_students_from_excel():
    if not os.path.exists(EXCEL_PATH):
        print(f"[ERROR] {EXCEL_PATH} পাওয়া যায়নি")
        return []

    df = pd.read_excel(EXCEL_PATH)
    df.columns = df.columns.str.strip().str.lower()

    if "session" in df.columns:
        session_col = "session"
    elif "section" in df.columns:
        session_col = "section"
    else:
        session_col = None

    students = []
    for _, row in df.iterrows():
        session_val = str(row[session_col]).strip() if session_col else ""

        guardian = str(row.get("guardian_email", "")).strip()
        if guardian.lower() == "nan":
            guardian = ""

        students.append({
            "name": str(row["name"]).strip(),
            "roll": str(row["roll"]).strip(),
            "section": session_val,
            "login_email": str(row["login_email"]).strip(),
            "login_password": str(row["login_password"]).strip(),
            "guardian_email": guardian,
            "semester": str(row["semester"]).strip()
        })
    return students


def load_teachers_from_excel():
    if not os.path.exists(TEACHERS_EXCEL_PATH):
        print(f"[ERROR] {TEACHERS_EXCEL_PATH} পাওয়া যায়নি")
        return []

    df = pd.read_excel(TEACHERS_EXCEL_PATH)
    df.columns = df.columns.str.strip().str.lower()

    teachers = []
    for _, row in df.iterrows():
        teachers.append({
            "name": str(row["name"]).strip(),
            "designation": str(row.get("designation", "")).strip(),
            "login_email": str(row["login_email"]).strip(),
            "login_password": str(row["login_password"]).strip(),
            "department": str(row.get("department", "")).strip()
        })
    return teachers


def get_student_by_email(email):
    students = load_students_from_excel()
    for s in students:
        if s["login_email"].lower() == email.lower():
            return s
    return None


def get_student_by_name(name):
    students = load_students_from_excel()
    for s in students:
        if s["name"].lower() == name.lower():
            return s
    return None


def get_teacher_by_email(email):
    teachers = load_teachers_from_excel()
    for t in teachers:
        if t["login_email"].lower() == email.lower():
            return t
    return None


def get_teacher_by_name(name):
    teachers = load_teachers_from_excel()
    for t in teachers:
        if t["name"].lower() == name.lower():
            return t
    return None


def get_admin_from_env():
    return {
        "name": "Admin",
        "login_email": os.getenv("ADMIN_EMAIL", "admin@university.com"),
        "login_password": os.getenv("ADMIN_PASSWORD", "admin123"),
        "role": "admin"
    }


def init_db():
    Base.metadata.create_all(bind=engine)
    print("[OK] Database কানেকশন সফল!")


if __name__ == "__main__":
    init_db()