# app/routers/events.py
from fastapi import APIRouter, HTTPException
from app.models.event_models import CalendarRequest, CalendarResponse
from app.services.event_processor import process_calendar_request
from app.services.google_calendar import create_google_calendar_event

router = APIRouter()

# Preprocess a calendar event
@router.post("/calendar", response_model=CalendarResponse)
def calendar_event(request: CalendarRequest):
    result = process_calendar_request(request.user_input)
    if not result:
        raise HTTPException(status_code=400, detail="The input does not appear to be a valid calendar event request.")
    return CalendarResponse(
        confirmation_message=result.confirmation_message,
        calendar_link=result.calendar_link
    )

# Create a calendar event
@router.post("/calendar/create", response_model=CalendarResponse)
def create_calendar_event(request: CalendarRequest):
    result = create_google_calendar_event(request.user_input)
    if not result:
        raise HTTPException(status_code=400, detail="The input does not appear to be a valid calendar event request.")
    return CalendarResponse(
        confirmation_message=result.confirmation_message,
        calendar_link=result.calendar_link
    )

# TODO: Implement this
# # Search for calendar events
# router.get("/calendar", response_model=CalendarResponse)
# def get_calendar_event(request: CalendarRequest):
#     result = (request.user_input)
#     if not result:
#         raise HTTPException(status_code=400, detail="The input does not appear to be a valid calendar event request.")
#     return CalendarResponse(
#         calendar_events=result.calendar_events
#     )
