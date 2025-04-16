# app/routers/conversations.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database.session import SessionLocal
from app.services.tools.conversation_tools import create_message, list_messages_in_conversation
from app.models.conversation_models import MessageCreate, MessageOut

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/messages", response_model=MessageOut)
def add_conversation_message(
    msg_in: MessageCreate,
    db: Session = Depends(get_db)
):
    """
    Add a new message to a conversation. 
    If no conversation_id is provided, starts a new conversation_id.
    """
    try:
        return create_message(db, msg_in)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}/messages", response_model=List[MessageOut])
def get_conversation_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Return all messages in the specified conversation.
    """
    try:
        return list_messages_in_conversation(db, conversation_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
