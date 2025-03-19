import os
import logging
from datetime import datetime
from typing import Optional, List
from openai import OpenAI
from app.models.task_models import CreateTask, TaskOut
from app.database.vector_store import VectorStore
from app.scripts.insert_vectors import insert_vectors
from timescale_vector import client as timescale_client
from fastapi import HTTPException
import uuid
import pandas as pd
import json
vec = VectorStore()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o"

# TODO: Improve the structure of this function
def create_task(task: CreateTask) -> TaskOut:
    """
    Creates a new task and inserts it into the same vector store 
    with a category='task' so it can be vector-searched.
    """
    # 1. Construct 'contents' for embedding
    contents = f"Task Title: {task.title}\nDescription: {task.description}"
    if task.due_date:
        # Parse the string into a datetime object
        due_date = datetime.fromisoformat(task.due_date)
        contents += f"\nDue date: {due_date.isoformat()}"

    # 2. Generate embedding
    embedding = vec.get_embedding(contents)

    # 3. Prepare the record
    record = {
        "id": str(uuid.uuid1()),  # or use your uuid_from_time if you prefer
        "metadata": {
            "category": "task",
            "created_at": datetime.now().isoformat(),
            "due_date": due_date.isoformat() if due_date else None,
        },
        "contents": contents,
        "embedding": embedding,
    }

    # 4. Upsert into Timescale
    df = pd.DataFrame([record])
    insert_vectors(df)

    return TaskOut(
        id=record["id"],
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        completed=False
    )
def search_tasks_by_subject(subject: str) -> List[TaskOut]:
    """
    Searches for tasks where the task title in the 'contents' matches the subject.
    The query is performed on the vector embedding of the subject,
    along with a predicate to filter for records with metadata 'category' equal to 'task'.
    """
    # Create a predicate to filter only task records
    predicates = timescale_client.Predicates("category", "==", "task")
    
    # Use the subject as the query text (ensure it's non-empty)
    query_text = subject if subject.strip() else " "
    
    results = vec.search(query_text, limit=10, predicates=predicates)
    
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
        due_date = record.get("metadata", {}).get("due_date")
        tasks.append(TaskOut(
            id=record.get("id", "unknown"),
            title=title,
            description=description,
            due_date=due_date,
            completed=False
        ))
    return tasks

def get_task_service(task_id: str) -> TaskOut:
    # Create a predicate to filter for the given task_id.
    predicates = timescale_client.Predicates("id", "==", task_id)
    
    # Use a non-empty query string (e.g., a single space) for the embedding API.
    results = vec.search(task_id, limit=1, predicates=predicates)
    
    if not results:
        raise Exception("Task not found.")
    
    record = results[0]
    contents = record.get("contents", "")
    lines = contents.split("\n")
    
    # Expected format: first line "Task Title: {title}", second line "Description: {description}"
    title = lines[0].replace("Task Title: ", "").strip() if lines else ""
    description = lines[1].replace("Description: ", "").strip() if len(lines) > 1 else ""
    due_date = record.get("metadata", {}).get("due_date")
    
    return TaskOut(
        id=task_id,
        title=title,
        description=description,
        due_date=due_date,
        completed=False
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
        else:
            due_date = None
        logger.info(f"Task: {title}, {description}, {due_date}")
        tasks.append(TaskOut(
            title=title,
            description=description,
            due_date=due_date,
            completed=False
        ))
    
    return tasks
