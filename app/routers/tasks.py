# tasks.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
import pandas as pd
from app.database.vector_store import VectorStore
from app.scripts.insert_vectors import insert_vectors
from timescale_vector import client
from app.models.task_models import CreateTask, TaskOut
from app.services.task_service import create_task, get_task_service, search_tasks_by_subject, list_tasks_by_date_range

router = APIRouter()
vec = VectorStore()


@router.post("/", response_model=TaskOut)
def create_task(task: CreateTask):
    try:
        created_task = create_task(task)
        return created_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str):
    try:
        task = get_task_service(task_id)
        return task
    except Exception as e:
        raise HTTPException(status_code=404, detail="Task not found.")
    
@router.get("/search", response_model=List[TaskOut])
def search_tasks(subject: str):
    """
    Searches for tasks whose title (embedded in the contents) matches the given subject.
    """
    try:
        tasks = search_tasks_by_subject(subject)
        if not tasks:
            raise HTTPException(status_code=404, detail="No tasks found matching the subject.")
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[TaskOut])
def list_tasks(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Returns all tasks by filtering on date range.  
    """
    # Filter by category 'task'
    try:
        tasks = list_tasks_by_date_range(start_date, end_date)
        if not tasks:
            raise HTTPException(status_code=404, detail="No tasks found matching the date range.")
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
