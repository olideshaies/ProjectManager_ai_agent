from typing import Literal, Union, Optional
from pydantic import BaseModel, Field
from app.models.task_models import CreateTask, TaskList, TaskUpdate, TaskDelete
from app.models.goal_models import GoalCreate, GoalOut, GoalDelete

class AgentDecision(BaseModel):
    """
    The LLM will return JSON like:
    {
      "tool_name": "create_task",
      "tool_input": {
        "title": "...",
        "description": "...",
        "due_date": "...",
        "priority": "...",
        "completed": "...",
        "subject": "..."
      }
    }
    """
    tool_name: Literal["create_task", "search_tasks_by_subject", "list_tasks_by_date_range", 
                       "delete_task", "update_task", "get_task_service",
                       "create_goal", "get_goal", "update_goal", "delete_goal", "list_goals"]
    
    tool_input: Union[CreateTask, TaskList, TaskUpdate, TaskDelete, GoalCreate, GoalOut, GoalDelete]
    
    time_context: Optional[dict] = Field(
        default=None,
        description="Parsed time context from user query"
    )
