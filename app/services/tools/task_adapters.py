# app/services/tools/task_adapters.py
"""
Adapter functions that maintain the original task tool interface
but implement functionality using the SQL database.
"""

import logging
from typing import List, Optional
from datetime import datetime
from app.services.tools.sql_task_tools import (
    create_sql_task, get_sql_task, list_sql_tasks,
    update_sql_task, delete_sql_task, search_sql_tasks_by_subject,
    list_sql_tasks_by_date_range
)
from app.models.task_models import CreateTask, TaskOut, TaskUpdate, TaskDelete
from app.models.sql_task_models import TaskCreateSQL, TaskOutSQL, TaskUpdateSQL, TaskDeleteSQL

logger = logging.getLogger(__name__)

# Conversion functions
def convert_to_sql_create(task: CreateTask) -> TaskCreateSQL:
    """Convert vector-based CreateTask to SQL-based TaskCreateSQL"""
    # Convert string due_date to datetime if it exists
    due_date = None
    if hasattr(task, 'due_date') and task.due_date:
        # If due_date is already a datetime, use it directly
        if isinstance(task.due_date, datetime):
            due_date = task.due_date
        # If it's a string, parse it
        elif isinstance(task.due_date, str):
            try:
                due_date = datetime.fromisoformat(task.due_date)
            except ValueError:
                logger.warning(f"Could not parse due_date string: {task.due_date}, using None")
    
    return TaskCreateSQL(
        title=task.title,
        description=task.description,
        completed=task.completed,
        due_date=due_date,
        priority=task.priority if hasattr(task, 'priority') else None
    )

def convert_to_task_out(sql_task: TaskOutSQL) -> TaskOut:
    """Convert SQL-based TaskOutSQL to vector-based TaskOut"""
    # Convert datetime to ISO format string if it exists
    due_date_str = sql_task.due_date.isoformat() if sql_task.due_date else None
    
    return TaskOut(
        id=str(sql_task.id),
        title=sql_task.title,
        description=sql_task.description,
        completed=sql_task.completed,
        due_date=due_date_str,  # Now as string
        priority=sql_task.priority
    )

def convert_to_sql_update(task: TaskUpdate) -> TaskUpdateSQL:
    """Convert vector-based TaskUpdate to SQL-based TaskUpdateSQL"""
    # Convert string due_date to datetime if it exists
    due_date = None
    if hasattr(task, 'due_date') and task.due_date:
        # If due_date is already a datetime, use it directly
        if isinstance(task.due_date, datetime):
            due_date = task.due_date
        # If it's a string, parse it
        elif isinstance(task.due_date, str):
            try:
                due_date = datetime.fromisoformat(task.due_date)
            except ValueError:
                logger.warning(f"Could not parse due_date string: {task.due_date}, using None")
    
    return TaskUpdateSQL(
        id=task.id if hasattr(task, 'id') else None,
        title=task.title if hasattr(task, 'title') else None,
        description=task.description if hasattr(task, 'description') else None,
        completed=task.completed if hasattr(task, 'completed') else None,
        due_date=due_date,
        priority=task.priority if hasattr(task, 'priority') else None,
        subject=task.subject if hasattr(task, 'subject') else None
    )

# Adapter functions with original names
def create_task(task: CreateTask) -> TaskOut:
    """Create a task using SQL database"""
    logger.info(f"Creating SQL task: {task.title}")
    sql_task = create_sql_task(convert_to_sql_create(task))
    return convert_to_task_out(sql_task)

def get_task_service(task_id: str) -> TaskOut:
    """Get a task by ID using SQL database"""
    logger.info(f"Getting SQL task: {task_id}")
    sql_task = get_sql_task(task_id)
    return convert_to_task_out(sql_task)

def update_task(task: TaskUpdate) -> TaskOut:
    """Update a task using SQL database"""
    logger.info(f"Updating SQL task: {task.id}")
    sql_task = update_sql_task(convert_to_sql_update(task))
    return convert_to_task_out(sql_task)

def search_tasks_by_subject(subject: str, limit: int = 10) -> List[TaskOut]:
    """Search tasks by subject using SQL database"""
    logger.info(f"Searching SQL tasks by subject: {subject}")
    sql_tasks = search_sql_tasks_by_subject(subject, limit)
    return [convert_to_task_out(t) for t in sql_tasks]

def list_tasks_by_date_range(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[TaskOut]:
    """List tasks by date range using SQL database"""
    # Convert string dates to datetime objects if needed
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    logger.info(f"Listing SQL tasks by date range: {start_date} to {end_date}")
    sql_tasks = list_sql_tasks_by_date_range(start, end)
    return [convert_to_task_out(t) for t in sql_tasks]

def delete_task(subject: str) -> TaskDelete:
    """Delete a task by subject using SQL database"""
    logger.info(f"Deleting SQL task by subject: {subject}")
    try:
        # First find the task by subject
        tasks = search_sql_tasks_by_subject(subject, limit=1)
        if not tasks:
            logger.warning(f"No task found matching '{subject}'")
            raise ValueError(f"No task found matching '{subject}'")
        
        # Delete using both ID and subject
        task_id = str(tasks[0].id)
        result = delete_sql_task(task_id, subject=subject)
        
        # Convert to vector-style TaskDelete response
        return TaskDelete(
            subject=subject,
            message=result.message
        )
    except Exception as e:
        logger.error(f"Error in delete_task adapter: {str(e)}")
        raise

def list_reccent_tasks(limit: int = 10) -> List[TaskOut]:
    """List recent tasks using SQL database"""
    logger.info(f"Listing recent SQL tasks")
    # For SQL, we'll just list tasks ordered by creation date
    tasks = list_sql_tasks()
    # Sort by created_at descending
    sorted_tasks = sorted(tasks, key=lambda t: t.created_at or datetime.min, reverse=True)
    # Limit to requested count
    recent_tasks = sorted_tasks[:limit]
    return [convert_to_task_out(t) for t in recent_tasks] 