# app/services/agent.py
import json
from pydantic import ValidationError
from app.models.agent_decision import AgentDecision
from app.services.llm_factory import LLMFactory
from app.config.settings import get_settings
from app.services.tools.task_tools import create_task, search_tasks_by_subject, get_task_service, update_task, list_tasks_by_date_range, delete_task, list_reccent_tasks
from app.services.time_utils import TimeParser
import logging

def parse_agent_decision(user_query: str) -> AgentDecision:
    """
    Uses a zero-shot approach: instructs the LLM to produce JSON matching the AgentDecision schema.
    We assume that our LLM client automatically parses the output into an AgentDecision instance.
    """
    
    provider = "openai"  # or "anthropic", "llama", etc.
    factory = LLMFactory(provider=provider)
    
    time_context = TimeParser.extract_time_context(user_query)
    system_prompt = f"""
    You are an AI that decides which tool to call for a user's request.
    Current time context: {time_context.get('formatted_date', 'not specified')}
    
    TOOL SELECTION GUIDELINES:
    - Use "create_task" for requests to create a new task
    - Use "search_tasks_by_subject" for queries about finding tasks without changing them
    - Use "update_task" for ANY request to change, modify, or update an existing task
    - Use "delete_task" for requests to remove a task
    - Use "list_tasks_by_date_range" for requests to see tasks within a time period
    - Use "get_task_service" only when a specific task ID is mentioned
    
    When creating tasks:
    1. Use explicit due dates from the query
    2. Fall back to parsed time context when no date is specified
    3. Set due_date to None only if no time references exist
    
    For updating tasks:
    1. ALWAYS use "update_task" when the user mentions updating, changing, modifying, or setting a property
    2. NEVER set "id" directly - use "subject" instead to specify which task to update 
    3. Extract the task title/subject from the query (the part before "set", "change", "update", etc.)
    4. Determine which specific fields to update based on the request
    5. Set completed=true when the user wants to mark a task as done
    
    Example update requests:
    - "Update Task Project X set priority to high" → update_task with {{ "subject": "Project X", "priority": "high" }}
    - "Change the due date of my homework task to Friday" → update_task with {{ "subject": "homework", "due_date": "(Friday's date)" }}
    - "Mark my dentist appointment as completed" → update_task with {{ "subject": "dentist appointment", "completed": true }}
    
    Return JSON with time_context included:
    {{
      "tool_name": "create_task" | "search_tasks_by_subject" | "get_task_service" | "list_tasks_by_date_range" | "delete_task" | "update_task",
      "tool_input": appropriate fields, no extra keys,
      "time_context": {time_context}
    }}
    Do not include any extra text or disclaimers.
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    
    # Call the LLM using our factory and let it parse the output using our Pydantic model.
    completion = factory.create_completion(
        response_model=AgentDecision,
        messages=messages
    )
    
    # If completion is already an AgentDecision, return it.
    if isinstance(completion, AgentDecision):
        completion.time_context = time_context
        return completion
    
    # Fallback: If not, assume we received raw text and parse manually.
    try:
        text_output = completion.choices[0].message.content.strip()
        data = json.loads(text_output)
        decision = AgentDecision(**data)
        return decision
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Invalid or incomplete JSON from LLM: {e}")

def agent_execute(decision: AgentDecision) -> str:
    if decision.tool_name == "create_task":
        # Get time context from the decision
        time_context = getattr(decision, 'time_context', None)
        
        # Merge time context into task creation
        if time_context and 'formatted_date' in time_context:
            if not decision.tool_input.due_date:
                decision.tool_input.due_date = time_context['formatted_date']
        
        new_task = create_task(decision.tool_input)
        return f"Created task '{new_task.title}' with due date {new_task.due_date}"
    elif decision.tool_name == "search_tasks_by_subject":
        tasks = search_tasks_by_subject(decision.tool_input.subject)
        message = "Found the specified task."
        if not tasks:
            tasks = list_reccent_tasks()
            message = "The specified task was not found. Here are the recent tasks:"
        titles = ", ".join(t.title for t in tasks)
        return f"{message} {len(tasks)} tasks: {titles}"
    elif decision.tool_name == "get_task_service":
        task = get_task_service(decision.tool_input.id)
        return f"Task: {task.title}, due: {task.due_date}"
    elif decision.tool_name == "list_tasks_by_date_range":
        tasks = list_tasks_by_date_range(decision.tool_input.start_date, decision.tool_input.end_date)
        if not tasks:
            return "No tasks found."
        titles = ", ".join(t.title for t in tasks)
        return f"Found {len(tasks)} tasks: {titles}"
    elif decision.tool_name == "delete_task":
        # Ensure we have a subject
        if not hasattr(decision.tool_input, "subject"):
            raise ValueError("Delete task requires a subject")
        
        subject = decision.tool_input.subject
        result = delete_task(subject)
        return f"Found task {subject} and deleted it:{result.message}"  # Use the message from TaskDelete
    elif decision.tool_name == "update_task":
        print(f"Decision: {decision}")
        if hasattr(decision.tool_input, "subject") and decision.tool_input.subject:
            subject = decision.tool_input.subject
            tasks = search_tasks_by_subject(subject, limit=1)
            if not tasks:
                return f"No task found matching '{subject}'"
            task_id = tasks[0].id
            print(f"Task ID: {task_id}")
            # Update the ID in the tool input
            decision.tool_input.id = task_id
        else:
            return "Cannot update task: No subject provided"
        
        try:
            updated_task = update_task(decision.tool_input)
            changes = []
            if decision.tool_input.title is not None:
                changes.append("title")
            if decision.tool_input.description is not None:
                changes.append("description")
            if decision.tool_input.due_date is not None:
                changes.append("due date")
            if decision.tool_input.priority is not None:
                changes.append("priority")
            if decision.tool_input.completed is not None:
                completion_status = "marked complete" if decision.tool_input.completed else "marked incomplete"
                changes.append(completion_status)
            
            changes_text = ", ".join(changes)
            return f"Updated task '{updated_task.title}' ({changes_text})"
        except Exception as e:
            return f"Error updating task: {str(e)}"
    else:
        return "Unknown tool. Be more specific with your request."

def agent_step(user_query: str) -> str:
    """
    1) Parse the LLM's decision using the provided user query.
    2) Execute the corresponding tool based on the decision.
    3) Return the final response.
    """
    logger = logging.getLogger(__name__)
    
    logger.info(f"Processing user query: {user_query}")
    decision = parse_agent_decision(user_query)
    logger.info(f"Tool selected: {decision.tool_name}")
    
    # Print the tool input with better formatting
    if hasattr(decision, 'tool_input'):
        input_dict = decision.tool_input.dict() if hasattr(decision.tool_input, 'dict') else vars(decision.tool_input)
        logger.info(f"Tool input: {input_dict}")
    
    result = agent_execute(decision)
    logger.info(f"Result: {result}")
    return result
