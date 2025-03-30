from unittest.mock import patch
from app.models.agent_decision import AgentDecision
from app.models.task_models import CreateTask, TaskOut
from app.services.agent import agent_step

def fake_create_task(task: CreateTask) -> TaskOut:
    # This fake function simulates creating a task and returns a TaskOut.
    return TaskOut(
        id="fake-task-id",
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        completed=False
    )

def test_agent_decision_create_task():
    # Prepare a fake AgentDecision that simulates the LLM returning a JSON decision.
    fake_decision = AgentDecision(
        tool_name="create_task",
        tool_input=CreateTask(
            title="Alfred Project Manager MVP",
            description=(
                "When trigger activated start Alfred and listen to request able to either add a task, "
                "search for a task and schedule task to calendar due date end of this Sunday and about 5 hours of work"
            ),
            due_date="2025-03-22T23:59:59"  # Example due date in ISO 8601 format.
        )
    )
    
    # Patch the parts of the agent flow:
    # 1. Override parse_agent_decision to return our fake decision.
    # 2. Patch create_task (as imported in the agent module) so it doesn't call the real implementation.
    with patch("app.services.agent.parse_agent_decision", return_value=fake_decision):
        with patch("app.services.agent.create_task", side_effect=fake_create_task):
            result = agent_step("Simulated voice input for task creation")
    
    # The agent step should now execute the create_task branch.
    expected_message = "Created task 'Alfred Project Manager MVP' with due date 2025-03-22T23:59:59"
    assert result == expected_message
