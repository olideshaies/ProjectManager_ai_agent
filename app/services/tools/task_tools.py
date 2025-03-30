# app/services/tools/task_tools.py
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from openai import OpenAI
from app.models.task_models import CreateTask, TaskOut, TaskDelete, TaskUpdate
from app.database.vector_store import VectorStore
from timescale_vector import client as timescale_client
from fastapi import HTTPException
import uuid
import pandas as pd


vec = VectorStore()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o"

def safe_value(value, default=None):
    """Safely convert pandas NaN to None or other appropriate default value"""
    return default if pd.isna(value) else value

# TODO: Improve the structure of this function
def create_task(task: CreateTask) -> TaskOut:
    """
    Creates a new task and inserts it into the same vector store 
    with a category='task' so it can be vector-searched.
    Uses time_context if provided to enhance the task creation.
    """
    if not task.due_date:
        # Use time context if available
        time_ctx = getattr(task, 'time_context', None)
        if time_ctx and time_ctx.get('datetime'):
            task.due_date = time_ctx['datetime'].isoformat()
        else:
            # Default to 3 days from now if no time specified
            default_due = datetime.now(timezone.utc) + timedelta(days=3)
            task.due_date = default_due.isoformat()
    
    due_date = None
    priority = None
    # 1. Construct 'contents' for embedding
    contents = f"Task Title: {task.title}\nDescription: {task.description}"
    if task.due_date:
        # Parse the string into a datetime object
        due_date = datetime.fromisoformat(task.due_date)
        contents += f"\nDue date: {due_date.isoformat()}"
    if task.priority:
        priority = task.priority
        contents += f"\nPriority: {priority}"
    # 2. Generate embedding
    embedding = vec.get_embedding(contents)

    # 3. Prepare the record
    record = {
        "id": str(uuid.uuid1()),  # or use your uuid_from_time if you prefer
        "metadata": {
            "category": "task",
            "created_at": datetime.now().isoformat(),
            "due_date": due_date.isoformat() if due_date else None,
            "completed": task.completed,  # Add completed status to metadata
            "priority": priority,  # Add priority to metadata
        },
        "contents": contents,
        "embedding": embedding,
    }

    # 4. Upsert into Timescale
    df = pd.DataFrame([record])
    vec.upsert(df)  # Using upsert directly instead of insert_vectors

    return TaskOut(
        id=record["id"],
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        priority=priority,
        completed=task.completed  # Use the actual completed status from the task
    )
def search_tasks_by_subject( subject: str, limit: int = 10) -> List[TaskOut]:
    """
    Searches for tasks where the task title in the 'contents' matches the subject.
    The query is performed on the vector embedding of the subject,
    along with a predicate to filter for records with metadata 'category' equal to 'task'.
    """
    # Create a predicate to filter only task records
    predicates = timescale_client.Predicates("category", "==", "task")
    
    # Use the subject as the query text (ensure it's non-empty)
    query_text = subject if subject.strip() else " "
    
    results = vec.search(query_text, limit=limit, predicates=predicates)
    
    if results.empty:
        return []
        
    tasks = []
    # Iterate through DataFrame rows
    for _, row in results.iterrows():
        # Access content using DataFrame column access
        contents = row['content'] 
        lines = contents.split("\n")
        if len(lines) < 2:
            continue
            
        # Extract task information
        title = lines[0].replace("Task Title: ", "").strip()
        description = lines[1].replace("Description: ", "").strip()
        
        # Properly handle NaN values from the DataFrame
        due_date = safe_value(row.get('due_date'))
        
        # Check if priority is NaN and convert to None if it is
        priority = safe_value(row.get('priority'))
        
        # Handle 'completed' NaN by providing a default Boolean value
        # Use pd.isna to properly check for NaN values
        completed_val = row.get('completed')
        completed = safe_value(completed_val, False)
        
        tasks.append(TaskOut(
            id=str(row['id']),  # Changed from task_id to id
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            completed=completed
        ))
    
    return tasks
