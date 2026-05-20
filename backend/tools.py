"""
LangGraph Tools — 5 CRM agent tools for HCP interaction management.

CRITICAL: All tools use LangGraph + LLM for their logic.
No hardcoded business logic — the LLM drives entity extraction,
summarization, follow-up suggestions, and compliance analysis.
"""

import json
from datetime import datetime, timezone
from typing import Optional, Type, TypeVar
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from database import SessionLocal
from models import Interaction
from groq_client import GroqRateLimitError, get_groq_llm, invoke_groq_with_retry

load_dotenv()


def _get_db() -> Session:
    """Get a fresh database session for tool execution."""
    return SessionLocal()


def _get_llm():
    """Get a fresh LLM instance for tool-level reasoning."""
    return get_groq_llm(max_tokens=300, temperature=0.2)


# ---------------------------------------------------------------------------
# Pydantic Schemas — strict validation for LLM JSON outputs
# ---------------------------------------------------------------------------
T = TypeVar("T", bound=BaseModel)


def _parse_llm_json(content: str, model_cls: Type[T]) -> T:
    """Parse and validate strict JSON from the LLM."""
    data = json.loads(content)
    return model_cls.model_validate(data)


class LogInteractionExtraction(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hcp_name: str = ""
    interaction_date: str = ""
    product_discussed: str = ""
    sentiment: str = ""
    shared_materials: str = ""
    notes: str = ""
    follow_up_required: bool = False
    next_action: str = ""
    interaction_type: Optional[str] = None
    interaction_time: Optional[str] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    samples_distributed: Optional[str] = None
    outcomes: Optional[str] = None


class InteractionEdits(BaseModel):
    model_config = ConfigDict(extra="forbid")

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


class FollowupSuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    next_action: str
    suggestions: list[str]


class SummaryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str


class ComplianceOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compliance_status: str
    issues: list[str]
    checks_passed: list[str]


# ---------------------------------------------------------------------------
# TOOL 1 — Log Interaction (Mandatory)
# ---------------------------------------------------------------------------
@tool
def log_interaction(user_input: str) -> dict:
    """Log a new HCP interaction using LLM-driven entity extraction."""
    db = _get_db()
    try:
        llm = _get_llm()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        prompt = f"""Extract CRM interaction details from the following conversation.

Return STRICT JSON:
{{
  "hcp_name": "",
  "interaction_date": "",
  "product_discussed": "",
  "sentiment": "",
  "shared_materials": "",
  "notes": "",
  "follow_up_required": false,
  "next_action": "",
  "interaction_type": "",
  "interaction_time": "",
  "attendees": "",
  "topics_discussed": "",
  "samples_distributed": "",
  "outcomes": ""
}}

Rules:
- Extract ALL fields present in the conversation.
- If no specific date is mentioned, use today's date: {today}
- sentiment MUST be one of: positive, negative, neutral (mandatory - infer from tone if needed)
- interaction_date MUST be filled (use {today} if not specified)
- Use empty strings only for optional fields (attendees, samples_distributed, outcomes)
- Do NOT fabricate information not in the conversation, EXCEPT date (use today) and sentiment (infer tone)

Conversation:
{user_input}
"""

        try:
            response = invoke_groq_with_retry(
                llm,
                [
                    SystemMessage(
                        content=(
                            "You are a pharmaceutical CRM extraction engine. "
                            "Return ONLY valid JSON that matches the schema."
                        )
                    ),
                    HumanMessage(content=prompt),
                ],
            )
            extraction = _parse_llm_json(response.content, LogInteractionExtraction)
        except GroqRateLimitError:
            return {
                "status": "error",
                "tool_used": "log_interaction",
                "message": "LLM unavailable due to rate limiting.",
                "interaction_id": None,
                "updated_fields": None,
                "activity_log": ["LLM extraction unavailable (rate limited)"],
            }
        except (json.JSONDecodeError, ValidationError):
            return {
                "status": "error",
                "tool_used": "log_interaction",
                "message": "LLM response was not valid JSON.",
                "interaction_id": None,
                "updated_fields": None,
                "activity_log": ["LLM extraction returned invalid JSON"],
            }

        interaction = Interaction()
        extracted = extraction.model_dump()
        for field_name, value in extracted.items():
            if value is None:
                continue
            # Normalize sentiment to allowed values: Positive, Neutral, Negative
            if field_name == 'sentiment' and value:
                value_lower = value.lower().strip()
                # Map variations to allowed values
                if 'positive' in value_lower or 'interested' in value_lower or 'good' in value_lower:
                    value = 'Positive'
                elif 'negative' in value_lower or 'uninterested' in value_lower or 'bad' in value_lower or 'closed' in value_lower:
                    value = 'Negative'
                else:
                    # Default lukewarm, neutral, ambiguous → Neutral
                    value = 'Neutral'
            setattr(interaction, field_name, value)

        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return {
            "status": "success",
            "tool_used": "log_interaction",
            "interaction_id": interaction.id,
            "updated_fields": interaction.to_dict(),
            "activity_log": [
                "Extracted HCP entity",
                "Mapped product and sentiment signals",
                "Captured materials and follow-up intent",
                "Created CRM interaction record",
            ],
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# TOOL 2 — Edit Interaction (Mandatory)
# ---------------------------------------------------------------------------
@tool
def edit_interaction(interaction_id: int, correction_text: str) -> dict:
    """Edit an existing HCP interaction using LLM-driven correction parsing."""
    db = _get_db()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return {
                "status": "error",
                "tool_used": "edit_interaction",
                "message": f"Interaction {interaction_id} not found",
                "interaction_id": interaction_id,
                "updated_fields": None,
            }

        llm = _get_llm()
        existing = json.dumps(interaction.to_dict(), ensure_ascii=False)
        prompt = f"""Existing interaction:
{existing}

User correction:
{correction_text}

Your task:
1. Identify which fields the user wants to change
2. For "sentiment was X" - extract sentiment value (positive, negative, neutral ONLY)
3. For date corrections - extract new date
4. Return STRICT JSON with ONLY the fields to update (no empty fields)
5. If field is mentioned but empty, still include it in the JSON

Examples:
- "sentiment was positive" → {{"sentiment": "positive"}}
- "date was yesterday" → {{"interaction_date": "<yesterday's date>"}}
- "correction: Dr. Jones not Dr. Smith" → {{"hcp_name": "Dr. Jones"}}

Return only valid JSON with fields to update.
"""

        try:
            response = invoke_groq_with_retry(
                llm,
                [
                    SystemMessage(
                        content=(
                            "You are a CRM data editor. Return ONLY valid JSON "
                            "containing fields that must be updated."
                        )
                    ),
                    HumanMessage(content=prompt),
                ],
            )
            edits = _parse_llm_json(response.content, InteractionEdits)
        except GroqRateLimitError:
            return {
                "status": "error",
                "tool_used": "edit_interaction",
                "message": "LLM unavailable due to rate limiting.",
                "interaction_id": interaction_id,
                "updated_fields": None,
                "activity_log": ["LLM correction parsing unavailable (rate limited)"],
            }
        except (json.JSONDecodeError, ValidationError):
            return {
                "status": "error",
                "tool_used": "edit_interaction",
                "message": "LLM response was not valid JSON.",
                "interaction_id": interaction_id,
                "updated_fields": None,
                "activity_log": ["LLM correction parsing returned invalid JSON"],
            }

        changes = {
            key: value
            for key, value in edits.model_dump(exclude_none=True).items()
            if not (isinstance(value, str) and not value.strip())
        }

        changed_fields = {}
        activity = []

        for field_name, value in changes.items():
            # Normalize sentiment to allowed values: Positive, Neutral, Negative
            if field_name == 'sentiment' and value:
                value_lower = value.lower().strip()
                # Map variations to allowed values
                if 'positive' in value_lower or 'interested' in value_lower or 'good' in value_lower:
                    value = 'Positive'
                elif 'negative' in value_lower or 'uninterested' in value_lower or 'bad' in value_lower or 'closed' in value_lower:
                    value = 'Negative'
                else:
                    # Default lukewarm, neutral, ambiguous → Neutral
                    value = 'Neutral'
            setattr(interaction, field_name, value)
            changed_fields[field_name] = value
            label = field_name.replace("_", " ").title()
            activity.append(f"Updated {label}")

        if changed_fields:
            interaction.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(interaction)

        return {
            "status": "success",
            "tool_used": "edit_interaction",
            "interaction_id": interaction.id,
            "updated_fields": interaction.to_dict(),
            "changed_fields": changed_fields,
            "activity_log": activity if activity else ["No fields were changed"],
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# TOOL 3 — Suggest Follow-up (LLM-DRIVEN)
# ---------------------------------------------------------------------------
@tool
def suggest_followup(interaction_id: int) -> dict:
    """Suggest follow-up actions for an existing HCP interaction using AI analysis."""
    db = _get_db()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return {
                "status": "error",
                "tool_used": "suggest_followup",
                "message": f"Interaction {interaction_id} not found",
                "interaction_id": interaction_id,
                "updated_fields": None,
            }

        llm = _get_llm()
        prompt = f"""You are a pharmaceutical sales strategy advisor. Based on this HCP interaction,
suggest exactly 3 specific, actionable follow-up actions.

Interaction Details:
- HCP: {interaction.hcp_name}
- Date: {interaction.interaction_date}
- Product: {interaction.product_discussed}
- Sentiment: {interaction.sentiment}
- Notes: {interaction.notes}
- Topics: {interaction.topics_discussed}
- Outcomes: {interaction.outcomes}
- Materials Shared: {interaction.shared_materials}

Respond in this exact JSON format only:
{{
  "next_action": "The single most important next step (one sentence)",
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}"""

        try:
            response = invoke_groq_with_retry(
                llm,
                [
                    SystemMessage(
                        content=(
                            "You are a pharmaceutical CRM advisor. "
                            "Respond ONLY with valid JSON."
                        )
                    ),
                    HumanMessage(content=prompt),
                ],
            )
            ai_result = _parse_llm_json(response.content, FollowupSuggestionOutput)
        except GroqRateLimitError:
            return {
                "status": "error",
                "tool_used": "suggest_followup",
                "message": "LLM unavailable due to rate limiting.",
                "interaction_id": interaction_id,
                "updated_fields": None,
                "activity_log": ["LLM follow-up generation unavailable (rate limited)"],
            }
        except (json.JSONDecodeError, ValidationError):
            return {
                "status": "error",
                "tool_used": "suggest_followup",
                "message": "LLM response was not valid JSON.",
                "interaction_id": interaction_id,
                "updated_fields": None,
                "activity_log": ["LLM follow-up generation returned invalid JSON"],
            }

        interaction.follow_up_required = True
        interaction.next_action = ai_result.next_action
        interaction.ai_followup_suggestions = json.dumps(ai_result.suggestions)
        interaction.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(interaction)

        return {
            "status": "success",
            "tool_used": "suggest_followup",
            "interaction_id": interaction.id,
            "updated_fields": interaction.to_dict(),
            "suggestions": ai_result.suggestions,
            "activity_log": [
                f"Analyzed interaction with {interaction.hcp_name}",
                "LLM generated follow-up plan",
                f"Set next action: {ai_result.next_action}",
                "Marked follow-up as required",
            ],
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# TOOL 4 — Generate Summary (LLM-DRIVEN)
# ---------------------------------------------------------------------------
@tool
def generate_summary(interaction_id: int) -> dict:
    """Generate a concise professional CRM summary using AI."""
    db = _get_db()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return {
                "status": "error",
                "tool_used": "generate_summary",
                "message": f"Interaction {interaction_id} not found",
                "interaction_id": interaction_id,
                "updated_fields": None,
            }

        llm = _get_llm()
        prompt = f"""Generate a concise, professional CRM interaction summary (3-4 sentences max) for this HCP interaction.
Write it as a field representative's log entry.

Interaction Details:
- HCP: {interaction.hcp_name}
- Type: {interaction.interaction_type}
- Date: {interaction.interaction_date}
- Product: {interaction.product_discussed}
- Sentiment: {interaction.sentiment}
- Notes: {interaction.notes}
- Topics Discussed: {interaction.topics_discussed}
- Materials Shared: {interaction.shared_materials}
- Samples: {interaction.samples_distributed}
- Outcomes: {interaction.outcomes}
- Follow-up Required: {interaction.follow_up_required}
- Next Action: {interaction.next_action}

Respond in this exact JSON format only:
{{
  "summary": "summary text"
}}"""

        try:
            response = invoke_groq_with_retry(
                llm,
                [
                    SystemMessage(
                        content=(
                            "You are a CRM summary writer for pharmaceutical sales. "
                            "Respond ONLY with valid JSON."
                        )
                    ),
                    HumanMessage(content=prompt),
                ],
            )
            summary_result = _parse_llm_json(response.content, SummaryOutput)
        except GroqRateLimitError:
            return {
                "status": "error",
                "tool_used": "generate_summary",
                "message": "LLM unavailable due to rate limiting.",
                "interaction_id": interaction_id,
                "updated_fields": None,
                "activity_log": ["LLM summary generation unavailable (rate limited)"],
            }
        except (json.JSONDecodeError, ValidationError):
            return {
                "status": "error",
                "tool_used": "generate_summary",
                "message": "LLM response was not valid JSON.",
                "interaction_id": interaction_id,
                "updated_fields": None,
                "activity_log": ["LLM summary generation returned invalid JSON"],
            }

        interaction.summary = summary_result.summary
        interaction.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(interaction)

        return {
            "status": "success",
            "tool_used": "generate_summary",
            "interaction_id": interaction.id,
            "updated_fields": interaction.to_dict(),
            "summary": summary_result.summary,
            "activity_log": [
                f"Retrieved interaction data for {interaction.hcp_name}",
                "LLM generated professional summary",
                "Saved summary to interaction record",
            ],
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# TOOL 5 — Compliance Check (LLM-DRIVEN)
# ---------------------------------------------------------------------------
@tool
def compliance_check(interaction_id: int) -> dict:
    """Check regulatory compliance of an HCP interaction using AI analysis."""
    db = _get_db()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return {
                "status": "error",
                "tool_used": "compliance_check",
                "message": f"Interaction {interaction_id} not found",
                "interaction_id": interaction_id,
                "updated_fields": None,
            }

        llm = _get_llm()
        prompt = f"""You are a pharmaceutical regulatory compliance officer. Analyze this HCP interaction for compliance issues.

Check for:
1. Are all mandatory fields documented? (HCP name, date, product, sentiment, notes)
2. Are there any potentially non-compliant claims (e.g., "cure", "guaranteed", "no side effects")?
3. Is the documentation sufficiently detailed?
4. Are shared materials and samples properly recorded?
5. Is follow-up documentation consistent?

Interaction Details:
- HCP Name: "{interaction.hcp_name}"
- Date: "{interaction.interaction_date}"
- Product: "{interaction.product_discussed}"
- Sentiment: "{interaction.sentiment}"
- Notes: "{interaction.notes}"
- Topics: "{interaction.topics_discussed}"
- Materials Shared: "{interaction.shared_materials}"
- Samples Distributed: "{interaction.samples_distributed}"
- Outcomes: "{interaction.outcomes}"
- Follow-up Required: {interaction.follow_up_required}
- Next Action: "{interaction.next_action}"

Respond in this exact JSON format only:
{{
  "compliance_status": "Compliant" or "Needs Review" or "Non-Compliant",
  "issues": ["issue 1", "issue 2"],
  "checks_passed": ["check 1", "check 2"]
}}"""

        try:
            response = invoke_groq_with_retry(
                llm,
                [
                    SystemMessage(
                        content=(
                            "You are a pharmaceutical compliance auditor. "
                            "Respond ONLY with valid JSON."
                        )
                    ),
                    HumanMessage(content=prompt),
                ],
            )
            ai_result = _parse_llm_json(response.content, ComplianceOutput)
        except GroqRateLimitError:
            return {
                "status": "error",
                "tool_used": "compliance_check",
                "message": "LLM unavailable due to rate limiting.",
                "interaction_id": interaction_id,
                "updated_fields": None,
                "activity_log": ["LLM compliance analysis unavailable (rate limited)"],
            }
        except (json.JSONDecodeError, ValidationError):
            return {
                "status": "error",
                "tool_used": "compliance_check",
                "message": "LLM response was not valid JSON.",
                "interaction_id": interaction_id,
                "updated_fields": None,
                "activity_log": ["LLM compliance analysis returned invalid JSON"],
            }

        activity = [
            "Checking mandatory fields",
            "LLM scanning for regulatory issues",
            "Evaluating documentation completeness",
            "Checking follow-up consistency",
        ]

        interaction.compliance_status = ai_result.compliance_status
        interaction.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(interaction)

        return {
            "status": "success",
            "tool_used": "compliance_check",
            "interaction_id": interaction.id,
            "updated_fields": interaction.to_dict(),
            "compliance_status": ai_result.compliance_status,
            "issues": ai_result.issues,
            "checks_passed": ai_result.checks_passed,
            "activity_log": activity,
        }
    finally:
        db.close()


# Export all tools for the agent
all_tools = [
    log_interaction,
    edit_interaction,
    suggest_followup,
    generate_summary,
    compliance_check,
]
