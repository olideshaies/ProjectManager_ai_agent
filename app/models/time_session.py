# app/db/models/time_session.py
import uuid, datetime as dt
from sqlalchemy import Column, Text, DateTime, Interval, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, INTERVAL
from sqlalchemy.orm import relationship
from app.database.base import Base
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
import uuid

class TimeSessionDB(Base):
    __tablename__ = "time_sessions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    task_id  = Column(UUID, ForeignKey("tasks.id"), nullable=False)
    goal     = Column(Text) 
    outcome  = Column(Text)
    start_ts = Column(DateTime(timezone=True), nullable=False)
    end_ts   = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Interval, nullable=True)  
    interuptions = Column(Integer, nullable=True, default=None)

    # --- New Fields ---
    # Stores the total accumulated time when the timer is not paused
    accumulated_duration = Column(Interval, nullable=False, default=timedelta(0))
    # Stores the timestamp of the last start or resume event
    last_event_ts = Column(DateTime(timezone=True), nullable=True)
    # --- End New Fields ---

    task     = relationship("TaskDB", back_populates="sessions")

class SessionStartIn(BaseModel):
    task_id: uuid.UUID = Field(description="ID of the task")
    goal: str | None = Field(description="Goal of th    e session")

class SessionStopIn(BaseModel):
    outcome: str | None = Field(description="Outcome of the session")

class SessionPauseIn(BaseModel):
    interuptions: int = Field(description="Number of interuptions during the session")

class TimeSessionOut(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    goal: str | None
    outcome: str | None
    start_ts: datetime
    end_ts: datetime | None
    duration: timedelta | None
    interuptions: int | None = Field(default=None)
    # --- Keep necessary state fields --- 
    accumulated_duration: timedelta
    last_event_ts: datetime | None # Frontend needs this to determine state
    # --- Remove calculated field --- 

    class Config:
        from_attributes = True # Use this for Pydantic v2+ ORM mode