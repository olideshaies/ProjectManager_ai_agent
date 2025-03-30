# tasks.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import pandas as pd
from app.database.vector_store import VectorStore
from app.scripts.insert_vectors import insert_vectors
from timescale_vector import client
from app.models.task_models import CreateTask, TaskOut, TaskDelete, TaskUpdate
from app.services.tools.task_tools import create_task, get_task_service, search_tasks_by_subject, list_tasks_by_date_range, delete_task, update_task
import logging
router = APIRouter()
vec = VectorStore()
logger = logging.getLogger(__name__)
    
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

@router.post("/", response_model=TaskOut)
def create_task(task: CreateTask):
    try:
        created_task = create_task(task)
        return created_task
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

@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str):
    try:
        task = get_task_service(task_id)
        return task
    except Exception as e:
        raise HTTPException(status_code=404, detail="Task not found.")
    
@router.delete("/{subject}", response_model=List[TaskOut])
def delete_task(subject: str):
    try:
        delete_task(subject)
        return {"message": f"Task {subject} deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/server-time")
def check_server_time():
    return {
        "utc_now": datetime.now(timezone.utc),
        "system_time": datetime.now(),
        "iso_format": datetime.now().isoformat()
    }

@router.patch("/{task_id}", response_model=TaskOut)
def update_task_endpoint(task_id: str, update_data: TaskUpdate):
    """
    Update a task by ID. Only the fields that are provided will be updated.
    """
    try:
        # Ensure the task_id from the path is used
        update_data.id = task_id
        
        updated_task = update_task(update_data)
        return updated_task
    except HTTPException as he:
        # Re-raise HTTP exceptions as-is
        raise he
    except Exception as e:
        # Log the error and convert other exceptions to 500
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")