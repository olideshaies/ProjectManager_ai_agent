# app/services/tools/conversation_tools.py

import uuid
from typing import List
from sqlalchemy.orm import Session
from app.models.conversation_models import MessageCreate, MessageOut, ConversationMessageDB

def create_message(db: Session, msg_in: MessageCreate) -> MessageOut:
    """
    Insert a new message row in conversation_messages table.
    If no conversation_id is provided, generate one to start a new conversation.
    """
    convo_id = msg_in.conversation_id or uuid.uuid4()

    db_message = ConversationMessageDB(
        conversation_id=convo_id,
        user_id=msg_in.user_id,
        role=msg_in.role,
        content=msg_in.content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    return MessageOut(
        id=db_message.id,
        conversation_id=db_message.conversation_id,
        role=db_message.role,
        content=db_message.content,
        created_at=db_message.created_at,
        user_id=db_message.user_id
    )

def list_messages_in_conversation(db: Session, convo_id: uuid.UUID) -> List[MessageOut]:
    """
    Returns all messages in a given conversation, sorted by created_at ascending (optional).
    """
    db_msgs = db.query(ConversationMessageDB)\
                .filter(ConversationMessageDB.conversation_id == convo_id)\
                .order_by(ConversationMessageDB.created_at.asc())\
                .all()
    return [
        MessageOut(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
            user_id=m.user_id
        )
        for m in db_msgs
    ]