def list_reccent_tasks(limit: int = 10) -> List[TaskOut]:
    """
    Searches for tasks where the task are recent returning task for this current week.
    The query is performed on the vector embedding of the subject.
    along with a predicate to filter for records with metadata 'category' equal to 'task'.
    """
    # Create a predicate to filter only task records
    predicates = timescale_client.Predicates("category", "==", "task")
        # Get the current date
    current_date = datetime.now()
    # Get the start and end of the current week
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Create a predicate for tasks within the current week
    week_predicates = timescale_client.Predicates("created_at", ">=", start_of_week.isoformat())    
    combined_predicates = [ 
        predicates,
        week_predicates
    ]
    # Perform the vector search with the combined predicates
    results = vec.search(" ", limit=limit, predicates=combined_predicates)

    tasks = []   
    for record in results:
        contents = record.get("contents", "")
        lines = contents.split("\n")
        if len(lines) < 2:
            continue
        # Assume the stored format is:
        # Line 1: "Task Title: {title}"
        # Line 2: "Description: {description}"
        title = lines[0].replace("Task Title: ", "").strip()
        description = lines[1].replace("Description: ", "").strip()
        due_date = safe_value(record.get("metadata", {}).get("due_date"))
        completed = safe_value(record.get("metadata", {}).get("completed"), False)
        priority = safe_value(record.get("metadata", {}).get("priority"))
        tasks.append(TaskOut(
            id=record.get("id", "unknown"),
            title=title,
            description=description,
            due_date=due_date,
            completed=completed,
            priority=priority
        ))
    return tasks
    
def get_task_service(id: str) -> TaskOut:
    # Create a predicate to filter for the given id.
    predicates = timescale_client.Predicates("id", "==", id)
    
    # Use a non-empty query string (e.g., a single space) for the embedding API.
    results = vec.search(id, limit=1, predicates=predicates)
    
    if not results:
        raise Exception("Task not found.")
    
    record = results[0]
    contents = record.get("contents", "")
    lines = contents.split("\n")
    
    # Expected format: first line "Task Title: {title}", second line "Description: {description}"
    title = lines[0].replace("Task Title: ", "").strip() if lines else ""
    description = lines[1].replace("Description: ", "").strip() if len(lines) > 1 else ""
    due_date = safe_value(record.get("metadata", {}).get("due_date"))
    completed = safe_value(record.get("metadata", {}).get("completed"), False)
    priority = safe_value(record.get("metadata", {}).get("priority"))
    return TaskOut(
        id=id,
        title=title,
        description=description,
        due_date=due_date,
        completed=completed,
        priority=priority
    )
