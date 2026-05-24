from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from database.db import get_db
from models.models import Student, Lecturer, Course, ClassSchedule, Announcement, User, AttendanceRecord, CourseStatus
from utils.auth import require_admin

router = APIRouter()

@router.get("/dashboard", summary="Admin dashboard overview")
def admin_dashboard(db: Session = Depends(get_db), _=Depends(require_admin)):
    total_students = db.query(Student).count()
    total_lecturers = db.query(Lecturer).count()
    total_courses = db.query(Course).count()
    active_classes = db.query(Course).filter(Course.status == CourseStatus.live).count()

    # Top student by average grade (from enrollment table)
    from sqlalchemy import text
    top_students = db.execute(text("""
        SELECT s.id, u.full_name, u.email, AVG(ce.grade) as avg_grade, COUNT(ce.course_id) as enrolled_courses
        FROM students s
        JOIN users u ON s.user_id = u.id
        JOIN course_enrollment ce ON ce.student_id = s.id
        WHERE ce.grade IS NOT NULL
        GROUP BY s.id, u.full_name, u.email
        ORDER BY avg_grade DESC
        LIMIT 5
    """)).fetchall()

    # Upcoming sessions (next 7 days)
    now = datetime.utcnow()
    upcoming = db.query(ClassSchedule).filter(
        ClassSchedule.start_time >= now,
        ClassSchedule.start_time <= now + timedelta(days=7)
    ).order_by(ClassSchedule.start_time).limit(10).all()

    # Recent activities (last 5 announcements + last 5 schedules)
    recent_announcements = db.query(Announcement).order_by(Announcement.created_at.desc()).limit(5).all()

    # Enrollment line graph: students enrolled per month (last 6 months)
    enrollment_graph = []
    for i in range(5, -1, -1):
        month = now - timedelta(days=30 * i)
        count = db.query(Student).filter(
            extract('month', Student.created_at) == month.month,
            extract('year', Student.created_at) == month.year
        ).count()
        enrollment_graph.append({"month": month.strftime("%b %Y"), "students": count})

    # Lecturer enrollment graph
    lecturer_graph = []
    for i in range(5, -1, -1):
        month = now - timedelta(days=30 * i)
        count = db.query(Lecturer).filter(
            extract('month', Lecturer.created_at) == month.month,
            extract('year', Lecturer.created_at) == month.year
        ).count()
        lecturer_graph.append({"month": month.strftime("%b %Y"), "lecturers": count})

    # Course stats
    course_stats = {
        "total": total_courses,
        "live": db.query(Course).filter(Course.status == CourseStatus.live).count(),
        "scheduled": db.query(Course).filter(Course.status == CourseStatus.scheduled).count(),
        "draft": db.query(Course).filter(Course.status == CourseStatus.draft).count(),
    }

    return {
        "summary": {
            "total_students": total_students,
            "total_lecturers": total_lecturers,
            "total_courses": total_courses,
            "active_classes": active_classes,
        },
        "top_students": [
            {"id": r[0], "full_name": r[1], "email": r[2], "avg_grade": round(r[3] or 0, 2), "enrolled_courses": r[4]}
            for r in top_students
        ],
        "upcoming_sessions": [
            {
                "id": s.id,
                "title": s.title,
                "course_id": s.course_id,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "meeting_link": s.meeting_link,
            }
            for s in upcoming
        ],
        "recent_activities": [
            {"type": "announcement", "title": a.title, "target": a.target, "created_at": a.created_at}
            for a in recent_announcements
        ],
        "enrollment_graph": enrollment_graph,
        "lecturer_graph": lecturer_graph,
        "course_stats": course_stats,
    }
