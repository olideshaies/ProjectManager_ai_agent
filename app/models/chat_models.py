from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
import uuid

from app.database.session import SessionLocal


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    conversation_id: Optional[uuid.UUID] = Field(description="The ID of the conversation the message belongs to")
    user_message: str = Field(description="The message to be sent to the agent")

class ChatResponse(BaseModel):
    conversation_id: uuid.UUID = Field(description="The ID of the conversation the message belongs to")
    ai_message: str = Field(description="The response from the agent")
