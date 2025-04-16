# tasks.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database.session import SessionLocal
from app.models.sql_task_models import TaskDB, TaskCreateSQL, TaskOutSQL, TaskUpdateSQL
import uuid

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
        priority=task_data.priority,
        goal_id=task_data.goal_id
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

@router.get("/goal/{goal_id}", response_model=List[TaskOutSQL])
def list_tasks_by_goal(goal_id: str, db: Session = Depends(get_db)):
    """
    List all tasks associated with a specific goal.
    """
    try:
        goal_uuid = uuid.UUID(goal_id)
        tasks = db.query(TaskDB).filter(TaskDB.goal_id == goal_uuid).all()
        return tasks
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid goal ID format")

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
    if updates.goal_id is not None:
        task.goal_id = updates.goal_id

    db.commit()
    db.refresh(task)
    return task

@router.patch("/{task_id}/assign-goal/{goal_id}", response_model=TaskOutSQL)
def assign_task_to_goal(task_id: str, goal_id: str, db: Session = Depends(get_db)):
    """
    Assign a task to a specific goal.
    """
    try:
        task = db.query(TaskDB).get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        # Check if the goal exists
        from app.models.goal_models import GoalDB
        goal_uuid = uuid.UUID(goal_id)
        goal = db.query(GoalDB).filter(GoalDB.id == goal_uuid).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
            
        task.goal_id = goal_uuid
        db.commit()
        db.refresh(task)
        return task
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

@router.patch("/{task_id}/remove-goal", response_model=TaskOutSQL)
def remove_task_from_goal(task_id: str, db: Session = Depends(get_db)):
    """
    Remove a task from its associated goal.
    """
    task = db.query(TaskDB).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task.goal_id = None
    db.commit()
    db.refresh(task)
    return task