# tests/test_agent_decision_flow.py
from types import SimpleNamespace
from unittest.mock import patch
from app.models.agent_decision import AgentDecision
from app.models.task_models import CreateTask, TaskOut
from app.services.agent import agent_step

# Fake implementation for create_task tool.
def fake_create_task(task: CreateTask) -> TaskOut:
    return TaskOut(
        id="fake-task-id",
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        completed=False
    )

# Fake implementation for search_tasks_by_subject tool.
# It now accepts a subject string and returns a list of TaskOut objects.
def fake_search_tasks_by_subject(subject: str) -> list:
    return [
        TaskOut(
            id="fake-task-id-1",
            title="Fake Task 1",
            description="Fake description 1",
            due_date="2025-03-22T23:59:59",
            completed=False
        ),
        TaskOut(
            id="fake-task-id-2",
            title="Fake Task 2",
            description="Fake description 2",
            due_date="2025-03-23T23:59:59",
            completed=False
        )
    ]

def test_agent_decision_create_task():
    # Create a fake decision indicating that a new task should be created.
    fake_decision = AgentDecision(
        tool_name="create_task",
        tool_input=CreateTask(
            title="Alfred Project Manager MVP",
            description=(
                "When trigger activated start Alfred and listen to request able to either add a task, "
                "search for a task and schedule task to calendar due date end of this Sunday and about 5 hours of work"
            ),
            due_date="2025-03-22T23:59:59"
        )
    )
    
    # Patch the decision parsing and task creation functions.
    with patch("app.services.agent.parse_agent_decision", return_value=fake_decision):
        with patch("app.services.agent.create_task", side_effect=fake_create_task):
            result = agent_step("Simulated voice input for creating a task")
    
    expected_message = "Created task 'Alfred Project Manager MVP' with due date 2025-03-22T23:59:59"
    assert result == expected_message

def test_agent_decision_search_task():
    # Instead of using a dict, we use SimpleNamespace to create a fake tool input that has a 'subject' attribute.
    fake_input = SimpleNamespace(subject="Alfred")
    
    # Use model_construct (or construct) to create a fake decision.
    fake_decision = AgentDecision.model_construct(
        tool_name="search_task",
        tool_input=fake_input
    )
    
    with patch("app.services.agent.parse_agent_decision", return_value=fake_decision):
        with patch("app.services.agent.search_tasks_by_subject", side_effect=fake_search_tasks_by_subject):
            result = agent_step("Simulated voice input for searching tasks")
    
    expected_message = "Found 2 tasks: Fake Task 1, Fake Task 2"
    assert result == expected_message
