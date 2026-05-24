from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database.db import get_db
from models.models import Report, Lecturer, Notification
from utils.auth import require_admin, get_current_user, require_lecturer

router = APIRouter()

class ReportCreate(BaseModel):
    title: str
    content: str
    report_type: Optional[str] = "progress"

class ReportFeedback(BaseModel):
    admin_feedback: str
    rating: Optional[float] = None

@router.post("/", summary="Lecturer submits a report")
def create_report(payload: ReportCreate, db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    lecturer = db.query(Lecturer).filter(Lecturer.user_id == current_user.id).first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer profile not found")
    report = Report(
        lecturer_id=lecturer.id,
        title=payload.title,
        content=payload.content,
        report_type=payload.report_type
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"message": "Report submitted", "report_id": report.id}

@router.get("/", summary="Admin gets all reports")
def get_all_reports(db: Session = Depends(get_db), _=Depends(require_admin)):
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "content": r.content,
            "report_type": r.report_type,
            "rating": r.rating,
            "admin_feedback": r.admin_feedback,
            "lecturer_id": r.lecturer_id,
            "lecturer_name": r.lecturer.user.full_name if r.lecturer and r.lecturer.user else None,
            "created_at": r.created_at,
        }
        for r in reports
    ]

@router.get("/my", summary="Lecturer views own reports")
def my_reports(db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    lecturer = db.query(Lecturer).filter(Lecturer.user_id == current_user.id).first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer profile not found")
    reports = db.query(Report).filter(Report.lecturer_id == lecturer.id).order_by(Report.created_at.desc()).all()
    return [
        {
            "id": r.id, "title": r.title, "content": r.content,
            "report_type": r.report_type, "rating": r.rating,
            "admin_feedback": r.admin_feedback, "created_at": r.created_at,
        }
        for r in reports
    ]

@router.put("/{report_id}/feedback", summary="Admin rates and gives feedback on a report")
def give_feedback(report_id: int, payload: ReportFeedback, db: Session = Depends(get_db), admin=Depends(require_admin)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.admin_feedback = payload.admin_feedback
    report.admin_id = admin.id
    if payload.rating is not None:
        report.rating = payload.rating
        # Update lecturer's rating as average
        lecturer = db.query(Lecturer).filter(Lecturer.id == report.lecturer_id).first()
        if lecturer:
            from sqlalchemy import func
            avg = db.query(func.avg(Report.rating)).filter(
                Report.lecturer_id == lecturer.id,
                Report.rating != None
            ).scalar()
            lecturer.rating = round(avg or 0, 2)
    db.commit()
    # Notify lecturer
    if report.lecturer:
        notif = Notification(
            user_id=report.lecturer.user_id,
            title="Report Feedback Received",
            message=f"Admin reviewed your report '{report.title}'" + (f" — Rating: {payload.rating}/5" if payload.rating else ""),
            notification_type="report"
        )
        db.add(notif)
        db.commit()
    return {"message": "Feedback submitted"}

@router.delete("/{report_id}", summary="Delete a report (Admin)")
def delete_report(report_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(report)
    db.commit()
    return {"message": "Report deleted"}
