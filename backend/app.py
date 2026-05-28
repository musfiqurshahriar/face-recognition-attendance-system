from flask import Flask
from flask_login import LoginManager
from database import init_db, get_student_by_email, get_admin_from_env, get_teacher_by_email
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


from routes.admin import admin_bp
from routes.student import student_bp
from routes.auth import auth_bp
from routes.teacher import teacher_bp

app.register_blueprint(admin_bp)
app.register_blueprint(student_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(teacher_bp)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)