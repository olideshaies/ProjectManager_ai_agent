# app/services/agent.py
import json
from pydantic import ValidationError
from app.models.agent_decision import AgentDecision
from app.models.conversation_models import ConversationResponse, EnhancedConversationResponse, Intent, IntentType, ConversationContext
from app.models.task_models import TaskUpdate
from app.services.llm_factory import LLMFactory
from app.config.settings import get_settings
from app.services.tools.task_adapters import create_task, search_tasks_by_subject, get_task_service, update_task, list_tasks_by_date_range, delete_task, list_reccent_tasks
from app.services.tools.goal_tools import create_goal, get_goal, update_goal, delete_goal, list_goals, search_goals_by_subject
from app.services.time_utils import TimeParser
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Simple state storage for pending goal linking (replace with more robust session management if needed)
pending_goal_link: Dict = {}


def extract_context_from_messages(messages: List[Dict]) -> ConversationContext:
    """Extract conversation context from message history"""
    context = ConversationContext()
    
    # Analyze messages to build context
    for msg in messages:
        content = msg.get("content", "").lower()
        
        # Try to identify current topic and its details
        if "algorithmic trading" in content:
            context.current_topic = "algorithmic trading strategy"
            # Extract details about algorithmic trading
            if msg["role"] == "assistant":
                lines = content.split("\n")
                trading_details = []
                for line in lines:
                    line = line.strip()
                    if line.startswith(("•", "-", "*", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.")):
                        clean_point = line.strip("•-*123456789. ")
                        if clean_point:
                            trading_details.append(clean_point)
                            context.add_discussion_point(clean_point, "strategy_step")
                if trading_details:
                    if "algorithmic trading strategy" not in context.topic_details:
                        context.topic_details["algorithmic trading strategy"] = []
                    context.topic_details["algorithmic trading strategy"].extend(trading_details)
        
        # Extract steps and discussion points
        if msg["role"] == "assistant":
            lines = content.split("\n")
            current_type = "general"
            for line in lines:
                line = line.strip()
                if "market research" in line.lower():
                    current_type = "market_research"
                elif "define objectives" in line.lower():
                    current_type = "objectives"
                elif "analyze data" in line.lower():
                    current_type = "data_analysis"
                elif "develop" in line.lower() and "strategy" in line.lower():
                    current_type = "strategy_development"
                elif "test" in line.lower():
                    current_type = "testing"
                elif "monitor" in line.lower():
                    current_type = "monitoring"
                
                if line.startswith(("•", "-", "*", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.")):
                    clean_point = line.strip("•-*123456789. ")
                    if clean_point:
                        context.add_discussion_point(clean_point, current_type)
    
    return context

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
    TASK TOOLS:
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
    
    GOAL TOOLS:
    - Use "create_goal" for requests to create a new goal
    - Use "get_goal" for requests to get a specific goal
    - Use "update_goal" for ANY request to change, modify, or update an existing goal
    - Use "delete_goal" for requests to remove a goal
    - Use "list_goals" for requests to see all goals

    When creating goals:
    1. Use explicit due dates from the query
    2. Fall back to parsed time context when no date is specified
    3. Set due_date to None only if no time references exist
    
    Example update requests:
    - "Update Goal Project X set priority to high" → update_goal with {{ "subject": "Project X", "priority": "high" }}
    - "Change the due date of my homework goal to Friday" → update_goal with {{ "subject": "homework", "due_date": "(Friday's date)" }}
    - "Mark my dentist appointment as completed" → update_goal with {{ "subject": "dentist appointment", "completed": true }}
    
    
    
    


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
        
        # Create the task first
        new_task = create_task(decision.tool_input)
        logger.info(f"Created task '{new_task.title}' with id {new_task.id}")

        # Check if there are goals to potentially link
        goals = list_goals()
        if goals:
            # Format the prompt message for the user
            prompt_message = f"Created task '{new_task.title}'. Would you like to link it to a goal?\n"
            goal_options = []
            for i, goal in enumerate(goals, start=1):
                goal_options.append(f"\n {i}. {goal.title}")
            prompt_message += "\n".join(goal_options)
            prompt_message += "\n\nPlease respond with the goal Title or 'No'."

            # Store the necessary state for the next turn
            # Ensure IDs are strings here if the models expect strings later
            pending_goal_link['user_session'] = {
                "task_id": str(new_task.id),
                "task_title": new_task.title,
                "goals": [{"id": str(g.id), "title": g.title} for g in goals]
            }
            logger.info(f"Stored pending goal link state for task {new_task.id}")
            # Return the prompt message to the user
            return prompt_message
        else:
            # No goals exist, just return the creation confirmation
            logger.info("No goals found to link.")
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
            return "Cannot delete task: No subject provided"
        
        try:
            subject = decision.tool_input.subject
            result = delete_task(subject)
            return f"Found task {subject} and deleted it: {result.message}"
        except ValueError as e:
            return str(e)  # Return the "No task found" message
        except Exception as e:
            return f"Error deleting task: {str(e)}"
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
            
    elif decision.tool_name == "create_goal":
        new_goal = create_goal(decision.tool_input)
        return f"Created goal '{new_goal.title}'"
    elif decision.tool_name == "get_goal":
        goal = get_goal(decision.tool_input.id)
        return f"Goal: {goal.title}, Description: {goal.description}, Completed: {goal.completed}"
    elif decision.tool_name == "update_goal":
        # Find goal by subject if provided
        if hasattr(decision.tool_input, "subject") and decision.tool_input.subject:
            subject = decision.tool_input.subject
            goals = search_goals_by_subject(subject, limit=1)
            if not goals:
                return f"No goal found matching '{subject}'"
            goal_id = goals[0].id
            # Update the ID in the tool input
            decision.tool_input.id = goal_id
        
        try:
            updated_goal = update_goal(decision.tool_input)
            changes = []
            if getattr(decision.tool_input, 'title', None) is not None:
                changes.append("title")
            if getattr(decision.tool_input, 'description', None) is not None:
                changes.append("description")
            if getattr(decision.tool_input, 'target_date', None) is not None:
                changes.append("target date")
            if getattr(decision.tool_input, 'completed', None) is not None:
                completion_status = "marked complete" if decision.tool_input.completed else "marked incomplete"
                changes.append(completion_status)
            
            changes_text = ", ".join(changes)
            return f"Updated goal '{updated_goal.title}' ({changes_text})"
        except Exception as e:
            return f"Error updating goal: {str(e)}"
    elif decision.tool_name == "delete_goal":
        # First check if we have a subject attribute instead of an id
        if hasattr(decision.tool_input, "subject") and decision.tool_input.subject:
            subject = decision.tool_input.subject
            goals = search_goals_by_subject(subject, limit=1)
            if not goals:
                return f"No goal found matching '{subject}'"
            goal_id = str(goals[0].id)
        # If we have neither id nor subject, we can't proceed
        elif not hasattr(decision.tool_input, "id") or decision.tool_input.id is None:
            return "Cannot delete goal: No goal ID or subject provided"
        else:
            goal_id = decision.tool_input.id
            
        result = delete_goal(goal_id)
        return f"Goal deleted: {result.message}"
    elif decision.tool_name == "list_goals":
        goals = list_goals()
        if not goals:
            return "You don't have any goals yet."
        return f"Found {len(goals)} goals: {', '.join([goal.title for goal in goals])}"
    else:
        return "Unknown tool. Be more specific with your request."

def classify_intent(user_query: str, conversation_messages: List[Dict], context: ConversationContext) -> Intent:
    """Classifies the user's intent using the LLM with context awareness"""
    provider = "openai"
    factory = LLMFactory(provider=provider)
    
    context_prompt = context.to_prompt()
    
    system_prompt = f"""
    You are an intent classifier for a project management assistant.
    
    Current Conversation Context:
    {context_prompt}
    
    INTENT GUIDELINES:
    1. DISCUSS - User wants to talk about, explore, or understand something
    2. PLAN - User wants to strategize, organize, or prepare something
    3. ACTION - User explicitly wants to create, update, or delete something
    4. QUERY - User wants to retrieve information
    
    Consider the conversation context when determining intent.
    If discussing algorithmic trading strategy and user mentions tasks/steps,
    classify as PLAN unless there's an explicit action command mentioning to Germain to do something.
    
    Examples:
    - "Let's talk about my goals" -> DISCUSS
    - "I want to plan my tasks" -> PLAN
    - "Tell Germain to create a new goal called Project X" -> ACTION
    - "What are my current tasks?" -> QUERY
    - "Let's set tasks for these steps" -> PLAN (when discussing strategy steps)
    
    Return the intent classification as JSON matching the Intent model.
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    
    try:
        completion = factory.create_completion(
            response_model=Intent,
            messages=messages
        )
        return completion
    except Exception as e:
        logger.error(f"Error in intent classification: {str(e)}")
        return Intent(
            primary_intent=IntentType.DISCUSS,
            confidence=0.5,
            action_words=[],
            requires_confirmation=False
        )

def agent_step(conversation_messages: List[Dict]) -> str:
    # Check for pending goal linking state first
    if 'user_session' in pending_goal_link:
        state = pending_goal_link['user_session']
        # 1. Read the raw response
        raw_user_response = conversation_messages[-1]["content"].strip()
        # 2. Normalize the response (strip, remove trailing period, lowercase)
        normalized_response = raw_user_response.rstrip('.').lower()
        
        task_id = state['task_id']
        task_title = state['task_title']
        goals = state['goals']
        
        logger.info(f"Handling raw response '{raw_user_response}' (normalized: '{normalized_response}') for pending goal link for task {task_id}")

        # 3. Check the NORMALIZED response for 'no'
        if normalized_response == 'no' or normalized_response == 'nope':
            del pending_goal_link['user_session']
            logger.info(f"User chose not to link goal for task {task_id}. State cleared.")
            return f"Okay, task '{task_title}' created without linking a goal."
        else:
            # 4. If not 'no', treat the normalized response as the potential goal title
            try:
                goal_title = normalized_response # Already normalized

                if goal_title in [goal['title'].lower() for goal in goals]:
                    #find the goal in the list of goals
                    selected_goal = next(goal for goal in goals if goal['title'].lower() == goal_title)
                    goal_id_to_link = selected_goal['id']
                    goal_title_to_link = selected_goal['title']
                    
                    task_update_payload = TaskUpdate(subject=task_title, id=task_id, goal_id=goal_id_to_link)
                    update_task(task_update_payload)
                    
                    del pending_goal_link['user_session']
                    logger.info(f"Successfully linked task {task_id} to goal {goal_id_to_link}. State cleared.")
                    return f"Linked task '{task_title}' to goal '{goal_title_to_link}'."
                else:
                    logger.warning(f"Invalid goal title {goal_title} provided for task {task_id}.")
                    return f"Invalid goal title. Please choose a title from the list or say 'No'."
            except ValueError:
                # Add debug log INSIDE the exception handler
                logger.warning(f"Could not parse goal title from response '{raw_user_response}'.")
                # Re-prompt with the simplified instruction
                # Construct the simplified prompt message again
                prompt_message = f"Created task '{task_title}'. Would you like to link it to a goal?\n"
                goal_options = []
                for i, goal in enumerate(goals, start=1):
                    goal_options.append(f"{i}. {goal['title']}")
                prompt_message += "\n".join(goal_options)
                prompt_message += "\n\nPlease respond with the goal title or 'No'."
                return f"Invalid response. {prompt_message}"
            except Exception as e:
                logger.error(f"Error linking goal for task {task_id}: {str(e)}", exc_info=True)
                # Clear state on unexpected error to prevent loop
                if 'user_session' in pending_goal_link: del pending_goal_link['user_session']
                return f"An error occurred while linking the goal: {str(e)}"

    # ---- If no pending state, proceed with normal flow ----
    logger.info("No pending goal link state found, proceeding with normal flow.")
    # Extract and maintain conversation context
    context = extract_context_from_messages(conversation_messages)
    
    # Get the latest user message
    user_query = conversation_messages[-1]["content"]
    
    # Classify intent with context awareness
    intent = classify_intent(user_query, conversation_messages, context)
    
    # If it's not an ACTION intent, handle as conversation
    if intent.primary_intent != IntentType.ACTION:
        provider = "openai"
        factory = LLMFactory(provider=provider)
        
        # Include conversation context in the system prompt
        context_section = context.to_prompt()
        
        system_prompt = f"""
        You are Alfred, a helpful project management assistant. You are currently in {intent.primary_intent.value.upper()} mode.
        
        CURRENT CONVERSATION CONTEXT:
        {context_section}
        
        CONVERSATION GUIDELINES:
        1. For DISCUSS: Engage in open dialogue, ask questions, understand user's needs
        2. For PLAN: Help break down goals, suggest approaches, discuss priorities
        3. For QUERY: Provide clear, concise information about existing items
        
        IMPORTANT RULES:
        - Maintain conversation continuity - reference previous points
        - If discussing algorithmic trading strategy, refer to the specific steps previously mentioned
        - When user wants to create tasks, suggest specific tasks for each step
        - Keep responses focused on the current topic
        - Provide clear, actionable next steps
        
        Current conversation intent: {intent.primary_intent.value}
        Confidence: {intent.confidence}
        """
        
        # Include full conversation history
        conv_messages = [{"role": "system", "content": system_prompt}]
        for m in conversation_messages[-5:]:  # Last 5 messages for context
            conv_messages.append({"role": m["role"], "content": m["content"]})
        
        try:
            completion = factory.create_completion(
                response_model=EnhancedConversationResponse,
                messages=conv_messages
            )
            
            # Update conversation context
            context.update_from_response(completion)
            
            # Format response with context awareness
            response = completion.response
            
            # If we're discussing algorithmic trading and tasks, ensure we reference the specific steps
            if (context.current_topic == "algorithmic trading strategy" and 
                any(word in user_query.lower() for word in ["task", "step", "plan"])):
                response = "Based on our discussion about the algorithmic trading strategy, let's create specific tasks for each step:\n\n"
                for point in context.discussion_points:
                    if point.type in ["strategy_step", "market_research", "objectives", "data_analysis", 
                                    "strategy_development", "testing", "monitoring"]:
                        response += f"For {point.content}, we should:\n"
                        response += "1. [Specific task suggestion]\n"
                        response += "2. [Another task suggestion]\n\n"
                response += "\nWould you like to create tasks for any specific step? Just say 'Create task for [step]' and I'll help you set it up."
            
            # Add suggested next steps if available
            if completion.suggested_actions:
                if not any(step in response for step in completion.suggested_actions):
                    action_suggestions = "\n\nNext steps:"
                    for action in completion.suggested_actions:
                        action_suggestions += f"\n- {action}"
                    response += action_suggestions
            
            return response
            
        except Exception as e:
            logger.error(f"Error in conversation handling: {str(e)}")
            if context.current_topic:
                return f"I understand we're discussing {context.current_topic}. Could you clarify your last point?"
            elif intent.primary_intent == IntentType.DISCUSS:
                return "I understand you want to discuss something. Could you tell me more about what's on your mind?"
            elif intent.primary_intent == IntentType.PLAN:
                return "I'm here to help you plan. What specific areas would you like to focus on?"
            else:
                return "I'm here to help. Could you please tell me more about what you'd like to know?"
    
    # Handle ACTION intent with confirmation if needed
    if intent.requires_confirmation:
        # Here you would implement confirmation logic
        # For now, we'll just proceed with the action
        pass
    
    # Process as tool-based command
    try:
        decision = parse_agent_decision(user_query)
        result = agent_execute(decision)
        return result
    except Exception as e:
        # Log the specific error for debugging
        logger.error(f"Error processing action request '{user_query}': {str(e)}", exc_info=True)
        return f"I'm having trouble processing your action request. Could you please rephrase it more explicitly? For example: 'Create a goal called X' or 'Update task Y'"
