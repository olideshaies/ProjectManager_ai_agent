from typing import List, Dict, Tuple
from app.services.conversation_agent import handle_conversation
from app.services.agent import parse_agent_decision, agent_execute
from app.models.conversation_models import ConversationContext
import logging

logger = logging.getLogger(__name__)

def coordinate_agents(conversation_messages: List[Dict], context: Optional[ConversationContext] = None) -> str:
    """
    Coordinates between Alfred (conversation) and Germain (task execution) based on explicit mentions.
    
    Rules:
    - If message contains "Germain", it's an action request
    - Otherwise, Alfred handles the conversation
    """
    # Get the latest user message
    user_query = conversation_messages[-1]["content"].lower()
    
    # Check if this is a Germain request (action)
    if "germain" in user_query:
        try:
            # Remove "Germain" from the query to clean it up
            clean_query = user_query.replace("germain", "").strip()
            # Parse and execute the action
            decision = parse_agent_decision(clean_query)
            result = agent_execute(decision)
            return f"Germain: {result}"
        except Exception as e:
            logger.error(f"Error in task execution: {str(e)}")
            return "Germain: I apologize, but I couldn't process that action. Could you please rephrase your request? For example: 'Germain create task Write documentation'"
    
    # Otherwise, let Alfred handle it
    try:
        response, is_action, updated_context = handle_conversation(conversation_messages, context)
        # Even if conversation agent suggests an action, don't execute it
        # Just return the response to guide the user
        return f"Alfred: {response}"
    except Exception as e:
        logger.error(f"Error in conversation: {str(e)}")
        return "Alfred: I'm here to help. What would you like to discuss?" 