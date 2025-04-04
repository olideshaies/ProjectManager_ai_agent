# app/models/goal_models.py
import uuid
from sqlalchemy import Column, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.base import Base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GoalDB(Base):
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    target_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class GoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False
    target_date: Optional[datetime] = None

class GoalOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    completed: bool
    target_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class GoalDelete(BaseModel):
    id: Optional[uuid.UUID] = None
    subject: Optional[str] = None


