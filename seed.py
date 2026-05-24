import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, ".")

from database.db import SessionLocal, engine
from models.models import Base, User, Student, Lecturer, Course, UserRole, CourseStatus
from utils.auth import get_password_hash

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Read credentials from .env
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@edunova.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
LECTURER_EMAIL = os.getenv("LECTURER_EMAIL", "john.doe@edunova.com")
LECTURER_PASSWORD = os.getenv("LECTURER_PASSWORD")
STUDENT_EMAIL = os.getenv("STUDENT_EMAIL", "jane.student@edunova.com")
STUDENT_PASSWORD = os.getenv("STUDENT_PASSWORD")

if not db.query(User).filter(User.email == ADMIN_EMAIL).first():
    admin = User(email=ADMIN_EMAIL, full_name="EduNova Admin",
                 hashed_password=get_password_hash(ADMIN_PASSWORD), role=UserRole.admin)
    db.add(admin)
    db.commit()
    print(f"✅ Admin created: {ADMIN_EMAIL}")

if not db.query(User).filter(User.email == LECTURER_EMAIL).first():
    luser = User(email=LECTURER_EMAIL, full_name="Dr. John Doe",
                 hashed_password=get_password_hash(LECTURER_PASSWORD), role=UserRole.lecturer)
    db.add(luser)
    db.commit()
    lecturer = Lecturer(user_id=luser.id, lecturer_id="LEC001",
                       department="Computer Science", specialization="AI & ML")
    db.add(lecturer)
    db.commit()
    print(f"✅ Lecturer created: {LECTURER_EMAIL}")
else:
    lecturer = db.query(Lecturer).join(User).filter(User.email == LECTURER_EMAIL).first()

if not db.query(User).filter(User.email == STUDENT_EMAIL).first():
    suser = User(email=STUDENT_EMAIL, full_name="Jane Student",
                 hashed_password=get_password_hash(STUDENT_PASSWORD), role=UserRole.student)
    db.add(suser)
    db.commit()
    student = Student(user_id=suser.id, student_id="STU001", phone="+237600000001")
    db.add(student)
    db.commit()
    print(f"✅ Student created: {STUDENT_EMAIL}")

if lecturer and not db.query(Course).filter(Course.code == "CS101").first():
    course = Course(title="Introduction to Python", code="CS101",
                   description="Learn Python from scratch.",
                   status=CourseStatus.live, lecturer_id=lecturer.id, duration_hours=40.0)
    db.add(course)
    db.commit()
    print("✅ Course created: CS101 - Introduction to Python")

db.close()
print("\n🎉 Seed complete!")