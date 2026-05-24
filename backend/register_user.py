from database import SessionLocal, User, init_db
from datetime import datetime
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_student(name, email, roll_number, section, semester="Spring 2024"):
    db = SessionLocal()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"[ERROR] {email} — already registered")
        db.close()
        return

    # Password হবে roll number
    user = User(
        name=name,
        email=email,
        password=hash_password(str(roll_number)),
        role="student",
        roll_number=str(roll_number),
        section=section
    )
    db.add(user)
    db.commit()
    print(f"[OK] Student: {name} | Roll: {roll_number} | Section: {section}")
    db.close()

def register_teacher(name, email, password):
    db = SessionLocal()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"[ERROR] {email} — already registered")
        db.close()
        return

    user = User(
        name=name,
        email=email,
        password=hash_password(password),
        role="teacher"
    )
    db.add(user)
    db.commit()
    print(f"[OK] Teacher: {name} | Email: {email}")
    db.close()

def register_admin(name, email, password):
    db = SessionLocal()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"[ERROR] {email} — already registered")
        db.close()
        return

    user = User(
        name=name,
        email=email,
        password=hash_password(password),
        role="admin"
    )
    db.add(user)
    db.commit()
    print(f"[OK] Admin: {name} | Email: {email}")
    db.close()

if __name__ == "__main__":
    init_db()

    print("\n--- Admin ---")
    register_admin(
        name="Admin",
        email="admin@university.com",
        password="admin123"
    )

    print("\n--- Teachers ---")
    register_teacher(
        name="Mr_Rahim",
        email="rahim@university.com",
        password="teacher123"
    )

    print("\n--- Students ---")
    # Format: name, email, roll_number, section
    students = [
        ("Musfiqur",  "musfiqur@gmail.com", "230508", "CSE-A"),
        ("Noman",     "noman@gmail.com",    "230535", "CSE-A"),
        ("Sajeeb",     "sajeeb@gmail.com",  "230524", "CSE-A"),
    ]

    for name, email, roll, section in students:
        register_student(name, email, roll, section)

    print("\n[DONE] সব registration সম্পন্ন")
    print("\nStudent login info:")
    print("  Email: student_name@gmail.com")
    print("  Password: তার roll number")