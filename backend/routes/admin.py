from flask import Blueprint, render_template, request, send_file
from flask_login import login_required, current_user
from database import SessionLocal, Attendance, User
from sqlalchemy import func
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(f):
    from functools import wraps
    from flask import redirect, url_for
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ["admin", "teacher"]:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    db = SessionLocal()

    today = __import__("datetime").date.today().strftime("%Y-%m-%d")
    today_records = db.query(Attendance).filter(
        Attendance.date == today
    ).order_by(Attendance.roll_number).all()

    total_students = db.query(User).filter(User.role == "student").count()
    today_present = len([r for r in today_records if r.role == "student"])
    today_absent = total_students - today_present

    sections = db.query(User.section).filter(
        User.role == "student", User.section != None
    ).distinct().all()
    sections = [s[0] for s in sections]

    db.close()
    return render_template("admin/dashboard.html",
        today_records=today_records,
        total_students=total_students,
        today_present=today_present,
        today_absent=today_absent,
        sections=sections,
        today=today
    )

@admin_bp.route("/attendance")
@login_required
@admin_required
def attendance():
    db = SessionLocal()

    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    section = request.args.get("section", "")
    semester = request.args.get("semester", "")

    query = db.query(Attendance).filter(Attendance.role == "student")

    if date_from:
        query = query.filter(Attendance.date >= date_from)
    if date_to:
        query = query.filter(Attendance.date <= date_to)
    if section:
        query = query.filter(Attendance.section == section)
    if semester:
        query = query.filter(Attendance.semester == semester)

    records = query.order_by(Attendance.roll_number, Attendance.date).all()

    sections = db.query(User.section).filter(
        User.role == "student", User.section != None
    ).distinct().all()
    sections = [s[0] for s in sections]

    semesters = db.query(Attendance.semester).distinct().all()
    semesters = [s[0] for s in semesters if s[0]]

    db.close()
    return render_template("admin/attendance.html",
        records=records,
        sections=sections,
        semesters=semesters,
        date_from=date_from,
        date_to=date_to,
        selected_section=section,
        selected_semester=semester
    )

@admin_bp.route("/percentage")
@login_required
@admin_required
def percentage():
    db = SessionLocal()

    section = request.args.get("section", "")
    semester = request.args.get("semester", "")

    students = db.query(User).filter(User.role == "student")
    if section:
        students = students.filter(User.section == section)
    students = students.order_by(User.roll_number).all()

    query = db.query(Attendance).filter(Attendance.role == "student")
    if section:
        query = query.filter(Attendance.section == section)
    if semester:
        query = query.filter(Attendance.semester == semester)

    total_days = db.query(
        Attendance.date
    ).filter(Attendance.role == "student").distinct().count()

    result = []
    for student in students:
        present_count = query.filter(
            Attendance.user_id == student.id
        ).count()

        percentage = round((present_count / total_days * 100), 1) if total_days > 0 else 0

        result.append({
            "roll": student.roll_number,
            "name": student.name,
            "section": student.section,
            "present": present_count,
            "total": total_days,
            "percentage": percentage
        })

    sections = db.query(User.section).filter(
        User.role == "student", User.section != None
    ).distinct().all()
    sections = [s[0] for s in sections]

    semesters = db.query(Attendance.semester).distinct().all()
    semesters = [s[0] for s in semesters if s[0]]

    db.close()
    return render_template("admin/percentage.html",
        result=result,
        sections=sections,
        semesters=semesters,
        selected_section=section,
        selected_semester=semester
    )

@admin_bp.route("/export/excel")
@login_required
@admin_required
def export_excel():
    db = SessionLocal()
    section = request.args.get("section", "")
    semester = request.args.get("semester", "")

    s_query = db.query(Attendance).filter(Attendance.role == "student")
    t_query = db.query(Attendance).filter(Attendance.role == "teacher")

    if section:
        s_query = s_query.filter(Attendance.section == section)
    if semester:
        s_query = s_query.filter(Attendance.semester == semester)
        t_query = t_query.filter(Attendance.semester == semester)

    s_records = s_query.order_by(Attendance.roll_number, Attendance.date).all()
    t_records = t_query.order_by(Attendance.name, Attendance.date).all()
    db.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Students sheet
        s_data = [{
            "Roll": r.roll_number,
            "Name": r.name,
            "Section": r.section,
            "Date": r.date,
            "Time": r.time,
            "Status": r.status,
            "Semester": r.semester
        } for r in s_records]
        pd.DataFrame(s_data).to_excel(writer, sheet_name="Students", index=False)

        # Teachers sheet
        t_data = [{
            "Name": r.name,
            "Date": r.date,
            "Time": r.time,
            "Status": r.status
        } for r in t_records]
        pd.DataFrame(t_data).to_excel(writer, sheet_name="Teachers", index=False)

    output.seek(0)
    return send_file(output,
        download_name="attendance_report.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )