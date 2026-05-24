from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from database import SessionLocal, User
import hashlib

auth_bp = Blueprint("auth", __name__)

# LoginUser ক্লাসটি এখানে নিয়ে আসা হলো
class LoginUser:
    def __init__(self, user):
        self.id = user.id
        self.name = user.name
        self.email = user.email
        self.role = user.role
        self.roll_number = user.roll_number
        self.section = user.section
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return str(self.id)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@auth_bp.route("/", methods=["GET", "POST"])
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        db.close()

        if user and user.password == hash_password(password):
            login_user(LoginUser(user))
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            elif user.role == "student":
                return redirect(url_for("student.dashboard"))
            elif user.role == "teacher":
                return redirect(url_for("admin.dashboard"))
        else:
            flash("Email বা Password ভুল!", "error")
            
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))