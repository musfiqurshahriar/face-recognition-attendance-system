from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_required
from database import init_db, get_student_by_email, get_admin_from_env, get_teacher_by_email, load_students_from_excel, load_teachers_from_excel
from attendance_manager import mark_attendance
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)
app.secret_key = "face_attendance_secret_key_2024"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "আগে login করুন।"

class LoginUser:
    def __init__(self, data, role):
        self.id = data.get("roll", data.get("name", "admin"))
        self.name = data["name"]
        self.email = data["login_email"]
        self.role = role
        self.roll_number = data.get("roll", None)
        self.section = data.get("section", None)
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return f"{self.role}:{self.email}"

@login_manager.user_loader
def load_user(user_id):
    if ":" not in user_id:
        return None
    role, email = user_id.split(":", 1)
    if role == "admin":
        admin = get_admin_from_env()
        if admin["login_email"] == email:
            return LoginUser(admin, "admin")
    elif role == "student":
        student = get_student_by_email(email)
        if student:
            return LoginUser(student, "student")
    elif role == "teacher":
        teacher = get_teacher_by_email(email)
        if teacher:
            return LoginUser(teacher, "teacher")
    return None

@app.after_request
def skip_ngrok_warning(response):
    response.headers["ngrok-skip-browser-warning"] = "69420"
    return response

# ==========================================
# API Endpoint for Remote Face Recognition
# ==========================================
@app.route("/api/mark-attendance", methods=["POST"])
def api_mark_attendance():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400
        
    name = data.get("name")
    role = data.get("role")
    semester = data.get("semester")
    
    if not name or not role:
        return jsonify({"status": "error", "message": "Missing name or role"}), 400
        
    result = mark_attendance(name=name, role=role, semester=semester)
    
    if result == "duplicate":
        return jsonify({"status": "duplicate", "message": "Already marked"})
    elif result:
        return jsonify({"status": "success", "status_message": result})
    else:
        return jsonify({"status": "error", "message": "Failed to mark attendance"})

# ==========================================
# SMART BULK & MANUAL ATTENDANCE CONTROLLER
# ==========================================
# আপনার কোড স্ট্রাকচার অনুযায়ী এই রাউটটি /routes/admin.py ফাইলে থাকতে পারে। 
# যদি সেখানে থাকে, তবে এই ফাংশনটি শুধু কেটে নিয়ে সেখানে বসিয়ে দিন।
@app.route("/admin/manual-attendance", methods=["POST"])
@login_required
def manual_attendance():
    role = request.form.get("role")
    identifier = request.form.get("identifier", "").strip()
    status = request.form.get("status", "On Time")
    custom_date = request.form.get("date")

    if not custom_date:
        custom_date = datetime.now().strftime("%Y-%m-%d")

    # কাস্টম ডেট সাপোর্ট করার জন্য attendance_manager এর ফাংশনে ডেট ওভাররাইড লজিক পাঠানো হচ্ছে
    if role == "student" and identifier.lower() == "all":
        # ডাটাবেজ/এক্সেল থেকে সব স্টুডেন্ট নিয়ে আসা
        all_students = load_students_from_excel()
        count = 0
        for student in all_students:
            res = mark_attendance(name=student["name"], role="students", status=status, custom_date=custom_date)
            if res and res != "duplicate":
                count += 1
        flash(f"সফলভাবে মোট {count} জন শিক্ষার্থীর বাল্ক হাজিরা নেওয়া হয়েছে।", "success")
    else:
        # সিঙ্গেল ছাত্র অথবা শিক্ষকের ম্যানুয়াল এন্ট্রি
        target_name = identifier
        if role == "student":
            all_students = load_students_from_excel()
            student_match = next((s for s in all_students if s["roll"] == identifier), None)
            if student_match:
                target_name = student_match["name"]
            role_param = "students"
        else:
            role_param = "teacher"

        res = mark_attendance(name=target_name, role=role_param, status=status, custom_date=custom_date)
        if res == "duplicate":
            flash(f"দুঃখিত, {target_name} এর হাজিরা আজ আগেই নেওয়া হয়েছে!", "danger")
        elif res:
            flash(f"সফলভাবে {target_name} এর ম্যানুয়াল হাজিরা নেওয়া হয়েছে।", "success")
        else:
            flash("হাজিরা নিতে ব্যর্থ! তথ্যগুলো আবার যাচাই করুন।", "danger")

    return redirect(url_for('admin.dashboard'))


from routes.admin import admin_bp
from routes.student import student_bp
from routes.auth import auth_bp
from routes.teacher import teacher_bp

app.register_blueprint(admin_bp)
app.register_blueprint(student_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(teacher_bp)

@app.route("/keep-alive")
def keep_alive():
    from database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return "Server and Database are awake!", 200
    except Exception as e:
        return f"Error waking up DB: {str(e)}", 500
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)