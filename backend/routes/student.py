from flask import Blueprint, render_template
from flask_login import login_required, current_user
from database import SessionLocal, Attendance

student_bp = Blueprint("student", __name__, url_prefix="/student")

@student_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "student":
        from flask import redirect, url_for
        return redirect(url_for("admin.dashboard"))

    db = SessionLocal()

    records = db.query(Attendance).filter(
        Attendance.user_id == current_user.id
    ).order_by(Attendance.date).all()

    total_days = db.query(Attendance.date).filter(
        Attendance.role == "student",
        Attendance.section == current_user.section
    ).distinct().count()

    present_count = len(records)
    percentage = round((present_count / total_days * 100), 1) if total_days > 0 else 0

    on_time = len([r for r in records if r.status == "On Time"])
    late = len([r for r in records if r.status == "Late"])

    db.close()
    return render_template("student/dashboard.html",
        records=records,
        total_days=total_days,
        present_count=present_count,
        percentage=percentage,
        on_time=on_time,
        late=late
    )