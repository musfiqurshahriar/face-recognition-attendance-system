from flask import Flask
from flask_login import LoginManager
from database import SessionLocal, User, init_db
import hashlib
import os

# ফোল্ডারের আসল লোকেশন বের করার কোড
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../frontend/templates"))
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, "../frontend/static"))

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR
)
app.secret_key = "face_attendance_secret_key_2024"

# ... নিচের বাকি কোড যেমন ছিল তেমনই থাকবে ...

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "আগে login করুন।"

@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    user = db.query(User).filter(User.id == int(user_id)).first()
    db.close()
    if user:
        return LoginUser(user)
    return None

# এখানে LoginUser কে auth.py থেকে ইমপোর্ট করা হলো
from routes.auth import auth_bp, LoginUser
from routes.admin import admin_bp
from routes.student import student_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(student_bp)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)