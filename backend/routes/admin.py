from flask import Blueprint, render_template, request, send_file, redirect, url_for, flash
from flask_login import login_required, current_user
from database import SessionLocal, Attendance, load_students_from_excel, get_admin_from_env
import pandas as pd
import io
import os
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(f):
    from functools import wraps
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
    ).order_by(
        Attendance.section.desc(),
        Attendance.roll_number
    ).all()

    students_list = load_students_from_excel()
    total_students = len(students_list)
    today_present = len([r for r in today_records if r.role == "student"])
    today_absent = total_students - today_present
    sections = sorted(list(set([s["section"] for s in students_list if s.get("section")])))

    # Absent list
    present_rolls = [r.roll_number for r in today_records if r.role == "student"]
    absent_students = [s for s in students_list if s.get("roll") not in present_rolls]

    # Low attendance alert (70% এর নিচে)
    all_dates = db.query(Attendance.date).filter(
        Attendance.role == "student"
    ).distinct().all()
    total_days = len(all_dates)

    low_attendance = []
    if total_days > 0:
        for student in students_list:
            present_count = db.query(Attendance).filter(
                Attendance.role == "student",
                Attendance.roll_number == student.get("roll")
            ).count()
            percentage = round((present_count / total_days * 100), 1)
            if percentage < 70:
                low_attendance.append({
                    "roll": student.get("roll"),
                    "name": student.get("name"),
                    "section": student.get("section"),
                    "percentage": percentage,
                    "present": present_count,
                    "total": total_days
                })

    # Chart data — শেষ ৭ দিনের attendance trend
    from datetime import datetime, timedelta
    chart_labels = []
    chart_present = []
    chart_absent = []

    for i in range(6, -1, -1):
        day = (datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_label = (datetime.today() - timedelta(days=i)).strftime("%d %b")
        present = db.query(Attendance).filter(
            Attendance.date == day,
            Attendance.role == "student"
        ).distinct(Attendance.roll_number).count()
        absent = total_students - present
        chart_labels.append(day_label)
        chart_present.append(present)
        chart_absent.append(absent)

    db.close()
    return render_template("admin/dashboard.html",
        today_records=today_records,
        total_students=total_students,
        today_present=today_present,
        today_absent=today_absent,
        sections=sections,
        today=today,
        absent_students=absent_students,
        low_attendance=low_attendance,
        chart_labels=chart_labels,
        chart_present=chart_present,
        chart_absent=chart_absent
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

    records = query.order_by(
        Attendance.section.desc(),
        Attendance.roll_number,
        Attendance.date
    ).all()

    students_list = load_students_from_excel()
    sections = sorted(list(set([s["section"] for s in students_list if s.get("section")])))
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

    all_students = load_students_from_excel()
    if section:
        students = [s for s in all_students if s.get("section") == section]
    else:
        students = all_students

    def session_sort_key(s):
        session = s.get("section", "0-0")
        try:
            first_year = int(session.split("-")[0])
        except:
            first_year = 0
        return (-first_year, s.get("roll", ""))

    students = sorted(students, key=session_sort_key)

    total_days = db.query(Attendance.date).filter(
        Attendance.role == "student"
    ).distinct().count()

    result = []
    for student in students:
        student_roll = student.get("roll")
        count_query = db.query(Attendance).filter(
            Attendance.role == "student",
            Attendance.roll_number == student_roll
        )
        if semester:
            count_query = count_query.filter(Attendance.semester == semester)
        present_count = count_query.count()
        percentage = round((present_count / total_days * 100), 1) if total_days > 0 else 0
        result.append({
            "roll": student_roll,
            "name": student.get("name"),
            "section": student.get("section"),
            "present": present_count,
            "total": total_days,
            "percentage": percentage
        })

    sections = sorted(list(set([s["section"] for s in all_students if s.get("section")])))
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

    s_records = s_query.order_by(
        Attendance.section.desc(),
        Attendance.roll_number,
        Attendance.date
    ).all()
    t_records = t_query.order_by(Attendance.name, Attendance.date).all()
    db.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        s_data = [{
            "Roll": r.roll_number,
            "Name": r.name,
            "Session": r.section,
            "Date": r.date,
            "Time": r.time,
            "Status": r.status,
            "Semester": r.semester
        } for r in s_records]
        pd.DataFrame(s_data).to_excel(writer, sheet_name="Students", index=False)

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

@admin_bp.route("/send-notifications", methods=["POST"])
@login_required
@admin_required
def send_notifications():
    from email_sender import send_absent_notifications
    target_date = request.form.get("date", "")
    if not target_date:
        from datetime import date
        target_date = date.today().strftime("%Y-%m-%d")

    result = send_absent_notifications(target_date)
    flash(
        f"{target_date} তারিখের অনুপস্থিত {result['total_absent']} জনের মধ্যে "
        f"{result['success']} জনকে email পাঠানো হয়েছে।",
        "success"
    )
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/upload-students", methods=["GET", "POST"])
@login_required
@admin_required
def upload_students():
    if request.method == "POST":
        file = request.files.get("excel_file")
        if file and file.filename.endswith(".xlsx"):
            save_path = os.path.normpath(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "..", "database", "students.xlsx"
            ))
            file.save(save_path)
            flash("Student list সফলভাবে update হয়েছে!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("শুধু .xlsx ফাইল upload করুন!", "error")

    return render_template("admin/upload_students.html")

@admin_bp.route("/change-password", methods=["GET", "POST"])
@login_required
@admin_required
def change_password():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        new_pass = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        admin = get_admin_from_env()

        if current != admin["login_password"]:
            flash("বর্তমান password ভুল!", "error")
            return redirect(url_for("admin.change_password"))

        if new_pass != confirm:
            flash("নতুন password দুটো মিলছে না!", "error")
            return redirect(url_for("admin.change_password"))

        if len(new_pass) < 6:
            flash("Password কমপক্ষে ৬ অক্ষরের হতে হবে!", "error")
            return redirect(url_for("admin.change_password"))

        # .env ফাইল আপডেট করো
        env_path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", ".env"
        ))

        with open(env_path, "r") as f:
            lines = f.readlines()

        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("ADMIN_PASSWORD="):
                    f.write(f"ADMIN_PASSWORD={new_pass}\n")
                else:
                    f.write(line)

        # dotenv reload
        from dotenv import load_dotenv
        load_dotenv(env_path, override=True)

        flash("Password সফলভাবে পরিবর্তন হয়েছে!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/change_password.html")