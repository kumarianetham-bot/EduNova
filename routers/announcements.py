from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database.db import get_db
from models.models import Announcement, Notification, Student, Lecturer, User, AnnouncementTarget
from utils.auth import require_admin, get_current_user

router = APIRouter()

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    target: AnnouncementTarget = AnnouncementTarget.all

@router.post("/", summary="Create announcement (Admin only)")
def create_announcement(payload: AnnouncementCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    ann = Announcement(admin_id=admin.id, title=payload.title, content=payload.content, target=payload.target)
    db.add(ann)
    db.commit()
    db.refresh(ann)

    # Determine who gets notified
    recipients = []
    if payload.target == AnnouncementTarget.all:
        recipients = db.query(User).filter(User.is_active == True).all()
    elif payload.target == AnnouncementTarget.students:
        students = db.query(Student).all()
        recipients = [db.query(User).filter(User.id == s.user_id).first() for s in students]
    elif payload.target == AnnouncementTarget.lecturers:
        lecturers = db.query(Lecturer).all()
        recipients = [db.query(User).filter(User.id == l.user_id).first() for l in lecturers]

    for user in recipients:
        if user:
            notif = Notification(
                user_id=user.id, title=f"Announcement: {payload.title}",
                message=payload.content, notification_type="announcement"
            )
            db.add(notif)
    db.commit()
    return {"message": "Announcement sent", "announcement_id": ann.id, "recipients": len(recipients)}

@router.get("/", summary="Get all announcements (history)")
def get_announcements(db: Session = Depends(get_db), _=Depends(get_current_user)):
    announcements = db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    return [
        {
            "id": a.id, "title": a.title, "content": a.content, "target": a.target,
            "admin_name": a.admin.full_name if a.admin else None, "created_at": a.created_at,
        }
        for a in announcements
    ]

@router.get("/my", summary="Get announcements for current user")
def my_announcements(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    role = current_user.role
    if role == "admin":
        announcements = db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    elif role == "lecturer":
        announcements = db.query(Announcement).filter(
            Announcement.target.in_(["all", "lecturers"])
        ).order_by(Announcement.created_at.desc()).all()
    else:
        announcements = db.query(Announcement).filter(
            Announcement.target.in_(["all", "students"])
        ).order_by(Announcement.created_at.desc()).all()
    return [
        {"id": a.id, "title": a.title, "content": a.content, "target": a.target, "created_at": a.created_at}
        for a in announcements
    ]

@router.delete("/{announcement_id}", summary="Delete announcement (Admin)")
def delete_announcement(announcement_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    ann = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    db.delete(ann)
    db.commit()
    return {"message": "Announcement deleted"}
