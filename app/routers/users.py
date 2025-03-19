# app/routers/tasks.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Example data model for tasks
class Task(BaseModel):
    id: int
    title: str
    description: str = ""
    status: str = "todo"

# We'll store tasks in memory for demo (not for production!)
fake_db = {}

@router.post("/", response_model=Task)
async def create_task(task: Task):
    if task.id in fake_db:
        raise HTTPException(status_code=400, detail="Task ID already exists")
    fake_db[task.id] = task
    return task

@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: int):
    task = fake_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
