from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database.db import get_db
from models.models import Assignment, AssignmentSubmission, Lecturer, Student, Course, Notification, AssignmentStatus
from utils.auth import require_lecturer, get_current_user

router = APIRouter()

class AssignmentCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    due_date: datetime
    total_marks: Optional[float] = 100.0
    file_url: Optional[str] = None

class SubmissionCreate(BaseModel):
    assignment_id: int
    file_url: Optional[str] = None
    text_answer: Optional[str] = None

class GradeSubmission(BaseModel):
    grade: float
    feedback: Optional[str] = None

@router.post("/", summary="Create a new assignment (Lecturer)")
def create_assignment(payload: AssignmentCreate, db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    lecturer = db.query(Lecturer).filter(Lecturer.user_id == current_user.id).first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")
    course = db.query(Course).filter(Course.id == payload.course_id, Course.lecturer_id == lecturer.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or not yours")
    assignment = Assignment(lecturer_id=lecturer.id, **payload.dict())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    # Notify enrolled students
    from sqlalchemy import text
    student_ids = db.execute(
        text("SELECT student_id FROM course_enrollment WHERE course_id=:cid"), {"cid": payload.course_id}
    ).fetchall()
    for (sid,) in student_ids:
        student = db.query(Student).filter(Student.id == sid).first()
        if student:
            notif = Notification(
                user_id=student.user_id,
                title="New Assignment Posted",
                message=f"New assignment '{payload.title}' in {course.title}. Due: {payload.due_date.strftime('%Y-%m-%d')}",
                notification_type="assignment"
            )
            db.add(notif)
    db.commit()
    return {"message": "Assignment created", "assignment_id": assignment.id}

@router.get("/course/{course_id}", summary="Get all assignments for a course")
def get_course_assignments(course_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    assignments = db.query(Assignment).filter(Assignment.course_id == course_id).order_by(Assignment.due_date).all()
    return [
        {
            "id": a.id, "title": a.title, "description": a.description,
            "due_date": a.due_date, "total_marks": a.total_marks,
            "file_url": a.file_url, "submissions_count": len(a.submissions),
            "created_at": a.created_at,
        }
        for a in assignments
    ]

@router.get("/{assignment_id}/submissions", summary="Get all submissions for an assignment (Lecturer)")
def get_submissions(assignment_id: int, db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    subs = db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment_id).all()
    return [
        {
            "id": s.id,
            "student_id": s.student_id,
            "student_name": s.student.user.full_name if s.student and s.student.user else None,
            "file_url": s.file_url,
            "text_answer": s.text_answer,
            "status": s.status,
            "grade": s.grade,
            "feedback": s.feedback,
            "submitted_at": s.submitted_at,
            "graded_at": s.graded_at,
        }
        for s in subs
    ]

@router.post("/submit", summary="Student submits an assignment")
def submit_assignment(payload: SubmissionCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=403, detail="Only students can submit assignments")
    existing = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == payload.assignment_id,
        AssignmentSubmission.student_id == student.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already submitted")
    submission = AssignmentSubmission(
        assignment_id=payload.assignment_id, student_id=student.id,
        file_url=payload.file_url, text_answer=payload.text_answer,
        status=AssignmentStatus.submitted
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return {"message": "Assignment submitted", "submission_id": submission.id}

@router.put("/submissions/{submission_id}/grade", summary="Grade a submission and send feedback (Lecturer)")
def grade_submission(submission_id: int, payload: GradeSubmission, db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    submission = db.query(AssignmentSubmission).filter(AssignmentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    submission.grade = payload.grade
    submission.feedback = payload.feedback
    submission.status = AssignmentStatus.graded
    submission.graded_at = datetime.utcnow()
    db.commit()
    # Notify student
    if submission.student:
        assignment_title = submission.assignment.title if submission.assignment else "Assignment"
        notif = Notification(
            user_id=submission.student.user_id,
            title="Assignment Graded",
            message=f"Your submission for '{assignment_title}' has been graded. Grade: {payload.grade}. {payload.feedback or ''}",
            notification_type="grade"
        )
        db.add(notif)
        db.commit()
    return {"message": "Submission graded and feedback sent"}
