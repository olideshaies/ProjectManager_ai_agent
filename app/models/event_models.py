# app/models/event_models.py
from typing import Optional, List
from pydantic import BaseModel, Field

class EventExtraction(BaseModel):
    description: str = Field(description="Raw description of the event")
    is_calendar_event: bool = Field(description="Whether this text describes a calendar event")
    confidence_score: float = Field(description="Confidence score between 0 and 1")

class EventDetails(BaseModel):
    name: str = Field(description="Name of the event")
    date: str = Field(description="Date and time of the event in ISO 8601 format")
    duration_minutes: int = Field(description="Expected duration in minutes")
    participants: List[str] = Field(description="List of participants")

class EventConfirmation(BaseModel):
    confirmation_message: str = Field(description="Natural language confirmation message")
    calendar_link: Optional[str] = Field(description="Generated calendar link if applicable")

# For our API request/response
class CalendarRequest(BaseModel):
    user_input: str = Field(description="User input to be parsed for an event")

class CalendarResponse(BaseModel):
    calendar_events: List[EventDetails] = Field(description="List of calendar events")
    confirmation_message: Optional[str] = Field(description="Natural language confirmation message")
    calendar_link: Optional[str] = Field(description="Generated calendar link if applicable")
    error: Optional[str] = Field(description="Error message if the event cannot be parsed")
