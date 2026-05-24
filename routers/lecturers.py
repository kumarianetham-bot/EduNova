from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from database.db import get_db
from models.models import Lecturer, User, UserRole, Course
from utils.auth import require_admin, get_current_user, get_password_hash
from sqlalchemy import text

router = APIRouter()

class LecturerCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    lecturer_id: str
    phone: Optional[str] = None
    department: Optional[str] = None
    specialization: Optional[str] = None

class LecturerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    specialization: Optional[str] = None
    is_active: Optional[bool] = None

@router.post("/", summary="Add a lecturer (Admin only)")
def add_lecturer(payload: LecturerCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(
        email=payload.email, full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password), role=UserRole.lecturer
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    lecturer = Lecturer(
        user_id=user.id, lecturer_id=payload.lecturer_id,
        phone=payload.phone, department=payload.department, specialization=payload.specialization
    )
    db.add(lecturer)
    db.commit()
    db.refresh(lecturer)
    return {"message": "Lecturer added", "lecturer_id": lecturer.id}

@router.get("/", summary="Get all lecturers")
def get_lecturers(db: Session = Depends(get_db), _=Depends(get_current_user)):
    lecturers = db.query(Lecturer).join(User).all()
    result = []
    for l in lecturers:
        courses_taught = db.query(Course).filter(Course.lecturer_id == l.id).count()
        total_students = db.execute(
            text("""
                SELECT COUNT(DISTINCT ce.student_id)
                FROM course_enrollment ce
                JOIN courses c ON ce.course_id = c.id
                WHERE c.lecturer_id = :lid
            """), {"lid": l.id}
        ).scalar()
        avg_completion = db.execute(
            text("SELECT AVG(completion_rate) FROM courses WHERE lecturer_id=:lid"), {"lid": l.id}
        ).scalar()
        result.append({
            "id": l.id, "user_id": l.user_id, "lecturer_id": l.lecturer_id,
            "full_name": l.user.full_name, "email": l.user.email,
            "phone": l.phone, "department": l.department, "specialization": l.specialization,
            "rating": l.rating, "is_active": l.is_active,
            "courses_taught": courses_taught,
            "total_students": total_students or 0,
            "completion_rate": round(avg_completion or 0, 2),
            "created_at": l.created_at,
        })
    return result

@router.get("/stats", summary="Lecturer stats")
def lecturer_stats(db: Session = Depends(get_db), _=Depends(get_current_user)):
    total = db.query(Lecturer).count()
    active = db.query(Lecturer).filter(Lecturer.is_active == True).count()
    avg_rating = db.execute(text("SELECT AVG(rating) FROM lecturers")).scalar()
    return {
        "total_lecturers": total,
        "active_lecturers": active,
        "avg_rating": round(avg_rating or 0, 2),
    }

@router.get("/{lecturer_id}", summary="Get lecturer details")
def get_lecturer(lecturer_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    l = db.query(Lecturer).filter(Lecturer.id == lecturer_id).first()
    if not l:
        raise HTTPException(status_code=404, detail="Lecturer not found")
    courses = db.query(Course).filter(Course.lecturer_id == l.id).all()
    return {
        "id": l.id, "lecturer_id": l.lecturer_id,
        "full_name": l.user.full_name, "email": l.user.email,
        "phone": l.phone, "department": l.department, "specialization": l.specialization,
        "rating": l.rating, "is_active": l.is_active,
        "courses": [{"id": c.id, "title": c.title, "code": c.code, "status": c.status, "total_students": c.total_students} for c in courses],
        "reports_count": len(l.reports),
    }

@router.put("/{lecturer_id}", summary="Update lecturer (Admin)")
def update_lecturer(lecturer_id: int, payload: LecturerUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    l = db.query(Lecturer).filter(Lecturer.id == lecturer_id).first()
    if not l:
        raise HTTPException(status_code=404, detail="Lecturer not found")
    data = payload.dict(exclude_none=True)
    if "full_name" in data:
        l.user.full_name = data.pop("full_name")
    for k, v in data.items():
        setattr(l, k, v)
    db.commit()
    return {"message": "Lecturer updated"}
