# app/services/tools/task_adapters.py
"""
Adapter functions that maintain the original task tool interface
but implement functionality using the SQL database.
"""

import logging
from typing import List, Optional
from datetime import datetime
import uuid  # Import uuid
from app.services.tools.sql_task_tools import (
    create_sql_task, get_sql_task, list_sql_tasks,
    update_sql_task, delete_sql_task, search_sql_tasks_by_subject,
    list_sql_tasks_by_date_range, list_tasks_by_goal
)
from app.models.task_models import CreateTask, TaskOut, TaskUpdate, TaskDelete
from app.models.sql_task_models import TaskCreateSQL, TaskOutSQL, TaskUpdateSQL, TaskDeleteSQL
from app.services.tools.goal_tools import search_goals_by_subject, get_goal  # Import search_goals_by_subject and get_goal
from fastapi import HTTPException # Import HTTPException

logger = logging.getLogger(__name__)

# Conversion functions
def convert_to_sql_create(task: CreateTask) -> TaskCreateSQL:
    """Convert vector-based CreateTask to SQL-based TaskCreateSQL"""
    due_date = None
    if hasattr(task, 'due_date') and task.due_date:
        if isinstance(task.due_date, datetime):
            due_date = task.due_date
        elif isinstance(task.due_date, str):
            try:
                due_date = datetime.fromisoformat(task.due_date)
            except ValueError:
                logger.warning(f"Could not parse due_date string: {task.due_date}, using None")
    
    goal_id_to_use = None
    # If goal_id is provided directly (and is a valid UUID string), use it
    if hasattr(task, 'goal_id') and task.goal_id:
        try:
            goal_id_to_use = uuid.UUID(task.goal_id)
            logger.info(f"Using provided goal_id: {goal_id_to_use}")
        except ValueError:
            logger.warning(f"Provided goal_id '{task.goal_id}' is not a valid UUID. Will attempt lookup by title if provided.")
    
    # If goal_id wasn't provided or was invalid, AND goal_title is provided, look up by title
    if goal_id_to_use is None and hasattr(task, 'goal_title') and task.goal_title:
        logger.info(f"Attempting to find goal by title for create: {task.goal_title}")
        try:
            # Use search_goals_by_subject for partial matching
            found_goals = search_goals_by_subject(task.goal_title, limit=1) 
            if found_goals:
                goal_id_to_use = found_goals[0].id # Use the ID of the first match
                logger.info(f"Found goal ID '{goal_id_to_use}' by title '{task.goal_title}' (using first match: '{found_goals[0].title}')")
                if len(found_goals) > 1:
                     logger.warning(f"Multiple goals found matching title '{task.goal_title}'. Used the first one found.")
            else:
                 logger.warning(f"Goal with title like '{task.goal_title}' not found.")
        except HTTPException as e:
            logger.error(f"Error searching goal by title '{task.goal_title}': {e.detail}")
        except Exception as e:
            logger.error(f"Unexpected error searching goal by title '{task.goal_title}': {str(e)}")

    return TaskCreateSQL(
        title=task.title,
        description=task.description,
        completed=task.completed,
        due_date=due_date,
        priority=task.priority if hasattr(task, 'priority') else None,
        goal_id=goal_id_to_use
    )

def convert_to_task_out(sql_task: TaskOutSQL) -> TaskOut:
    """Convert SQL-based TaskOutSQL to vector-based TaskOut"""
    due_date_str = sql_task.due_date.isoformat() if sql_task.due_date else None
    goal_id_str = str(sql_task.goal_id) if sql_task.goal_id else None
    
    return TaskOut(
        id=str(sql_task.id),
        title=sql_task.title,
        description=sql_task.description,
        completed=sql_task.completed,
        due_date=due_date_str,
        priority=sql_task.priority,
        goal_id=goal_id_str
    )

