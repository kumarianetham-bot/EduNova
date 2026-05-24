from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from models.models import Student, Course, ClassSchedule, Assignment, AssignmentSubmission, Quiz, QuizAttempt, Announcement
from utils.auth import get_current_user
from sqlalchemy import text
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/dashboard", summary="Student dashboard overview")
def student_dashboard(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    now = datetime.utcnow()

    # Enrolled courses
    enrolled = db.execute(
        text("""
            SELECT c.id, c.title, c.code, c.status, ce.completion_rate, ce.grade, ce.attendance_rate
            FROM course_enrollment ce JOIN courses c ON ce.course_id = c.id
            WHERE ce.student_id = :sid
        """), {"sid": student.id}
    ).fetchall()
    course_ids = [r[0] for r in enrolled]

    # Upcoming classes
    upcoming = []
    if course_ids:
        upcoming = db.query(ClassSchedule).filter(
            ClassSchedule.course_id.in_(course_ids),
            ClassSchedule.start_time >= now,
            ClassSchedule.start_time <= now + timedelta(days=7)
        ).order_by(ClassSchedule.start_time).limit(10).all()

    # Pending assignments
    pending_assignments = []
    if course_ids:
        all_assignments = db.query(Assignment).filter(
            Assignment.course_id.in_(course_ids),
            Assignment.due_date >= now
        ).all()
        submitted_ids = [
            s.assignment_id for s in db.query(AssignmentSubmission).filter(
                AssignmentSubmission.student_id == student.id
            ).all()
        ]
        pending_assignments = [a for a in all_assignments if a.id not in submitted_ids]

    # Announcements for students
    announcements = db.query(Announcement).filter(
        Announcement.target.in_(["all", "students"])
    ).order_by(Announcement.created_at.desc()).limit(5).all()

    avg_grade = db.execute(
        text("SELECT AVG(grade) FROM course_enrollment WHERE student_id=:sid AND grade IS NOT NULL"),
        {"sid": student.id}
    ).scalar()

    return {
        "student_info": {
            "id": student.id,
            "student_id": student.student_id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "is_active": student.is_active,
            "at_risk": student.at_risk,
        },
        "summary": {
            "total_courses": len(enrolled),
            "avg_grade": round(avg_grade or 0, 2),
            "pending_assignments": len(pending_assignments),
        },
        "enrolled_courses": [
            {
                "course_id": r[0], "title": r[1], "code": r[2],
                "status": r[3], "completion_rate": r[4],
                "grade": r[5], "attendance_rate": r[6],
            }
            for r in enrolled
        ],
        "upcoming_classes": [
            {
                "id": s.id, "title": s.title, "course_id": s.course_id,
                "start_time": s.start_time, "end_time": s.end_time,
                "meeting_link": s.meeting_link,
            }
            for s in upcoming
        ],
        "pending_assignments": [
            {
                "id": a.id, "title": a.title, "course_id": a.course_id,
                "due_date": a.due_date, "total_marks": a.total_marks,
            }
            for a in pending_assignments
        ],
        "announcements": [
            {"id": a.id, "title": a.title, "content": a.content, "created_at": a.created_at}
            for a in announcements
        ],
    }

@router.get("/my-grades", summary="Student's grades across all courses")
def my_grades(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    results = db.execute(
        text("""
            SELECT c.id, c.title, c.code, ce.grade, ce.completion_rate, ce.attendance_rate
            FROM course_enrollment ce JOIN courses c ON ce.course_id = c.id
            WHERE ce.student_id = :sid
        """), {"sid": student.id}
    ).fetchall()
    return [
        {"course_id": r[0], "title": r[1], "code": r[2], "grade": r[3], "completion": r[4], "attendance": r[5]}
        for r in results
    ]

@router.get("/my-assignments", summary="Student's assignments and submissions")
def my_assignments(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    enrolled_course_ids = db.execute(
        text("SELECT course_id FROM course_enrollment WHERE student_id=:sid"), {"sid": student.id}
    ).fetchall()
    course_ids = [r[0] for r in enrolled_course_ids]
    if not course_ids:
        return []
    assignments = db.query(Assignment).filter(Assignment.course_id.in_(course_ids)).all()
    result = []
    for a in assignments:
        submission = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == a.id,
            AssignmentSubmission.student_id == student.id
        ).first()
        result.append({
            "id": a.id, "title": a.title, "course_id": a.course_id,
            "due_date": a.due_date, "total_marks": a.total_marks,
            "submitted": submission is not None,
            "submission_status": submission.status if submission else "not_submitted",
            "grade": submission.grade if submission else None,
            "feedback": submission.feedback if submission else None,
        })
    return result
