from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from database.db import get_db
from models.models import Student, User, UserRole, course_enrollment
from utils.auth import require_admin, get_current_user, get_password_hash
from sqlalchemy import text

router = APIRouter()

class StudentCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    student_id: str
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    is_active: Optional[bool] = None
    at_risk: Optional[bool] = None

@router.post("/", summary="Add a student (Admin only)")
def add_student(payload: StudentCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    if db.query(Student).filter(Student.student_id == payload.student_id).first():
        raise HTTPException(status_code=400, detail="Student ID already exists")
    user = User(
        email=payload.email, full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password), role=UserRole.student
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    student = Student(
        user_id=user.id, student_id=payload.student_id,
        phone=payload.phone, address=payload.address, date_of_birth=payload.date_of_birth
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"message": "Student added", "student_id": student.id}

@router.get("/", summary="Get all students")
def get_students(db: Session = Depends(get_db), _=Depends(get_current_user)):
    students = db.query(Student).join(User).all()
    result = []
    for s in students:
        avg_grade = db.execute(
            text("SELECT AVG(grade) FROM course_enrollment WHERE student_id=:sid AND grade IS NOT NULL"),
            {"sid": s.id}
        ).scalar()
        total_courses = db.execute(
            text("SELECT COUNT(*) FROM course_enrollment WHERE student_id=:sid"), {"sid": s.id}
        ).scalar()
        result.append({
            "id": s.id, "user_id": s.user_id, "student_id": s.student_id,
            "full_name": s.user.full_name, "email": s.user.email,
            "phone": s.phone, "address": s.address, "date_of_birth": s.date_of_birth,
            "is_active": s.is_active, "at_risk": s.at_risk,
            "avg_grade": round(avg_grade or 0, 2), "total_courses": total_courses,
            "created_at": s.created_at,
        })
    return result

@router.get("/stats", summary="Student stats for admin")
def student_stats(db: Session = Depends(get_db), _=Depends(get_current_user)):
    total = db.query(Student).count()
    active = db.query(Student).filter(Student.is_active == True).count()
    at_risk = db.query(Student).filter(Student.at_risk == True).count()
    avg_grade_result = db.execute(text("SELECT AVG(grade) FROM course_enrollment WHERE grade IS NOT NULL")).scalar()
    return {
        "total_students": total,
        "active_students": active,
        "at_risk": at_risk,
        "avg_grade": round(avg_grade_result or 0, 2),
    }

@router.get("/{student_id}", summary="Get student details")
def get_student(student_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    enrollments = db.execute(
        text("""
            SELECT c.id, c.title, c.code, ce.grade, ce.completion_rate, ce.attendance_rate
            FROM course_enrollment ce JOIN courses c ON ce.course_id = c.id
            WHERE ce.student_id = :sid
        """), {"sid": student_id}
    ).fetchall()
    submissions = [
        {"assignment_id": sub.assignment_id, "grade": sub.grade, "status": sub.status}
        for sub in s.assignment_submissions
    ]
    return {
        "id": s.id, "student_id": s.student_id,
        "full_name": s.user.full_name, "email": s.user.email,
        "phone": s.phone, "address": s.address, "date_of_birth": s.date_of_birth,
        "is_active": s.is_active, "at_risk": s.at_risk,
        "courses": [
            {"course_id": r[0], "title": r[1], "code": r[2], "grade": r[3], "completion": r[4], "attendance": r[5]}
            for r in enrollments
        ],
        "assignment_performance": submissions,
        "created_at": s.created_at,
    }

@router.put("/{student_id}", summary="Update student (Admin)")
def update_student(student_id: int, payload: StudentUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    data = payload.dict(exclude_none=True)
    if "full_name" in data:
        s.user.full_name = data.pop("full_name")
    for k, v in data.items():
        setattr(s, k, v)
    db.commit()
    return {"message": "Student updated"}