def convert_to_sql_update(task: TaskUpdate) -> TaskUpdateSQL:
    """Convert vector-based TaskUpdate to SQL-based TaskUpdateSQL"""
    due_date = None
    if hasattr(task, 'due_date') and task.due_date:
        if isinstance(task.due_date, datetime):
            due_date = task.due_date
        elif isinstance(task.due_date, str):
            try:
                due_date = datetime.fromisoformat(task.due_date)
            except ValueError:
                logger.warning(f"Could not parse due_date string: {task.due_date}, using None")

    # Determine the goal ID to use
    goal_id_to_use = None # Default to None
    goal_lookup_attempted = False

    # 1. Check for explicit goal_id (UUID string or None/empty)
    if hasattr(task, 'goal_id'):
        goal_lookup_attempted = True # Mark that goal handling was intended
        if task.goal_id:
            try:
                goal_id_to_use = uuid.UUID(task.goal_id)
                logger.info(f"Using provided goal_id for update: {goal_id_to_use}")
            except ValueError:
                logger.warning(f"Provided goal_id '{task.goal_id}' for update is not a valid UUID. Will attempt lookup by title if provided.")
                goal_lookup_attempted = False # Reset flag to allow title lookup
        else:
             # Explicitly removing goal association
             goal_id_to_use = None 
             logger.info("Explicitly removing goal association (goal_id is None or empty).")

    # 2. If explicit goal_id wasn't valid or provided, check for goal_title
    if not goal_lookup_attempted and hasattr(task, 'goal_title') and task.goal_title:
        goal_lookup_attempted = True # Mark that goal handling was intended
        logger.info(f"Attempting to find goal by title for update: {task.goal_title}")
        try:
            found_goals = search_goals_by_subject(task.goal_title, limit=1)
            if found_goals:
                goal_id_to_use = found_goals[0].id
                logger.info(f"Found goal ID '{goal_id_to_use}' by title '{task.goal_title}' (using first match: '{found_goals[0].title}')")
                if len(found_goals) > 1:
                     logger.warning(f"Multiple goals found matching title '{task.goal_title}'. Used the first one found.")
            else:
                 logger.warning(f"Goal with title like '{task.goal_title}' not found for update.")
                 goal_id_to_use = None # Ensure it's None if lookup failed
        except HTTPException as e:
            logger.error(f"Error searching goal by title '{task.goal_title}' for update: {e.detail}")
            goal_id_to_use = None # Ensure it's None on error
        except Exception as e:
             logger.error(f"Unexpected error searching goal by title '{task.goal_title}' for update: {str(e)}")
             goal_id_to_use = None # Ensure it's None on error

    # Construct the payload, always including goal_id if goal handling was intended
    update_payload = {
        "id": task.id if hasattr(task, 'id') else None,
        "title": task.title if hasattr(task, 'title') else None,
        "description": task.description if hasattr(task, 'description') else None,
        "completed": task.completed if hasattr(task, 'completed') else None,
        "due_date": due_date,
        "priority": task.priority if hasattr(task, 'priority') else None,
        "subject": task.subject if hasattr(task, 'subject') else None,
    }

    # Only include goal_id in the update payload if the user intended to modify it
    # (i.e., provided goal_id or goal_title)
    if goal_lookup_attempted:
        update_payload["goal_id"] = goal_id_to_use

    # Validate and return TaskUpdateSQL
    try:
        # Use .model_validate to handle potential extra fields gracefully if needed,
        # although TaskUpdateSQL should match the keys we construct.
        sql_update_obj = TaskUpdateSQL.model_validate(update_payload) 
        logger.info(f"Successfully created TaskUpdateSQL object: {sql_update_obj}")
        return sql_update_obj
    except Exception as e:
        # Log the payload that caused the error
        logger.error(f"Pydantic validation failed for TaskUpdateSQL with payload: {update_payload}")
        logger.error(f"Validation error details: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error creating update payload: {e}")

# Adapter functions with original names
def create_task(task: CreateTask) -> TaskOut:
    """Create a task using SQL database"""
    logger.info(f"Creating SQL task: {task.title}")
    # Conversion logic now happens inside convert_to_sql_create
    sql_create_data = convert_to_sql_create(task)
    sql_task = create_sql_task(sql_create_data)
    return convert_to_task_out(sql_task)

def get_task_service(task_id: str) -> TaskOut:
    """Get a task by ID using SQL database"""
    logger.info(f"Getting SQL task: {task_id}")
    sql_task = get_sql_task(task_id)
    return convert_to_task_out(sql_task)

def update_task(task: TaskUpdate) -> TaskOut:
    """Update a task using SQL database"""
    # We need the task ID to perform the update. The adapter needs the specific task ID.
    # The Agent logic should ideally find the task ID first using the subject.
    # Let's assume for now the agent provides the task.id correctly in the TaskUpdate object.
    if not hasattr(task, 'id') or not task.id:
         # If ID is missing, try to find it using the subject
         if hasattr(task, 'subject') and task.subject:
             logger.info(f"Task ID missing, searching by subject: {task.subject}")
             found_tasks = search_sql_tasks_by_subject(task.subject, limit=1)
             if found_tasks:
                 task.id = str(found_tasks[0].id)
                 logger.info(f"Found task ID by subject: {task.id}")
             else:
                 raise HTTPException(status_code=404, detail=f"Task with subject '{task.subject}' not found for update.")
         else:
             raise HTTPException(status_code=400, detail="Task ID or subject must be provided for update.")
             
    logger.info(f"Updating SQL task ID: {task.id}")
    # Conversion logic now happens inside convert_to_sql_update
    sql_update_data = convert_to_sql_update(task)
    # The update_sql_task function only updates fields present in sql_update_data
    sql_task = update_sql_task(sql_update_data)
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

def list_tasks_by_goal_id(goal_id: str) -> List[TaskOut]:
    """List tasks associated with a specific goal"""
    logger.info(f"Listing tasks for goal: {goal_id}")
    sql_tasks = list_tasks_by_goal(goal_id)
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