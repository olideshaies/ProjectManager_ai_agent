# app/routers/chat.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.database.session import get_db
from app.models.conversation_models import MessageCreate, MessageOut
from app.services.tools.conversation_tools import create_message, list_messages_in_conversation
from app.models.chat_models import ChatRequest, ChatResponse
from app.services.agent_coordinator import coordinate_agents

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_with_agent(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Multi-turn conversation endpoint that:
    1. Stores user message
    2. Retrieves *all* past conversation messages
    3. Calls coordinate_agents(...) to route to Alfred or Germain
    4. Stores assistant message
    5. Returns AI message + conversation_id
    """
    # 1) If conversation_id is not provided, generate a new one
    convo_id = req.conversation_id or uuid.uuid4()

    # 2) Store this new user message in the DB
    user_msg = MessageCreate(
        conversation_id=convo_id,
        role="user",
        content=req.user_message
    )
    create_message(db, user_msg)

    # 3) Retrieve all messages for this conversation
    all_msgs = list_messages_in_conversation(db, convo_id)

    # 4) Build conversation context list
    conversation_context = []
    for msg in all_msgs:
        conversation_context.append({"role": msg.role, "content": msg.content})

    # 5) Call coordinator to route to appropriate agent
    agent_reply = coordinate_agents(conversation_context)

    # 6) Store the assistant's response
    assistant_msg = MessageCreate(
        conversation_id=convo_id,
        role="assistant",
        content=agent_reply
    )
    create_message(db, assistant_msg)

    # 7) Return the conversation_id and response
    return ChatResponse(
        conversation_id=convo_id,
        ai_message=agent_reply
    )
