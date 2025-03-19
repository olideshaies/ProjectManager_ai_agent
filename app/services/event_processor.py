# app/services/event_processor.py
import os
import logging
from datetime import datetime
from typing import Optional
from openai import OpenAI
from app.models.event_models import EventExtraction, EventDetails, EventConfirmation
from app.services.google_calendar import create_google_calendar_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o"

def extract_event_info(user_input: str) -> EventExtraction:
    logger.info("Starting event extraction analysis")
    today = datetime.now()
    date_context = f"Today is {today.strftime('%A, %B %d, %Y')}."
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": f"{date_context} Analyze if the text describes a calendar event."},
            {"role": "user", "content": user_input},
        ],
        response_format=EventExtraction,
    )
    result = completion.choices[0].message.parsed
    logger.info(f"Extraction complete - Is calendar event: {result.is_calendar_event}, Confidence: {result.confidence_score:.2f}")
    return result

def parse_event_details(description: str) -> EventDetails:
    logger.info("Starting event details parsing")
    today = datetime.now()
    date_context = f"Today is {today.strftime('%A, %B %d, %Y')}."
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": f"{date_context} Extract detailed event information. When dates reference 'next Tuesday' or similar relative dates, use this current date as reference."},
            {"role": "user", "content": description},
        ],
        response_format=EventDetails,
    )
    result = completion.choices[0].message.parsed
    logger.info(f"Parsed event details - Name: {result.name}, Date: {result.date}, Duration: {result.duration_minutes}min")
    return result

def generate_confirmation(event_details: EventDetails) -> EventConfirmation:
    logger.info("Generating confirmation message")
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": "Generate a natural confirmation message for the event. Sign off with your name; Susie"},
            {"role": "user", "content": str(event_details.model_dump())},
        ],
        response_format=EventConfirmation,
    )
    result = completion.choices[0].message.parsed
    logger.info("Confirmation message generated successfully")
    return result

def process_calendar_request(user_input: str) -> Optional[EventConfirmation]:
    logger.info("Processing calendar request")
    initial_extraction = extract_event_info(user_input)
    if not initial_extraction.is_calendar_event or initial_extraction.confidence_score < 0.7:
        logger.warning(f"Gate check failed - is_calendar_event: {initial_extraction.is_calendar_event}, confidence: {initial_extraction.confidence_score:.2f}")
        return None
    event_details = parse_event_details(initial_extraction.description)
    # Create Google Calendar event and get a link
    calendar_link = create_google_calendar_event(event_details)
    confirmation = generate_confirmation(event_details)
    if calendar_link:
        confirmation.calendar_link = calendar_link
    logger.info("Calendar request processing completed successfully")
    return confirmation
