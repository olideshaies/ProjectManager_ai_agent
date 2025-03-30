# app/services/agent_flow.py

from typing import Optional
from pydantic import BaseModel

class AgentFlowResult(BaseModel):
    message: str
    calendar_link: Optional[str] = None

def run_agent_flow(user_input: str) -> AgentFlowResult:
    """
    1) Takes user input (text)
    2) Calls your agent logic (zero-shot + tools) or a specialized function (e.g. process_calendar_request)
    3) Returns a standardized result
    """
    from app.services.agent import agent_step
    response_text = agent_step(user_input)
    return AgentFlowResult(message=response_text)
