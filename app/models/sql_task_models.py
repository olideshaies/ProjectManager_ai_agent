import uuid
from sqlalchemy import Column, Text, DateTime, Boolean, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base
from pydantic import BaseModel, Field   
from typing import Optional
from datetime import datetime


class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    priority = Column(String(20), nullable=True)  # For storing priority levels
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=True)  # Reference to associated goal
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class TaskCreateSQL(BaseModel):
    title: str
    description: Optional[str] = Field(description="Description of the task")
    completed: bool = Field(description="Whether the task has been completed", default=False)
    due_date: Optional[datetime] = Field(description="Due date of the task")
    priority: Optional[str] = Field(description="Priority of the task")
    goal_id: Optional[uuid.UUID] = Field(description="ID of the associated goal", default=None)

class TaskOutSQL(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = Field(description="Description of the task")
    completed: bool
    due_date: Optional[datetime] = Field(description="Due date of the task")
    priority: Optional[str] = Field(description="Priority of the task")
    goal_id: Optional[uuid.UUID] = Field(description="ID of the associated goal")
    created_at: Optional[datetime] = Field(description="Creation date of the task")
    updated_at: Optional[datetime] = Field(description="Last update date of the task")

class TaskUpdateSQL(BaseModel):
    id: Optional[uuid.UUID] = Field(description="ID of the task to update")
    title: Optional[str] = Field(description="New title of the task")
    description: Optional[str] = Field(description="New description of the task")
    completed: Optional[bool] = Field(description="Whether the task has been completed")
    due_date: Optional[datetime] = Field(description="New due date of the task")
    priority: Optional[str] = Field(description="New priority of the task")
    goal_id: Optional[uuid.UUID] = Field(description="ID of the associated goal")
    subject: Optional[str] = Field(description="Subject of the task")

class TaskDeleteSQL(BaseModel):
    id: Optional[uuid.UUID] = None
    subject: Optional[str] = None
    message: Optional[str] = None