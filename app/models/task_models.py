from typing import Optional, List
from pydantic import BaseModel, Field, model_validator

#Example
# class EventExtraction(BaseModel):
#     description: str = Field(description="Raw description of the event")
#     is_calendar_event: bool = Field(description="Whether this text describes a calendar event")
#     confidence_score: float = Field(description="Confidence score between 0 and 1")

class TaskBase(BaseModel):
    title: str = Field(description="Title of the task")
    description: str = Field(description="Description of the task")
    due_date: Optional[str] = Field(description="Due date of the task")
    priority: Optional[str] = Field(description="Priority of the task")
    completed: bool = Field(description="Whether the task has been completed", default=False)

class CreateTask(TaskBase):
    pass

class TaskOut(TaskBase):
    id: str = Field(description="Unique identifier for the task")
class TaskList(BaseModel):
    subject: Optional[str] = Field(description="Subject of the task list")
    id: Optional[List[str]] = Field(description="List of task ids")
    start_date: Optional[str] = Field(description="Start date of the task list")
    end_date: Optional[str] = Field(description="End date of the task list")

class TaskDelete(BaseModel):
    subject: str = Field(description="Subject of the task to delete")
    message: str = Field(description="Message confirming the task has been deleted")

class TaskUpdate(BaseModel):
    id: Optional[str] = Field(description="ID of the task to update")
    subject: Optional[str] = Field(description="Subject of the task to update")
    title: str = Field(description="New title of the task", default=None)
    description: Optional[str] = Field(description="New description of the task", default=None)
    due_date: Optional[str] = Field(description="New due date of the task", default=None)
    priority: Optional[str] = Field(description="New priority of the task", default=None)
    completed: Optional[bool] = Field(description="Whether the task has been completed", default=None)
