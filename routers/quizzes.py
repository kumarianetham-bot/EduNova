from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any
from database.db import get_db
from models.models import Quiz, QuizAttempt, Lecturer, Student, Course, Notification
from utils.auth import require_lecturer, get_current_user

router = APIRouter()

class QuizCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = 30
    total_marks: Optional[float] = 100.0
    questions: Optional[List[Any]] = []  # [{question, options, answer, marks}]
    is_active: Optional[bool] = False

class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    total_marks: Optional[float] = None
    questions: Optional[List[Any]] = None
    is_active: Optional[bool] = None

class QuizAttemptCreate(BaseModel):
    quiz_id: int
    answers: List[Any]

@router.post("/", summary="Create a quiz (Lecturer)")
def create_quiz(payload: QuizCreate, db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    lecturer = db.query(Lecturer).filter(Lecturer.user_id == current_user.id).first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")
    course = db.query(Course).filter(Course.id == payload.course_id, Course.lecturer_id == lecturer.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or not yours")
    quiz = Quiz(lecturer_id=lecturer.id, **payload.dict())
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    # Notify students if active
    if payload.is_active:
        from sqlalchemy import text
        student_ids = db.execute(
            text("SELECT student_id FROM course_enrollment WHERE course_id=:cid"), {"cid": payload.course_id}
        ).fetchall()
        for (sid,) in student_ids:
            student = db.query(Student).filter(Student.id == sid).first()
            if student:
                notif = Notification(
                    user_id=student.user_id,
                    title="New Quiz Available",
                    message=f"New quiz '{payload.title}' is now available in {course.title}",
                    notification_type="quiz"
                )
                db.add(notif)
        db.commit()
    return {"message": "Quiz created", "quiz_id": quiz.id}

@router.get("/course/{course_id}", summary="Get all quizzes for a course")
def get_course_quizzes(course_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    quizzes = db.query(Quiz).filter(Quiz.course_id == course_id).all()
    return [
        {
            "id": q.id, "title": q.title, "description": q.description,
            "duration_minutes": q.duration_minutes, "total_marks": q.total_marks,
            "is_active": q.is_active, "questions_count": len(q.questions or []),
            "attempts_count": len(q.attempts), "created_at": q.created_at,
        }
        for q in quizzes
    ]

@router.get("/total", summary="Get lecturer's total quiz count")
def total_quizzes(db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    lecturer = db.query(Lecturer).filter(Lecturer.user_id == current_user.id).first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")
    total = db.query(Quiz).filter(Quiz.lecturer_id == lecturer.id).count()
    return {"total_quizzes": total}

@router.get("/{quiz_id}", summary="Get quiz details with questions")
def get_quiz(quiz_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return {
        "id": quiz.id, "title": quiz.title, "description": quiz.description,
        "duration_minutes": quiz.duration_minutes, "total_marks": quiz.total_marks,
        "is_active": quiz.is_active, "questions": quiz.questions,
        "course_id": quiz.course_id,
    }

@router.put("/{quiz_id}", summary="Update quiz (Lecturer)")
def update_quiz(quiz_id: int, payload: QuizUpdate, db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    lecturer = db.query(Lecturer).filter(Lecturer.user_id == current_user.id).first()
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.lecturer_id == lecturer.id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    for k, v in payload.dict(exclude_none=True).items():
        setattr(quiz, k, v)
    db.commit()
    return {"message": "Quiz updated"}

@router.post("/attempt", summary="Student submits quiz attempt")
def attempt_quiz(payload: QuizAttemptCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=403, detail="Only students can attempt quizzes")
    existing = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == payload.quiz_id, QuizAttempt.student_id == student.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already attempted this quiz")
    quiz = db.query(Quiz).filter(Quiz.id == payload.quiz_id).first()
    if not quiz or not quiz.is_active:
        raise HTTPException(status_code=400, detail="Quiz not available")
    # Auto-score: compare answers to quiz.questions answer field
    score = 0.0
    if quiz.questions:
        for i, q in enumerate(quiz.questions):
            if i < len(payload.answers) and payload.answers[i] == q.get("answer"):
                score += q.get("marks", 0)
    attempt = QuizAttempt(quiz_id=payload.quiz_id, student_id=student.id, answers=payload.answers, score=score)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return {"message": "Quiz submitted", "attempt_id": attempt.id, "score": score, "total_marks": quiz.total_marks}

@router.get("/{quiz_id}/attempts", summary="Get all student attempts for a quiz (Lecturer)")
def get_quiz_attempts(quiz_id: int, db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id).all()
    return [
        {
            "id": a.id,
            "student_id": a.student_id,
            "student_name": a.student.user.full_name if a.student and a.student.user else None,
            "score": a.score,
            "answers": a.answers,
            "submitted_at": a.submitted_at,
        }
        for a in attempts
    ]
