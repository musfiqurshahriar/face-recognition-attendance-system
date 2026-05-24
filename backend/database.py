from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///../database/attendance.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)       # "student" / "teacher" / "admin"
    roll_number = Column(String, nullable=True) # শুধু student এর জন্য
    section = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    roll_number = Column(String, nullable=True)
    section = Column(String, nullable=True)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    status = Column(String, nullable=False)
    semester = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)
    section = Column(String, nullable=False)
    first_entry_time = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


def init_db():
    Base.metadata.create_all(bind=engine)
    print("[OK] Database তৈরি হয়েছে → database/attendance.db")


if __name__ == "__main__":
    init_db()