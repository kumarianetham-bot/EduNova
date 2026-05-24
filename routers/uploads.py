from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from models.models import User, Student, Lecturer
from utils.auth import get_current_user
from utils.cloudinary_upload import upload_file, upload_image

router = APIRouter()

@router.post("/avatar", summary="Upload profile avatar (any user)")
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    url = await upload_image(file, folder="edunova/avatars")
    current_user.avatar_url = url
    db.commit()
    return {"message": "Avatar uploaded", "avatar_url": url}


@router.post("/assignment", summary="Upload assignment file (returns URL)")
async def upload_assignment_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    result = await upload_file(file, folder="edunova/assignments")
    return {
        "message": "File uploaded successfully",
        "file_url": result["url"],
        "file_name": result["file_name"],
        "file_size": result["file_size"],
    }


@router.post("/submission", summary="Upload student submission file (returns URL)")
async def upload_submission_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Only students can upload submissions
    student = db.query(Student).filter(Student.user_id == current_user.id).first() if hasattr(current_user, 'id') else None
    result = await upload_file(file, folder="edunova/submissions")
    return {
        "message": "Submission uploaded",
        "file_url": result["url"],
        "file_name": result["file_name"],
        "file_size": result["file_size"],
    }


@router.post("/resource", summary="Upload course resource file (Lecturer)")
async def upload_resource_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    result = await upload_file(file, folder="edunova/resources")
    return {
        "message": "Resource uploaded",
        "file_url": result["url"],
        "file_name": result["file_name"],
        "file_size": result["file_size"],
    }


@router.post("/course-thumbnail", summary="Upload course thumbnail image")
async def upload_thumbnail(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    url = await upload_image(file, folder="edunova/thumbnails")
    return {"message": "Thumbnail uploaded", "thumbnail_url": url}


@router.post("/message-file", summary="Upload file attachment for a message")
async def upload_message_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    result = await upload_file(file, folder="edunova/messages")
    return {
        "message": "File uploaded",
        "file_url": result["url"],
        "file_name": result["file_name"],
        "file_size": result["file_size"],
    }
