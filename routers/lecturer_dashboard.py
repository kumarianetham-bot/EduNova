from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, extract, func
from datetime import datetime, timedelta
from database.db import get_db
from models.models import Lecturer, Course, ClassSchedule, Assignment, Quiz, AttendanceRecord, Announcement
from utils.auth import require_lecturer

router = APIRouter()

def get_lecturer_or_404(current_user, db):
    lecturer = db.query(Lecturer).filter(Lecturer.user_id == current_user.id).first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer profile not found")
    return lecturer

@router.get("/dashboard", summary="Lecturer main dashboard")
def lecturer_dashboard(db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    lecturer = get_lecturer_or_404(current_user, db)
    now = datetime.utcnow()

    total_classes = db.query(Course).filter(Course.lecturer_id == lecturer.id).count()
    total_assignments = db.query(Assignment).filter(Assignment.lecturer_id == lecturer.id).count()
    total_quizzes = db.query(Quiz).filter(Quiz.lecturer_id == lecturer.id).count()

    # Total students across all courses
    total_students = db.execute(
        text("""
            SELECT COUNT(DISTINCT ce.student_id)
            FROM course_enrollment ce
            JOIN courses c ON ce.course_id = c.id
            WHERE c.lecturer_id = :lid
        """), {"lid": lecturer.id}
    ).scalar() or 0

    # Upcoming classes (next 7 days)
    upcoming = db.query(ClassSchedule).filter(
        ClassSchedule.lecturer_id == lecturer.id,
        ClassSchedule.start_time >= now,
        ClassSchedule.start_time <= now + timedelta(days=7)
    ).order_by(ClassSchedule.start_time).limit(10).all()

    # Class overview line graph (classes per month, last 6 months)
    class_graph = []
    for i in range(5, -1, -1):
        month = now - timedelta(days=30 * i)
        count = db.query(ClassSchedule).filter(
            ClassSchedule.lecturer_id == lecturer.id,
            extract('month', ClassSchedule.start_time) == month.month,
            extract('year', ClassSchedule.start_time) == month.year,
        ).count()
        class_graph.append({"month": month.strftime("%b %Y"), "classes": count})

    # Student engagement: avg attendance rate across lecturer's courses
    engagement = db.execute(
        text("""
            SELECT AVG(ce.attendance_rate) as avg_attendance,
                   AVG(ce.completion_rate) as avg_completion,
                   AVG(ce.grade) as avg_grade
            FROM course_enrollment ce
            JOIN courses c ON ce.course_id = c.id
            WHERE c.lecturer_id = :lid
        """), {"lid": lecturer.id}
    ).fetchone()

    # Recent activities (last 5 assignment submissions)
    recent_submissions = db.execute(
        text("""
            SELECT asub.id, a.title, u.full_name, asub.submitted_at, asub.status
            FROM assignment_submissions asub
            JOIN assignments a ON asub.assignment_id = a.id
            JOIN students s ON asub.student_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE a.lecturer_id = :lid
            ORDER BY asub.submitted_at DESC LIMIT 5
        """), {"lid": lecturer.id}
    ).fetchall()

    # Announcements for lecturers
    announcements = db.query(Announcement).filter(
        Announcement.target.in_(["all", "lecturers"])
    ).order_by(Announcement.created_at.desc()).limit(5).all()

    return {
        "summary": {
            "total_classes": total_classes,
            "total_assignments": total_assignments,
            "total_quizzes": total_quizzes,
            "total_students": total_students,
        },
        "class_overview_graph": class_graph,
        "upcoming_classes": [
            {
                "id": s.id, "title": s.title, "course_id": s.course_id,
                "start_time": s.start_time, "end_time": s.end_time,
                "meeting_link": s.meeting_link,
            }
            for s in upcoming
        ],
        "student_engagement": {
            "avg_attendance_rate": round(engagement[0] or 0, 2),
            "avg_completion_rate": round(engagement[1] or 0, 2),
            "avg_grade": round(engagement[2] or 0, 2),
        },
        "recent_activities": [
            {
                "submission_id": r[0], "assignment_title": r[1],
                "student_name": r[2], "submitted_at": r[3], "status": r[4]
            }
            for r in recent_submissions
        ],
        "announcements": [
            {"id": a.id, "title": a.title, "content": a.content, "created_at": a.created_at}
            for a in announcements
        ],
    }

@router.get("/my-classes", summary="Lecturer's courses overview")
def my_classes(db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    lecturer = get_lecturer_or_404(current_user, db)
    from models.models import CourseStatus

    courses = db.query(Course).filter(Course.lecturer_id == lecturer.id).all()
    live_count = sum(1 for c in courses if c.status == CourseStatus.live)
    avg_completion = sum(c.completion_rate for c in courses) / len(courses) if courses else 0

    total_students = db.execute(
        text("""
            SELECT COUNT(DISTINCT ce.student_id) FROM course_enrollment ce
            JOIN courses c ON ce.course_id = c.id WHERE c.lecturer_id = :lid
        """), {"lid": lecturer.id}
    ).scalar() or 0

    return {
        "summary": {
            "total_courses": len(courses),
            "total_students": total_students,
            "live_now": live_count,
            "avg_completion": round(avg_completion, 2),
        },
        "courses": [
            {
                "id": c.id, "title": c.title, "code": c.code,
                "status": c.status, "total_students": c.total_students,
                "completion_rate": c.completion_rate,
                "duration_hours": c.duration_hours,
                "thumbnail_url": c.thumbnail_url,
                "assignments_count": len(c.assignments),
                "quizzes_count": len(c.quizzes),
            }
            for c in courses
        ]
    }

@router.get("/my-classes/{course_id}/students", summary="Students in a lecturer's course")
def course_students(course_id: int, db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    lecturer = get_lecturer_or_404(current_user, db)
    course = db.query(Course).filter(Course.id == course_id, Course.lecturer_id == lecturer.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or not yours")

    stats = db.execute(
        text("""
            SELECT s.id, u.full_name, u.email, s.student_id,
                   ce.attendance_rate, ce.grade, ce.completion_rate, s.at_risk
            FROM course_enrollment ce
            JOIN students s ON ce.student_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE ce.course_id = :cid
        """), {"cid": course_id}
    ).fetchall()

    total = len(stats)
    active = sum(1 for r in stats if r[6] and r[6] > 0)
    at_risk = sum(1 for r in stats if r[7])
    avg_grade = sum(r[5] for r in stats if r[5]) / total if total else 0

    return {
        "summary": {
            "total_students": total,
            "active_students": active,
            "at_risk": at_risk,
            "avg_grade": round(avg_grade, 2),
        },
        "students": [
            {
                "id": r[0], "full_name": r[1], "email": r[2], "student_id": r[3],
                "attendance_rate": r[4], "grade": r[5],
                "completion_rate": r[6], "at_risk": r[7],
            }
            for r in stats
        ]
    }
