from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database.db import get_db
from models.models import Course, Lecturer, Student, Notification, User, CourseStatus, course_enrollment
from utils.auth import require_admin, get_current_user
from sqlalchemy import text

router = APIRouter()

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    code: str
    status: CourseStatus = CourseStatus.draft
    lecturer_id: Optional[int] = None
    thumbnail_url: Optional[str] = None
    duration_hours: Optional[float] = 0.0

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CourseStatus] = None
    lecturer_id: Optional[int] = None
    thumbnail_url: Optional[str] = None
    duration_hours: Optional[float] = None

@router.post("/", summary="Create a new course (Admin only)")
def create_course(payload: CourseCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(Course).filter(Course.code == payload.code).first():
        raise HTTPException(status_code=400, detail="Course code already exists")
    course = Course(**payload.dict())
    db.add(course)
    db.commit()
    db.refresh(course)
    # Notify lecturer if assigned
    if course.lecturer_id:
        lecturer = db.query(Lecturer).filter(Lecturer.id == course.lecturer_id).first()
        if lecturer:
            notif = Notification(
                user_id=lecturer.user_id,
                title="New Course Assigned",
                message=f"You have been assigned to teach '{course.title}' ({course.code})",
                notification_type="course"
            )
            db.add(notif)
            db.commit()
    return {"message": "Course created successfully", "course_id": course.id}

@router.get("/", summary="Get all courses")
def get_courses(db: Session = Depends(get_db), _=Depends(get_current_user)):
    courses = db.query(Course).all()
    result = []
    for c in courses:
        lecturer_name = None
        if c.lecturer:
            lecturer_name = c.lecturer.user.full_name if c.lecturer.user else None
        result.append({
            "id": c.id, "title": c.title, "code": c.code, "description": c.description,
            "status": c.status, "lecturer_id": c.lecturer_id, "lecturer_name": lecturer_name,
            "total_students": c.total_students, "completion_rate": c.completion_rate,
            "duration_hours": c.duration_hours, "thumbnail_url": c.thumbnail_url,
            "created_at": c.created_at,
        })
    return result

@router.get("/{course_id}", summary="Get course details")
def get_course(course_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    enrolled = db.execute(
        text("SELECT student_id, completion_rate, grade, attendance_rate FROM course_enrollment WHERE course_id=:cid"),
        {"cid": course_id}
    ).fetchall()
    return {
        "id": course.id, "title": course.title, "code": course.code,
        "description": course.description, "status": course.status,
        "lecturer_id": course.lecturer_id,
        "lecturer_name": course.lecturer.user.full_name if course.lecturer and course.lecturer.user else None,
        "total_students": course.total_students,
        "completion_rate": course.completion_rate,
        "duration_hours": course.duration_hours,
        "thumbnail_url": course.thumbnail_url,
        "assignments_count": len(course.assignments),
        "quizzes_count": len(course.quizzes),
        "schedules_count": len(course.schedules),
        "enrollment_details": [{"student_id": r[0], "completion": r[1], "grade": r[2], "attendance": r[3]} for r in enrolled],
        "created_at": course.created_at,
    }

@router.put("/{course_id}", summary="Update course (Admin only)")
def update_course(course_id: int, payload: CourseUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for k, v in payload.dict(exclude_none=True).items():
        setattr(course, k, v)
    db.commit()
    return {"message": "Course updated"}

@router.delete("/{course_id}", summary="Delete course (Admin only)")
def delete_course(course_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return {"message": "Course deleted"}

@router.post("/{course_id}/enroll/{student_id}", summary="Enroll student in course (Admin)")
def enroll_student(course_id: int, student_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    course = db.query(Course).filter(Course.id == course_id).first()
    student = db.query(Student).filter(Student.id == student_id).first()
    if not course or not student:
        raise HTTPException(status_code=404, detail="Course or student not found")
    db.execute(
        text("INSERT OR IGNORE INTO course_enrollment (student_id, course_id) VALUES (:sid, :cid)"),
        {"sid": student_id, "cid": course_id}
    )
    course.total_students = db.execute(
        text("SELECT COUNT(*) FROM course_enrollment WHERE course_id=:cid"), {"cid": course_id}
    ).scalar()
    db.commit()
    # Notify student
    notif = Notification(
        user_id=student.user_id,
        title="Course Enrollment",
        message=f"You have been enrolled in '{course.title}'",
        notification_type="enrollment"
    )
    db.add(notif)
    db.commit()
    return {"message": "Student enrolled successfully"}
