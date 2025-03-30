from dateparser import parse
from datetime import datetime, timezone, timedelta
import re
from typing import Optional, Dict

class TimeParser:
    @staticmethod
    def _enhance_time_interpretation(text: str, parsed_time: datetime) -> datetime:
        """
        Add intelligent handling for common temporal phrases
        that dateparser might miss or interpret differently
        """
        text_lower = text.lower()
        now = datetime.now(timezone.utc)
        
        # Pattern mapping
        patterns = {
            r'\bend of (this|next) week\b': lambda: now + timedelta(
                weeks=1 if 'next' in text_lower else 0,
                days=(6 - now.weekday()) % 7  # Next Sunday
            ),
            r'\bend of (this|next) month\b': lambda: (
                (now.replace(day=28) + timedelta(days=4)).replace(day=1) 
                - timedelta(days=1) + 
                timedelta(weeks=4 if 'next' in text_lower else 0)
            ),
            r'\b(end of|eoy)\b.*\byear\b': lambda: datetime(now.year, 12, 31),
            r'\bmidnight\b': lambda: parsed_time.replace(hour=23, minute=59, second=59),
            r'\bnoon\b': lambda: parsed_time.replace(hour=12, minute=0, second=0)
        }

        for pattern, handler in patterns.items():
            if re.search(pattern, text_lower):
                new_time = handler()
                # Preserve original timezone awareness
                return new_time.replace(tzinfo=timezone.utc) if new_time.tzinfo else new_time.astimezone(timezone.utc)
        
        return parsed_time

    @staticmethod
    def parse_time_reference(text: str) -> Optional[datetime]:
        try:
            parsed = parse(
                text,
                settings={
                    'PREFER_DATES_FROM': 'future',
                    'RELATIVE_BASE': datetime.now(timezone.utc),
                    'TIMEZONE': 'UTC',
                    'RETURN_AS_TIMEZONE_AWARE': True
                }
            )
            if parsed:
                return TimeParser._enhance_time_interpretation(text, parsed)
            return None
        except Exception as e:
            logger.error(f"Time parsing error: {str(e)}")
            return None

    @staticmethod
    def extract_time_context(query: str) -> dict:
        """
        Extract time context from user query.
        Returns a dict with time-related information.
        """
        print(f"\n[DEBUG] Processing query: {query}")
        
        parsed_time = TimeParser.parse_time_reference(query)
        print(f"[DEBUG] Parsed time: {parsed_time}")
        
        if not parsed_time:
            if "this year" in query.lower():
                now = datetime.now(timezone.utc)
                print(f"[DEBUG] Manual 'this year' handling: {now.year}")
                return {
                    "datetime": datetime(now.year, 12, 31),
                    "formatted_date": f"{now.year}-12-31"
                }
            return {}
        
        print(f"[DEBUG] Final time context: {parsed_time}")
        return {
            "datetime": parsed_time,
            "formatted_date": parsed_time.isoformat()
        }
