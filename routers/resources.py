from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database.db import get_db
from models.models import Resource, Course, Lecturer, Student, Notification, ResourceType
from utils.auth import get_current_user, require_lecturer
from sqlalchemy import text

router = APIRouter()

class ResourceCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    resource_type: ResourceType = ResourceType.file
    url: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    is_shared_with_students: Optional[bool] = True

@router.post("/", summary="Upload/add a resource (Lecturer or Admin)")
def add_resource(payload: ResourceCreate, db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    resource = Resource(uploader_id=current_user.id, **payload.dict())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    # Notify enrolled students if shared
    if payload.is_shared_with_students:
        course = db.query(Course).filter(Course.id == payload.course_id).first()
        student_ids = db.execute(
            text("SELECT student_id FROM course_enrollment WHERE course_id=:cid"), {"cid": payload.course_id}
        ).fetchall()
        for (sid,) in student_ids:
            student = db.query(Student).filter(Student.id == sid).first()
            if student:
                notif = Notification(
                    user_id=student.user_id,
                    title="New Resource Available",
                    message=f"A new resource '{payload.title}' has been shared in {course.title if course else 'your course'}.",
                    notification_type="resource"
                )
                db.add(notif)
        db.commit()
    return {"message": "Resource added", "resource_id": resource.id}

@router.get("/course/{course_id}", summary="Get all resources for a course")
def get_course_resources(course_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # Students only see shared resources
    if current_user.role == "student":
        resources = db.query(Resource).filter(
            Resource.course_id == course_id, Resource.is_shared_with_students == True
        ).order_by(Resource.created_at.desc()).all()
    else:
        resources = db.query(Resource).filter(
            Resource.course_id == course_id
        ).order_by(Resource.created_at.desc()).all()
    return [_fmt_resource(r) for r in resources]

@router.get("/{resource_id}", summary="Get resource details")
def get_resource(resource_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return _fmt_resource(resource)

@router.delete("/{resource_id}", summary="Delete a resource (Lecturer/Admin)")
def delete_resource(resource_id: int, db: Session = Depends(get_db), current_user=Depends(require_lecturer)):
    resource = db.query(Resource).filter(
        Resource.id == resource_id, Resource.uploader_id == current_user.id
    ).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found or not authorized")
    db.delete(resource)
    db.commit()
    return {"message": "Resource deleted"}

def _fmt_resource(r):
    return {
        "id": r.id, "title": r.title, "description": r.description,
        "resource_type": r.resource_type, "url": r.url,
        "file_name": r.file_name, "file_size": r.file_size,
        "course_id": r.course_id, "uploader_id": r.uploader_id,
        "is_shared_with_students": r.is_shared_with_students,
        "created_at": r.created_at,
    }