# TODO: Improve the structure of this function and make it work lol
def list_tasks_by_date_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Returns all tasks by filtering on metadata category 'task'.  
    Optionally, if start_date and end_date (ISO 8601 strings) are provided,
    only returns tasks whose metadata 'created_at' (or due_date) falls within the range.
    """
    # Filter by category 'task'
    predicates = timescale_client.Predicates("category", "==", "task")
    
    time_range = None
    # If both dates are provided, parse them into datetime objects
    if start_date and end_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            time_range = (start_dt, end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601.")
    logger.info(f"Searching for tasks between {start_date} and {end_date}")
    # Perform the vector search with the predicate and optional time_range
    results = vec.search(" ", limit=10, predicates=predicates, time_range=time_range)
    logger.info(f"Found {len(results)} tasks.")
    tasks = []
    #record is a df
    for index, row in results.iterrows():
        logger.info(f"Processing task: {row}")
        logger.info(f"Contents: {row['content']}")
        contents = row["content"]
        lines = contents.split("\n")
        if len(lines) < 2:
            continue  # Skip records that don't match expected formats
        title = lines[0].replace("Task Title: ", "").strip()
        description = lines[1].replace("Description: ", "").strip()
        # if third line exists, it is due_date
        if len(lines) >=3:
            due_date = lines[2].replace("Due date: ", "").strip()
            # if fourth line exists, it is completed
            if len(lines) >= 4:
                completed = lines[3].replace("Completed: ", "").strip()
            else:
                completed = False
            # if fifth line exists, it is priority
            if len(lines) >= 5:
                priority = lines[4].replace("Priority: ", "").strip()
            else:
                priority = None
        logger.info(f"Task: {title}, {description}, {due_date}")
        tasks.append(TaskOut(
            id=str(row['id']),  # Include the task ID
            title=title,
            description=description,
            due_date=due_date,
            completed=completed,
            priority=priority
        ))
    
    return tasks

def delete_task(subject: str) -> TaskDelete:
    """
    Deletes a task with the given subject.
    Returns a TaskDelete object confirming the deletion.
    """
    # Create a predicate to filter only task records
    predicates = timescale_client.Predicates("category", "==", "task")
    
    # Use the subject as the query text (ensure it's non-empty)
    query_text = subject if subject.strip() else " "
    
    # Get search results
    results = vec.search(query_text, limit=1, predicates=predicates)
    
    # Handle empty results
    if results.empty:
        raise HTTPException(status_code=404, detail="Task to delete not found.")
    
    # Get the first row from the DataFrame
    record = results.iloc[0]
    
    # Parse the contents
    contents = record['content']  # Using direct column access for DataFrame
    lines = contents.split("\n")
    
    if len(lines) < 2:
        raise HTTPException(status_code=500, detail="Invalid task format")
    
    # Get the task ID for deletion
    id = record['id']  # Using direct column access for DataFrame
    
    # Delete the task
    vec.delete([id])  # Pass id as a list

    return TaskDelete(
        subject=subject,
        message=f"Task '{subject}' deleted."
    )

def update_task(update_data: TaskUpdate) -> TaskOut:
    """
    For updating tasks:
    1. Extract the task title/subject from the query
    2. Determine which fields to update based on the request
    3. Set completed=true when the user wants to mark a task as done
    """
    logger.info(f"Updating task with ID: {update_data.id}")
    
    # Get the existing task
    results = vec.search(update_data.id, limit=1)
    if results.empty:
        logger.error(f"Task not found with ID: {update_data.id}")
        raise HTTPException(status_code=404, detail=f"Task not found with ID: {update_data.id}")
    
    # Extract current values
    record = results.iloc[0]
    print(f"Record: {record}")
    current_title = record['content'].split("\n")[0].replace("Task Title: ", "").strip()
    current_description = record['content'].split("\n")[1].replace("Description: ", "").strip()
    current_due_date = None if pd.isna(record['due_date']) else str(record['due_date'])
    current_completed = bool(record['completed'])
    print(f"Current completed: {current_completed}")
    current_priority = None if pd.isna(record['priority']) else str(record['priority'])
    current_created_at = str(record['created_at'])
    
    # Update only the fields that are provided
    new_title = update_data.title if update_data.title is not None else current_title
    new_description = update_data.description if update_data.description is not None else current_description
    new_due_date = update_data.due_date if update_data.due_date is not None else current_due_date
    new_completed = update_data.completed if update_data.completed is not None else current_completed
    print(f"New completed: {new_completed}")
    new_priority = update_data.priority if update_data.priority is not None else current_priority
    
    # Construct new contents
    new_contents = f"Task Title: {new_title}\nDescription: {new_description}"
    if new_due_date:
        new_contents += f"\nDue date: {new_due_date}"
    
    # Generate new embedding
    new_embedding = vec.get_embedding(new_contents)
    
    # Prepare the updated record
    updated_record = {
        "id": str(uuid.uuid1()),
        "metadata": {
            "category": "task",
            "created_at": current_created_at,
            "due_date": new_due_date,
            "completed": bool(new_completed),
            "priority": new_priority
        },
        "contents": new_contents,
        "embedding": new_embedding
    }
    print(f"Updated record: {updated_record}")
    # Update in vector store
    df = pd.DataFrame([updated_record])
    # DELETE TASK ID
    id = record['id']
    vec.delete([id])
    print(f"Deleted record: {id}")
    # UPSERT NEW RECORD
    vec.upsert(df)
    print(f"Upserted record: {id}")
    
    # Return updated task
    return TaskOut(
        id=update_data.id,
        title=new_title,
        description=new_description,
        due_date=new_due_date,
        completed=bool(new_completed),
        priority=new_priority
    )


    