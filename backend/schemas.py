"""
Pydantic schemas for structured API request/response validation.
Using structured outputs ensures enterprise-grade data handling.
"""

from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""
    message: str
    interaction_id: Optional[int] = None
    conversation_history: Optional[list] = None


class UpdatedFields(BaseModel):
    """Partial CRM form field updates returned by AI tools."""
    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = None
    interaction_date: Optional[str] = None
    interaction_time: Optional[str] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    product_discussed: Optional[str] = None
    sentiment: Optional[str] = None
    follow_up_required: Optional[bool] = None
    notes: Optional[str] = None
    shared_materials: Optional[str] = None
    samples_distributed: Optional[str] = None
    outcomes: Optional[str] = None
    next_action: Optional[str] = None
    summary: Optional[str] = None
    compliance_status: Optional[str] = None
    ai_followup_suggestions: Optional[str] = None


class InteractionInput(UpdatedFields):
    """Structured CRM form payload for manual create/update flows."""
    pass


class ChatResponse(BaseModel):
    """Structured JSON response from the AI agent."""
    reply: str
    tool_used: Optional[str] = None
    interaction_id: Optional[int] = None
    updated_fields: Optional[dict] = None
    confidence: Optional[float] = None
    activity_log: Optional[list[str]] = None
