from pydantic import BaseModel
from typing import Optional

class AgentResponse(BaseModel):
    text: str
    error: Optional[str] = None