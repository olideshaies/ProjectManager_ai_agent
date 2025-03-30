# google_calendar.py
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
from typing import List
load_dotenv()

# If modifying scopes, delete the token file to re-auth.
#gmail calendar
SCOPES = ["https://www.googleapis.com/auth/calendar"]
SECRET_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")



def get_calendar_service():
    creds = None
    # token.pickle stores the user's credentials after OAuth login
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If there's no (valid) creds, prompt user to log in again
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save the creds for next time
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)
    return service

# google_calendar.py (continuing)

def create_google_calendar_event(event_details) -> str:
    """
    Insert an event into the user's primary Google Calendar
    Returns the event's HTML link.
    """
    service = get_calendar_service()

    # Convert the LLM's date/time to RFC3339 if needed
    # Example: "2025-03-18T14:00:00" is already valid RFC3339
    start_time = event_details.date  # e.g., "2025-03-18T14:00:00"
    # We'll assume event_details.duration_minutes is an integer
    # to compute the end time. Let's do something naive:
    end_time = "some calculation or parse from start_time + duration"

    # For simplicity, let's say you do a manual parse or arrow/pytz 
    # to add your duration:
    # (Pseudo-code, not robust!)
    # from datetime import datetime, timedelta
    # dt_format = "%Y-%m-%dT%H:%M:%S"
    # parsed_start = datetime.strptime(start_time, dt_format)
    # parsed_end = parsed_start + timedelta(minutes=event_details.duration_minutes)
    # end_time = parsed_end.strftime(dt_format)

    event = {
        "summary": event_details.name,
        "description": f"Participants: {', '.join(event_details.participants)}",
        "start": {
            "dateTime": start_time,
            "timeZone": "America/New_York",  # Change to your timezone
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "America/New_York",
        },
        # optional: add attendees if you have their emails
        # "attendees": [{"email": email} for email in event_details.participants_emails],
    }

    created_event = service.events().insert(calendarId="primary", body=event).execute()

    return created_event.get("htmlLink", "")

# TODO: Implement this
# def search_calendar_events(user_input: str) -> List[EventDetails]:
#     """Search for events in the user's primary calendar"""
#     service = get_calendar_service()
#     events = []
#     events_result = service.events().list(
#         calendarId="primary", maxResults=5, singleEvents=True, 
#         orderBy="startTime"
#     ).execute()

#     events = events_result.get("items", [])
#     if not events:
#         print("No upcoming events found.")
#     else:
#         print("Upcoming events:")
#         for event in events:
#             summary = event.get("summary", "No Title")
#             start = event["start"].get("dateTime", event["start"].get("date"))
#             print(f"- {start}: {summary}")
