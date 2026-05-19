"""
SQLAlchemy ORM models for CRM interactions.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from database import Base


class Interaction(Base):
    """Represents a single HCP interaction logged by a field representative."""

    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hcp_name = Column(String(255), nullable=True, default="")
    interaction_type = Column(String(50), nullable=True, default="Meeting")
    interaction_date = Column(String(50), nullable=True, default="")
    interaction_time = Column(String(20), nullable=True, default="")
    attendees = Column(String(500), nullable=True, default="")
    topics_discussed = Column(Text, nullable=True, default="")
    product_discussed = Column(String(255), nullable=True, default="")
    sentiment = Column(String(50), nullable=True, default="")
    follow_up_required = Column(Boolean, default=False)
    notes = Column(Text, nullable=True, default="")
    shared_materials = Column(String(500), nullable=True, default="")
    samples_distributed = Column(String(500), nullable=True, default="")
    outcomes = Column(Text, nullable=True, default="")
    next_action = Column(String(500), nullable=True, default="")
    summary = Column(Text, nullable=True, default="")
    compliance_status = Column(String(50), nullable=True, default="Pending")
    ai_followup_suggestions = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        """Serialize to dictionary for API responses."""
        return {
            "id": self.id,
            "hcp_name": self.hcp_name or "",
            "interaction_type": self.interaction_type or "Meeting",
            "interaction_date": self.interaction_date or "",
            "interaction_time": self.interaction_time or "",
            "attendees": self.attendees or "",
            "topics_discussed": self.topics_discussed or "",
            "product_discussed": self.product_discussed or "",
            "sentiment": self.sentiment or "",
            "follow_up_required": self.follow_up_required or False,
            "notes": self.notes or "",
            "shared_materials": self.shared_materials or "",
            "samples_distributed": self.samples_distributed or "",
            "outcomes": self.outcomes or "",
            "next_action": self.next_action or "",
            "summary": self.summary or "",
            "compliance_status": self.compliance_status or "Pending",
            "ai_followup_suggestions": self.ai_followup_suggestions or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
