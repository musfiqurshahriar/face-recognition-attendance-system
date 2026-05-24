from database import SessionLocal, Attendance, ClassSession, get_student_by_name
from datetime import datetime

LATE_THRESHOLD_MINUTES = 20


def is_duplicate(roll_number, date):
    db = SessionLocal()
    existing = db.query(Attendance).filter(
        Attendance.roll_number == roll_number,
        Attendance.date == date
    ).first()
    db.close()
    return existing is not None


def get_or_create_session(date, section):
    db = SessionLocal()
    session = db.query(ClassSession).filter(
        ClassSession.date == date,
        ClassSession.section == section
    ).first()

    if not session:
        session = ClassSession(
            date=date,
            section=section,
            first_entry_time=None
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    db.close()
    return session


def update_first_entry(date, section, time_str):
    db = SessionLocal()
    session = db.query(ClassSession).filter(
        ClassSession.date == date,
        ClassSession.section == section
    ).first()

    if session and session.first_entry_time is None:
        session.first_entry_time = time_str
        db.commit()

    db.close()


def calculate_status(role, section, date, current_time_str):
    if role == "teacher":
        return "Present"

    session = get_or_create_session(date, section)

    if session.first_entry_time is None:
        update_first_entry(date, section, current_time_str)
        return "On Time"

    fmt = "%H:%M:%S"
    first_time = datetime.strptime(session.first_entry_time, fmt)
    current_time = datetime.strptime(current_time_str, fmt)
    diff_minutes = (current_time - first_time).total_seconds() / 60

    return "On Time" if diff_minutes <= LATE_THRESHOLD_MINUTES else "Late"


def mark_attendance(name, role, section=None, semester=None):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # Excel থেকে student info নাও
    student = get_student_by_name(name)

    if student is None:
        print(f"[WARNING] {name} — Excel এ নেই")
        return None

    roll = student["roll"]
    sec = section or student["section"]
    sem = student.get("semester", "") or semester or ""

    if is_duplicate(roll, date_str):
        return "duplicate"

    status = calculate_status(role, sec, date_str, time_str)

    db = SessionLocal()
    record = Attendance(
        user_id=roll,
        name=name,
        role=role,
        roll_number=roll,
        section=sec,
        date=date_str,
        time=time_str,
        status=status,
        semester=sem
    )
    db.add(record)
    db.commit()
    db.close()

    print(f"[ATTENDANCE] Roll: {roll} | {name} | {status} | {date_str} {time_str}")
    return status