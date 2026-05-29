from flask import Flask, request, jsonify
from flask_login import LoginManager
from database import init_db, get_student_by_email, get_admin_from_env, get_teacher_by_email
from attendance_manager import mark_attendance
from dotenv import load_dotenv
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
    # এটি Render এবং Neon ডাটাবেজ দুটোকেই সজাগ রাখবে
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
    # Render-এর ডায়নামিক পোর্ট নেওয়ার জন্য
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)