from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import pandas as pd
import os

DATABASE_URL = "sqlite:///../database/attendance.db"
EXCEL_PATH = "../database/students.xlsx"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
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

    # session বা section যেকোনো column name support করবে
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


def get_admin_from_env():
    return {
        "name": "Admin",
        "login_email": os.getenv("ADMIN_EMAIL", "admin@university.com"),
        "login_password": os.getenv("ADMIN_PASSWORD", "admin123"),
        "role": "admin"
    }


def init_db():
    Base.metadata.create_all(bind=engine)
    print("[OK] Database তৈরি হয়েছে → database/attendance.db")


if __name__ == "__main__":
    init_db()