# tasks.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database.session import SessionLocal
from app.models.sql_task_models import TaskDB, TaskCreateSQL, TaskOutSQL, TaskUpdateSQL

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=TaskOutSQL)
def create_task(task_data: TaskCreateSQL, db: Session = Depends(get_db)):
    """
    Create a new task in the 'tasks' table.
    """
    new_task = TaskDB(
        title=task_data.title,
        description=task_data.description,
        completed=task_data.completed,
        due_date=task_data.due_date,
        priority=task_data.priority
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.get("/", response_model=List[TaskOutSQL])
def list_tasks(db: Session = Depends(get_db)):
    """
    List all tasks.
    """
    tasks = db.query(TaskDB).all()
    return tasks

@router.get("/{task_id}", response_model=TaskOutSQL)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(TaskDB).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(TaskDB).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": f"Task {task_id} deleted."}

@router.patch("/{task_id}", response_model=TaskOutSQL)
def update_task(task_id: str, updates: TaskUpdateSQL, db: Session = Depends(get_db)):
    """
    Partial update: any field in TaskUpdateSQL can be used to update the existing record.
    """
    task = db.query(TaskDB).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if updates.title is not None:
        task.title = updates.title
    if updates.description is not None:
        task.description = updates.description
    if updates.completed is not None:
        task.completed = updates.completed
    if updates.due_date is not None:
        task.due_date = updates.due_date
    if updates.priority is not None:
        task.priority = updates.priority

    db.commit()
    db.refresh(task)
    return task