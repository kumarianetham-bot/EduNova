from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database.db import get_db
from models.models import Message, User, MessageStatus, Notification
from utils.auth import get_current_user

router = APIRouter()

class MessageCreate(BaseModel):
    receiver_id: int
    content: str
    file_url: Optional[str] = None

@router.post("/", summary="Send a message")
def send_message(payload: MessageCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    receiver = db.query(User).filter(User.id == payload.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Recipient not found")
    message = Message(sender_id=current_user.id, **payload.dict())
    db.add(message)
    db.commit()
    db.refresh(message)
    # Notify receiver
    notif = Notification(
        user_id=payload.receiver_id,
        title=f"New message from {current_user.full_name}",
        message=payload.content[:100],
        notification_type="message"
    )
    db.add(notif)
    db.commit()
    return {"message": "Message sent", "message_id": message.id}

@router.get("/inbox", summary="Get received messages")
def get_inbox(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    messages = db.query(Message).filter(
        Message.receiver_id == current_user.id
    ).order_by(Message.sent_at.desc()).all()
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_name": m.sender.full_name if m.sender else None,
            "content": m.content,
            "file_url": m.file_url,
            "status": m.status,
            "sent_at": m.sent_at,
        }
        for m in messages
    ]

@router.get("/sent", summary="Get sent messages")
def get_sent(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    messages = db.query(Message).filter(
        Message.sender_id == current_user.id
    ).order_by(Message.sent_at.desc()).all()
    return [
        {
            "id": m.id,
            "receiver_id": m.receiver_id,
            "receiver_name": m.receiver.full_name if m.receiver else None,
            "content": m.content,
            "file_url": m.file_url,
            "status": m.status,
            "sent_at": m.sent_at,
        }
        for m in messages
    ]

@router.get("/conversation/{user_id}", summary="Get full conversation with a user")
def get_conversation(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    messages = db.query(Message).filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.sent_at.asc()).all()
    # Mark received messages as read
    for m in messages:
        if m.receiver_id == current_user.id and m.status == MessageStatus.sent:
            m.status = MessageStatus.read
    db.commit()
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_name": m.sender.full_name if m.sender else None,
            "receiver_id": m.receiver_id,
            "content": m.content,
            "file_url": m.file_url,
            "status": m.status,
            "sent_at": m.sent_at,
            "is_mine": m.sender_id == current_user.id,
        }
        for m in messages
    ]

@router.delete("/{message_id}", summary="Delete a message")
def delete_message(message_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    message = db.query(Message).filter(
        Message.id == message_id, Message.sender_id == current_user.id
    ).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(message)
    db.commit()
    return {"message": "Message deleted"}
