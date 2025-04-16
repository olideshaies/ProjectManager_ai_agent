import logging
from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.models.sql_task_models import TaskDB, TaskCreateSQL, TaskOutSQL, TaskUpdateSQL, TaskDeleteSQL
from app.database.session import SessionLocal
from app.services.tools.goal_tools import get_goal
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def get_db():
    """Get a database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def create_sql_task(task_data: TaskCreateSQL) -> TaskOutSQL:
    """
    Creates a new task in the database
    """
    db = get_db()
    try:
        # Check if a goal title is provided
        if task_data.goal_title:
            # Retrieve the goal by title
            goal = get_goal(task_data.goal_title)
            if goal:
                task_data.goal_id = goal.id
            else:
                raise ValueError(f"Goal with title '{task_data.goal_title}' not found")
        # Create new task object
        new_task = TaskDB(
            title=task_data.title,
            description=task_data.description,
            completed=task_data.completed,
            due_date=task_data.due_date,
            priority=task_data.priority,
            goal_id=task_data.goal_id
        )
        
        # Add to database and commit
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        # Return as TaskOutSQL model
        return TaskOutSQL(
            id=new_task.id,
            title=new_task.title,
            description=new_task.description,
            completed=new_task.completed,
            due_date=new_task.due_date,
            priority=new_task.priority,
            goal_id=new_task.goal_id,
            created_at=new_task.created_at,
            updated_at=new_task.updated_at
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")
    finally:
        db.close()

def get_sql_task(task_id: str) -> TaskOutSQL:
    """
    Retrieves a task by ID
    """
    db = get_db()
    try:
        # Convert string ID to UUID if necessary
        if isinstance(task_id, str):
            task_id = uuid.UUID(task_id)
            
        task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
            
        return TaskOutSQL(
            id=task.id,
            title=task.title,
            description=task.description,
            completed=task.completed,
            due_date=task.due_date,
            priority=task.priority,
            goal_id=task.goal_id,
            created_at=task.created_at,
            updated_at=task.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task: {str(e)}")
    finally:
        db.close()

def list_sql_tasks() -> List[TaskOutSQL]:
    """
    Lists all tasks
    """
    db = get_db()
    try:
        tasks = db.query(TaskDB).all()
        return [
            TaskOutSQL(
                id=task.id,
                title=task.title,
                description=task.description,
                completed=task.completed,
                due_date=task.due_date,
                priority=task.priority,
                goal_id=task.goal_id,
                created_at=task.created_at,
                updated_at=task.updated_at
            ) for task in tasks
        ]
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")
    finally:
        db.close()

def list_tasks_by_goal(goal_id: str) -> List[TaskOutSQL]:
    """
    Lists all tasks associated with a specific goal
    """
    db = get_db()
    try:
        # Convert string ID to UUID if necessary
        if isinstance(goal_id, str):
            goal_id = uuid.UUID(goal_id)
            
        tasks = db.query(TaskDB).filter(TaskDB.goal_id == goal_id).all()
        return [
            TaskOutSQL(
                id=task.id,
                title=task.title,
                description=task.description,
                completed=task.completed,
                due_date=task.due_date,
                priority=task.priority,
                goal_id=task.goal_id,
                created_at=task.created_at,
                updated_at=task.updated_at
            ) for task in tasks
        ]
    except Exception as e:
        logger.error(f"Error listing tasks by goal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks by goal: {str(e)}")
    finally:
        db.close()

def update_sql_task(task_data: TaskUpdateSQL) -> TaskOutSQL:
    """
    Updates a task based on provided data
    The task_data object should have an id and any fields to update
    """
    db = get_db()
    try:
        # Convert string ID to UUID if necessary
        if isinstance(task_data.id, str):
            task_id = uuid.UUID(task_data.id)
        else:
            task_id = task_data.id
            
        task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
        # Check if a goal title is provided
        if task.goal_title:
            # Retrieve the goal by title
            goal = get_goal(task.goal_title)
            if goal:
                task.goal_id = goal.id
            else:
                raise ValueError(f"Goal with title '{task.goal_title}' not found")
        # Update fields if provided in the input
        if hasattr(task_data, 'title') and task_data.title is not None:
            task.title = task_data.title
        if hasattr(task_data, 'description') and task_data.description is not None:
            task.description = task_data.description
        if hasattr(task_data, 'completed') and task_data.completed is not None:
            task.completed = task_data.completed
        if hasattr(task_data, 'due_date') and task_data.due_date is not None:
            task.due_date = task_data.due_date
        if hasattr(task_data, 'priority') and task_data.priority is not None:
            task.priority = task_data.priority
        if hasattr(task_data, 'goal_id') and task_data.goal_id is not None:
            task.goal_id = task_data.goal_id
            
        db.commit()
        db.refresh(task)
        
        return TaskOutSQL(
            id=task.id,
            title=task.title,
            description=task.description,
            completed=task.completed,
            due_date=task.due_date,
            priority=task.priority,
            goal_id=task.goal_id,
            created_at=task.created_at,
            updated_at=task.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")
    finally:
        db.close()

def delete_sql_task(task_id: str, subject: Optional[str] = None) -> TaskDeleteSQL:
    """
    Deletes a task by ID
    Returns a confirmation message
    """
    db = get_db()
    try:
        # Convert string ID to UUID if necessary
        if isinstance(task_id, str):
            task_id = uuid.UUID(task_id)
            
        task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
            
        task_title = task.title
        db.delete(task)
        db.commit()
        
        return TaskDeleteSQL(
            id=task_id,
            subject=subject or task_title,  # Use provided subject or fall back to title
            message=f"Task '{task_title}' deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")
    finally:
        db.close()

def search_sql_tasks_by_subject(subject: str, limit: int = 10) -> List[TaskOutSQL]:
    """
    Searches for tasks where the title contains the subject string
    """
    db = get_db()
    try:
        tasks = db.query(TaskDB).filter(TaskDB.title.ilike(f"%{subject}%")).limit(limit).all()
        
        return [
            TaskOutSQL(
                id=task.id,
                title=task.title,
                description=task.description,
                completed=task.completed,
                due_date=task.due_date,
                priority=task.priority,
                goal_id=task.goal_id,
                created_at=task.created_at,
                updated_at=task.updated_at
            ) for task in tasks
        ]
    except Exception as e:
        logger.error(f"Error searching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search tasks: {str(e)}")
    finally:
        db.close()

def list_sql_tasks_by_date_range(start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[TaskOutSQL]:
    """
    Lists tasks with due dates in the specified range
    """
    db = get_db()
    try:
        query = db.query(TaskDB)
        
        if start_date:
            query = query.filter(TaskDB.due_date >= start_date)
        if end_date:
            query = query.filter(TaskDB.due_date <= end_date)
            
        tasks = query.all()
        return [
            TaskOutSQL(
                id=task.id,
                title=task.title,
                description=task.description,
                completed=task.completed,
                due_date=task.due_date,
                priority=task.priority,
                goal_id=task.goal_id,
                created_at=task.created_at,
                updated_at=task.updated_at
            ) for task in tasks
        ]
    except Exception as e:
        logger.error(f"Error listing tasks by date range: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks by date range: {str(e)}")
    finally:
        db.close() 