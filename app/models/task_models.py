from typing import Optional, List
from pydantic import BaseModel, Field

#Example
# class EventExtraction(BaseModel):
#     description: str = Field(description="Raw description of the event")
#     is_calendar_event: bool = Field(description="Whether this text describes a calendar event")
#     confidence_score: float = Field(description="Confidence score between 0 and 1")

class TaskBase(BaseModel):
    title: str = Field(description="Title of the task")
    description: str = Field(description="Description of the task")
    due_date: Optional[str] = Field(description="Due date of the task")
    completed: bool = Field(description="Whether the task has been completed")

class CreateTask(TaskBase   ):
    pass

class TaskOut(TaskBase):
    pass

class TaskList(BaseModel):
    tasks: List[TaskOut]
    total: int = Field(description="Total number of tasks")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(description="Title of the task")
    description: Optional[str] = Field(description="Description of the task")
    due_date: Optional[str] = Field(description="Due date of the task")
    completed: Optional[bool] = Field(description="Whether the task has been completed")

class TaskDelete(BaseModel):
    message: str = Field(description="Message confirming the task has been deleted")
