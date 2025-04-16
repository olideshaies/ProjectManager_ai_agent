# app/models/conversation_model.py

import uuid
from sqlalchemy import Column, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy import String
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

from app.database.base import Base  # or however you import your Base

class ConversationMessageDB(Base):
    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(String, nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MessageCreate(BaseModel):
    role: str  = Field(description="The role of the message sender. Must be one of 'user', 'assistant', or 'system'")
    content: str = Field(description="The content of the message")
    conversation_id: Optional[uuid.UUID] = Field(description="The ID of the conversation the message belongs to")
    user_id: Optional[uuid.UUID] = Field(description="The ID of the user who sent the message")

class MessageOut(BaseModel):
    id: uuid.UUID = Field(description="The unique identifier for the message")
    conversation_id: uuid.UUID = Field(description="The ID of the conversation the message belongs to")
    role: str = Field(description="The role of the message sender. Must be one of 'user', 'assistant', or 'system'")
    content: str = Field(description="The content of the message")
    created_at: datetime = Field(description="The date and time the message was created")
    user_id: Optional[uuid.UUID] = Field(description="The ID of the user who sent the message")

class IntentType(str, Enum):
    DISCUSS = "discuss"  # General discussion or information gathering
    PLAN = "plan"       # Planning or strategizing
    ACTION = "action"   # Explicit action request
    QUERY = "query"     # Information request

class DiscussionPoint(BaseModel):
    """A single point of discussion with its context"""
    content: str = Field(description="The content of the discussion point")
    type: str = Field(description="The type of point (e.g., 'step', 'goal', 'task')")
    order: Optional[int] = Field(default=None, description="Order in a sequence if applicable")

class ConversationContext(BaseModel):
    """Enhanced context tracking for conversations"""
    current_topic: Optional[str] = Field(
        default=None,
        description="The current topic being discussed"
    )
    current_step: Optional[str] = Field(
        default=None,
        description="The current step in a multi-step process"
    )
    discussion_points: List[DiscussionPoint] = Field(
        default_factory=list,
        description="Key points from the discussion"
    )
    next_steps: List[str] = Field(
        default_factory=list,
        description="Planned next steps"
    )
    last_intent: Optional[IntentType] = Field(
        default=None,
        description="The last detected intent"
    )
    topic_details: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Detailed information about topics discussed"
    )
    
    def update_from_response(self, response: 'EnhancedConversationResponse'):
        """Update context based on the latest response"""
        if response.suggested_actions:
            self.next_steps = response.suggested_actions
        if response.detected_intent:
            self.last_intent = response.detected_intent.primary_intent
        if response.topic_details:
            for topic, details in response.topic_details.items():
                if topic not in self.topic_details:
                    self.topic_details[topic] = []
                self.topic_details[topic].extend(details)

    def to_prompt(self) -> str:
        """Convert context to a prompt section"""
        context_parts = []
        
        # Add current topic and its details
        if self.current_topic:
            context_parts.append(f"Current Topic: {self.current_topic}")
            if self.current_topic in self.topic_details:
                details = "\n".join(f"  - {detail}" for detail in self.topic_details[self.current_topic][-5:])
                context_parts.append(f"Topic Details:\n{details}")
        
        # Add current step
        if self.current_step:
            context_parts.append(f"Current Step: {self.current_step}")
        
        # Add recent discussion points
        if self.discussion_points:
            recent_points = self.discussion_points[-5:]  # Last 5 points
            points_text = "\n".join(f"- {point.content} ({point.type})" for point in recent_points)
            context_parts.append(f"Recent Discussion Points:\n{points_text}")
        
        # Add next steps
        if self.next_steps:
            steps = "\n".join(f"- {step}" for step in self.next_steps)
            context_parts.append(f"Planned Next Steps:\n{steps}")
        
        return "\n\n".join(context_parts)

    def add_discussion_point(self, content: str, point_type: str, order: Optional[int] = None):
        """Add a new discussion point"""
        point = DiscussionPoint(content=content, type=point_type, order=order)
        self.discussion_points.append(point)

class Intent(BaseModel):
    """Model for classifying user intent in conversations"""
    primary_intent: IntentType = Field(
        description="The primary type of intent detected in the message"
    )
    confidence: float = Field(
        description="Confidence score for the intent classification",
        ge=0.0,
        le=1.0
    )
    action_words: List[str] = Field(
        default=[],
        description="Action words detected in the message"
    )
    requires_confirmation: bool = Field(
        default=False,
        description="Whether this intent requires confirmation before executing"
    )

class ConversationResponse(BaseModel):
    """
    Model for conversational responses from the LLM.
    This provides a structured way to get responses for general conversation.
    """
    response: str = Field(
        description="The conversational response from the assistant"
    )
    
    follow_up_suggestion: Optional[str] = Field(
        default=None,
        description="Optional suggestion for follow-up questions or actions"
    )

class EnhancedConversationResponse(BaseModel):
    """Enhanced model for conversation responses that includes intent understanding"""
    response: str = Field(
        description="The conversational response from the assistant"
    )
    detected_intent: Intent = Field(
        description="The detected intent from the user's message"
    )
    suggested_actions: Optional[List[str]] = Field(
        default=None,
        description="Suggested next actions based on the conversation"
    )
    requires_confirmation: bool = Field(
        default=False,
        description="Whether the next step requires user confirmation"
    )
    topic_details: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Details about topics discussed in this response"
    )
    current_step_details: Optional[Dict[str, str]] = Field(
        default=None,
        description="Details about the current step in a process"
    )