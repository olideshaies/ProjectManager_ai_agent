from dotenv import load_dotenv
import os
load_dotenv()

# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from app.scripts.calendar_management import process_calendar_request  # Import your function

# 1. Init FastAPI
app = FastAPI(title="Calendar Agent")

# 2. Define the request/response models
class CalendarRequest(BaseModel):
    user_input: str

class CalendarResponse(BaseModel):
    confirmation_message: Optional[str] = None
    calendar_link: Optional[str] = None
    error: Optional[str] = None

# 3. Create an endpoint
@app.post("/calendar", response_model=CalendarResponse)
async def create_calendar_event(req: CalendarRequest):
    """
    Takes user input describing a calendar event,
    calls process_calendar_request, 
    and returns either a confirmation or an error
    """
    confirmation = process_calendar_request(req.user_input)
    if confirmation is None:
        # Means gate check failed - not an event or low confidence
        return CalendarResponse(error="This doesn't appear to be a calendar event.")
    else:
        return CalendarResponse(
            confirmation_message=confirmation.confirmation_message,
            calendar_link=confirmation.calendar_link
        )
    