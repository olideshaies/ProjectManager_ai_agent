from app.models.conversation_models import EnhancedConversationResponse, Intent, IntentType, ConversationContext
from app.services.llm_factory import LLMFactory
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def handle_conversation(conversation_messages: List[Dict], context: Optional[ConversationContext] = None) -> Tuple[str, bool, ConversationContext]:
    """
    Handles general conversational interactions with the user.
    
    Args:
        conversation_messages: List of conversation messages with role and content
        context: Optional conversation context from previous interactions
    
    Returns:
        Tuple containing:
        - response text
        - boolean indicating if this should be handed to task agent
        - updated conversation context
    """
    # Initialize or use provided context
    if not context:
        context = ConversationContext()
    
    # Get the latest user message
    user_query = conversation_messages[-1]["content"]
    
    # First, determine if this is a direct action request that should go to task agent
    action_verbs = ["create", "add", "make", "set up", "generate", "delete", "remove", "update", "change", "modify"]
    action_objects = ["task", "goal", "reminder", "project", "todo"]
    
    # Check if this is clearly a task action
    is_task_action = False
    lower_query = user_query.lower()
    
    # Look for explicit task actions
    for verb in action_verbs:
        for obj in action_objects:
            if f"{verb} {obj}" in lower_query or f"{verb} a {obj}" in lower_query or f"{verb} the {obj}" in lower_query:
                is_task_action = True
                break
        if is_task_action:
            break
    
    # If it's a clear task action, let the coordinator know to pass to task agent
    if is_task_action:
        return (
            "I understand you want to take action on a task or goal. Let me help with that.",
            True,
            context
        )
    
    # Otherwise, handle as conversation
    provider = "openai"
    factory = LLMFactory(provider=provider)
    
    # Generate a system prompt based on context
    context_section = context.to_prompt() if context.to_prompt() else "No prior context available."
    
    system_prompt = f"""
    You are Alfred, a helpful assistant that specializes in conversations and planning.
    
    CURRENT CONVERSATION CONTEXT:
    {context_section}
    
    CONVERSATION GUIDELINES:
    1. Engage in natural, helpful conversation with the user
    2. Help the user think through plans and goals
    3. Maintain the conversation topic and follow logical transitions
    4. If the user mentions "algorithmic trading strategy", be sure to reference our previous discussions
    5. Don't create, modify, or delete tasks/goals directly - suggest that as next steps instead
    
    Your primary role is to discuss, plan, and help the user think through their ideas.
    When the user is ready to create specific tasks or goals, guide them to use specific commands.
    """
    
    # Prepare conversation messages
    conv_messages = [{"role": "system", "content": system_prompt}]
    # Include the last 5 messages for context
    for m in conversation_messages[-5:]:
        conv_messages.append({"role": m["role"], "content": m["content"]})
    
    try:
        completion = factory.create_completion(
            response_model=EnhancedConversationResponse,
            messages=conv_messages
        )
        
        # Update context
        context.update_from_response(completion)
        
        # Extract relevant information from the response
        if "algorithmic trading" in user_query.lower() and "algorithmic trading strategy" not in context.topic_details:
            context.current_topic = "algorithmic trading strategy"
            context.topic_details["algorithmic trading strategy"] = []
        
        # Analyze the response for steps or points
        lines = completion.response.split("\n")
        current_type = "general"
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                if line.startswith(("•", "-", "*", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.")):
                    clean_point = line.strip("•-*123456789. ")
                    if clean_point:
                        context.add_discussion_point(clean_point, current_type)
                        
                        # Add to topic details if relevant
                        if context.current_topic and len(clean_point) > 10:
                            if context.current_topic not in context.topic_details:
                                context.topic_details[context.current_topic] = []
                            context.topic_details[context.current_topic].append(clean_point)
        
        response = completion.response
        
        # Add suggested next steps if available
        if completion.suggested_actions:
            if not any(step in response for step in completion.suggested_actions):
                action_suggestions = "\n\nNext steps:"
                for action in completion.suggested_actions:
                    action_suggestions += f"\n- {action}"
                response += action_suggestions
        
        return response, False, context
        
    except Exception as e:
        logger.error(f"Error in conversation handling: {str(e)}")
        # Fallback response
        return "I'm here to help. What would you like to discuss?", False, context 