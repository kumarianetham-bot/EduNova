from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database.db import get_db
from models.models import ClassSchedule, Lecturer, Course, Student, Notification
from utils.auth import require_lecturer, get_current_user
from sqlalchemy import text

router = APIRouter()

class ScheduleCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    meeting_link: Optional[str] = None
    is_recurring: Optional[bool] = False

class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    meeting_link: Optional[str] = None

@router.post("/", summary="Schedule a class (Lecturer)")
def create_schedule(payload: ScheduleCreate, db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    lecturer = db.query(Lecturer).filter(Lecturer.user_id == current_user.id).first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")
    course = db.query(Course).filter(Course.id == payload.course_id, Course.lecturer_id == lecturer.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or not yours")
    sched = ClassSchedule(lecturer_id=lecturer.id, **payload.dict())
    db.add(sched)
    db.commit()
    db.refresh(sched)
    # Notify enrolled students
    student_ids = db.execute(
        text("SELECT student_id FROM course_enrollment WHERE course_id=:cid"), {"cid": payload.course_id}
    ).fetchall()
    for (sid,) in student_ids:
        student = db.query(Student).filter(Student.id == sid).first()
        if student:
            notif = Notification(
                user_id=student.user_id,
                title="New Class Scheduled",
                message=f"A new class '{payload.title}' has been scheduled for {course.title} on {payload.start_time.strftime('%Y-%m-%d %H:%M')}.",
                notification_type="schedule"
            )
            db.add(notif)
    db.commit()
    return {"message": "Class scheduled", "schedule_id": sched.id}

@router.get("/", summary="Get all schedules (lecturer's own)")
def get_schedules(db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    lecturer = db.query(Lecturer).filter(Lecturer.user_id == current_user.id).first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")
    schedules = db.query(ClassSchedule).filter(
        ClassSchedule.lecturer_id == lecturer.id
    ).order_by(ClassSchedule.start_time).all()
    return [_fmt_schedule(s) for s in schedules]

@router.get("/course/{course_id}", summary="Get schedules for a course")
def course_schedules(course_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    schedules = db.query(ClassSchedule).filter(
        ClassSchedule.course_id == course_id
    ).order_by(ClassSchedule.start_time).all()
    return [_fmt_schedule(s) for s in schedules]

@router.get("/upcoming", summary="Get upcoming schedules for current user")
def upcoming_schedules(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    now = datetime.utcnow()
    if current_user.role == "lecturer":
        lecturer = db.query(Lecturer).filter(Lecturer.user_id == current_user.id).first()
        schedules = db.query(ClassSchedule).filter(
            ClassSchedule.lecturer_id == lecturer.id,
            ClassSchedule.start_time >= now
        ).order_by(ClassSchedule.start_time).limit(10).all()
    else:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return []
        enrolled_courses = db.execute(
            text("SELECT course_id FROM course_enrollment WHERE student_id=:sid"), {"sid": student.id}
        ).fetchall()
        course_ids = [r[0] for r in enrolled_courses]
        schedules = db.query(ClassSchedule).filter(
            ClassSchedule.course_id.in_(course_ids),
            ClassSchedule.start_time >= now
        ).order_by(ClassSchedule.start_time).limit(10).all()
    return [_fmt_schedule(s) for s in schedules]

@router.put("/{schedule_id}", summary="Update a schedule (Lecturer)")
def update_schedule(schedule_id: int, payload: ScheduleUpdate, db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    lecturer = db.query(Lecturer).filter(Lecturer.user_id == current_user.id).first()
    sched = db.query(ClassSchedule).filter(
        ClassSchedule.id == schedule_id, ClassSchedule.lecturer_id == lecturer.id
    ).first()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    for k, v in payload.dict(exclude_none=True).items():
        setattr(sched, k, v)
    db.commit()
    return {"message": "Schedule updated"}

@router.delete("/{schedule_id}", summary="Delete a schedule (Lecturer)")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    lecturer = db.query(Lecturer).filter(Lecturer.user_id == current_user.id).first()
    sched = db.query(ClassSchedule).filter(
        ClassSchedule.id == schedule_id, ClassSchedule.lecturer_id == lecturer.id
    ).first()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(sched)
    db.commit()
    return {"message": "Schedule deleted"}

def _fmt_schedule(s):
    return {
        "id": s.id, "title": s.title, "description": s.description,
        "course_id": s.course_id, "lecturer_id": s.lecturer_id,
        "start_time": s.start_time, "end_time": s.end_time,
        "meeting_link": s.meeting_link, "is_recurring": s.is_recurring,
        "created_at": s.created_at,
    }
