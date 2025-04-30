# app/db/models/time_session.py
import uuid, datetime as dt
from sqlalchemy import Column, Text, DateTime, Interval, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, INTERVAL
from sqlalchemy.orm import relationship
from app.database.base import Base
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid
class TimeSessionDB(Base):
    __tablename__ = "time_sessions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    task_id  = Column(UUID, ForeignKey("tasks.id"), nullable=False)
    goal     = Column(Text) 
    outcome  = Column(Text)
    start_ts = Column(DateTime(timezone=True), nullable=False)
    end_ts   = Column(DateTime(timezone=True))
    duration = Column(Interval)  
    interuptions = Column(Integer, nullable=True, default=None)

    task     = relationship("TaskDB", back_populates="sessions")

class SessionStartIn(BaseModel):
    task_id: uuid.UUID = Field(description="ID of the task")
    goal: str | None = Field(description="Goal of th    e session")

class SessionStopIn(BaseModel):
    outcome: str | None = Field(description="Outcome of the session")

class SessionPauseIn(BaseModel):
    interuptions: int = Field(description="Number of interuptions during the session")

class TimeSessionOut(BaseModel):
    id: uuid.UUID = Field(description="ID of the time session")
    task_id: uuid.UUID = Field(description="ID of the task")
    goal: str | None = Field(description="Goal of the session")
    outcome: str | None = Field(description="Outcome of the session")   
    start_ts: datetime = Field(description="Start time of the session")
    end_ts: datetime | None = Field(description="End time of the session")
    duration: timedelta | None = Field(description="Duration of the session")
    interuptions: int | None = Field(default=None, description="Number of interuptions during the session")