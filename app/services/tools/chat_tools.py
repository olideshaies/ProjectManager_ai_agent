from app.models.conversation_models import ChatRequest, ChatResponse, MessageCreate
from app.services.tools.conversation_tools import (
    list_messages_in_conversation,
    create_message
)
from sqlalchemy.orm import Session
import uuid
from fastapi import Depends
from app.database.session import get_db
from app.services.agent import agent_step

def chat_with_agent(req: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """
    1) Retrieve or generate conversation_id
    2) Pull all previous messages from DB
    3) Append the new user message to the context
    4) Pass the entire list of messages to `agent_step`
    5) Store the assistant's reply
    6) Return the AI reply + conversation_id
    """
    # 1) If conversation_id not provided, generate a new one
    convo_id = req.conversation_id or uuid.uuid4()

    # 2) Fetch all previous messages
    past_msgs = list_messages_in_conversation(db, convo_id)
    
    # Convert them into the format [ {"role": "...", "content": "..."}, ... ]
    conversation_messages = []
    for m in past_msgs:
        conversation_messages.append({"role": m.role, "content": m.content})
    
    # 3) Append the new user message
    #   Also store it in DB
    user_msg = MessageCreate(
        conversation_id=convo_id,
        role="user",
        content=req.user_message
    )
    create_message(db, user_msg)
    
    conversation_messages.append({"role": "user", "content": req.user_message})

    # 4) Pass everything to `agent_step(conversation_messages)`
    ai_reply_text = agent_step(conversation_messages)

    # 5) Store the assistant's reply
    assistant_msg = MessageCreate(
        conversation_id=convo_id,
        role="assistant",
        content=ai_reply_text
    )
    create_message(db, assistant_msg)

    # 6) Return final response with convo_id + AI text
    return ChatResponse(
        conversation_id=convo_id,
        ai_message=ai_reply_text
    )
