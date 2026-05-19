"""
LangGraph Agent — The AI orchestration core.

Uses a StateGraph with stateful conversational continuity for
multi-tool CRM interaction management.

Architecture:
    User Message → Intent Detection → Tool Selection → Execute Tool
    → Update CRM State → Return Structured Response
"""

import json
from typing import Optional, Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from tools import all_tools
from groq_client import get_groq_llm, invoke_groq_with_retry

load_dotenv()

# ---------------------------------------------------------------------------
# Agent State — maintains conversational continuity across turns
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    """LangGraph state schema with CRM-specific fields.
    
    The state maintains conversational continuity across interaction edits 
    and follow-up actions, enabling multi-turn agentic workflows.
    """
    messages: Annotated[list, add_messages]
    interaction_id: Optional[int]
    updated_fields: Optional[dict]
    tool_used: Optional[str]
    conversation_history: Optional[list]
    confidence: Optional[float]
    activity_log: Optional[list]


# ---------------------------------------------------------------------------
# System Prompt — guides the LLM's tool selection and behavior
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an AI CRM assistant for pharmaceutical field representatives.

Your responsibility is to manage HCP interactions using conversational AI.

You must:
- extract structured CRM data
- identify edits and corrections
- generate compliant summaries
- suggest follow-up actions
- verify healthcare compliance

Tools:
1. log_interaction: For NEW interactions. Pass unstructured conversation text.
2. edit_interaction: Correct/update data. Requires interaction_id + correction_text.
3. suggest_followup: Recommend next steps. Requires interaction_id.
4. generate_summary: Create a summary. Requires interaction_id.
5. compliance_check: Verify compliance. Requires interaction_id.

Rules:
- Always use tools when applicable.
- Never fabricate missing information.
- Return structured outputs.
- Current interaction_id: {interaction_id}. Use this for tools 2-5 if not specified.
"""


# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------
def _get_llm():
    """Initialize Groq LLM with tool binding.
    
    Uses llama-3.1-8b-instant. Note: gemma2-9b-it was decommissioned by Groq
    and is no longer available. This model is the official replacement with
    better performance and higher rate limits.
    """
    llm = get_groq_llm(max_tokens=450, temperature=0.2)
    return llm.bind_tools(all_tools)


# ---------------------------------------------------------------------------
# Graph Nodes
# ---------------------------------------------------------------------------
def agent_node(state: AgentState):
    """LLM reasoning node — decides which tool to call or responds directly."""
    llm = _get_llm()

    # Build system message with current context
    interaction_id = state.get("interaction_id") or "none yet"
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    system_msg = SystemMessage(
        content=SYSTEM_PROMPT.format(
            today_date=today,
            interaction_id=interaction_id,
        )
    )

    # Prepend system message to conversation
    messages = [system_msg] + state["messages"]

    response = invoke_groq_with_retry(llm, messages)
    return {"messages": [response]}


# ---------------------------------------------------------------------------
# Build & Compile the LangGraph
# ---------------------------------------------------------------------------
def build_graph():
    """Construct the LangGraph StateGraph for CRM agent orchestration.
    
    Graph Flow:
        START -> agent (LLM) -> [tools_condition] -> tools (ToolNode) -> END
                                                   -> END
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(all_tools))

    # Add edges — the agent decides whether to call a tool or finish
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", END)

    return graph.compile()


# Compile the graph once at module level
compiled_graph = build_graph()


# ---------------------------------------------------------------------------
# Public API — invoke the agent
# ---------------------------------------------------------------------------
def run_agent(
    user_message: str,
    interaction_id: Optional[int] = None,
    conversation_history: Optional[list] = None,
) -> dict:
    """Run the LangGraph agent with a user message.
    
    Args:
        user_message: Natural language input from the user.
        interaction_id: Current interaction ID for context (if any).
        conversation_history: Previous messages for multi-turn context.
    
    Returns:
        Structured dict with: reply, tool_used, interaction_id,
        updated_fields, confidence, activity_log.
    """
    # Build messages list with conversation history for continuity
    messages = []
    if conversation_history:
        # Keep recent context compact to avoid Groq TPM spikes.
        recent_history = conversation_history[-4:]
        for msg in recent_history:
            if msg.get("role") == "user":
                content = str(msg["content"])[:350]
                messages.append(HumanMessage(content=content))
            elif msg.get("role") == "assistant":
                # Truncate extremely long assistant messages just in case
                content = str(msg["content"])[:300]
                messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=user_message[:800]))

    # Invoke the compiled LangGraph
    initial_state = {
        "messages": messages,
        "interaction_id": interaction_id,
        "updated_fields": None,
        "tool_used": None,
        "conversation_history": conversation_history or [],
        "confidence": None,
        "activity_log": None,
    }

    result = compiled_graph.invoke(initial_state)

    # Parse the result — extract tool info from messages
    return _parse_agent_result(result)


def _parse_agent_result(result: dict) -> dict:
    """Extract structured response data from LangGraph execution result."""
    messages = result.get("messages", [])

    # The final AI message is the reply
    reply = ""
    tool_used = None
    interaction_id = None
    updated_fields = None
    confidence = None
    activity_log = None
    last_tool_data = None

    # Walk through messages to find tool calls and results
    for msg in messages:
        # Check for tool call messages (ToolMessage)
        if hasattr(msg, "type") and msg.type == "tool":
            tool_payload = getattr(msg, "content", None)
            if isinstance(tool_payload, str):
                try:
                    tool_payload = json.loads(tool_payload)
                except json.JSONDecodeError:
                    continue

            if isinstance(tool_payload, dict):
                last_tool_data = tool_payload
                tool_used = tool_payload.get("tool_used", tool_used)
                interaction_id = tool_payload.get("interaction_id", interaction_id)
                updated_fields = tool_payload.get("updated_fields", updated_fields)
                activity_log = tool_payload.get("activity_log", activity_log)

    # Get the final AI message as the reply
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "ai" and msg.content:
            reply = msg.content
            break

    # Calculate confidence based on fields extracted
    if updated_fields and tool_used:
        filled_count = sum(1 for v in updated_fields.values() if v)
        total = len(updated_fields)
        confidence = round(min(0.95, 0.7 + (filled_count / total) * 0.25), 2)
    elif tool_used:
        confidence = 0.88

    return {
        "reply": reply or _build_tool_reply(tool_used, last_tool_data),
        "tool_used": tool_used,
        "interaction_id": interaction_id,
        "updated_fields": updated_fields,
        "confidence": confidence,
        "activity_log": activity_log,
    }


def _build_tool_reply(tool_used: str | None, tool_data: dict | None) -> str:
    """Create a deterministic confirmation after a tool mutates CRM state."""
    if not tool_data:
        return "I've processed your request."

    if tool_data.get("status") == "error":
        return tool_data.get("message") or "I could not complete that request."

    updated_fields = tool_data.get("updated_fields") or {}
    hcp_name = updated_fields.get("hcp_name") or "the HCP"

    if tool_used == "log_interaction":
        return f"Logged the interaction for {hcp_name}."
    if tool_used == "edit_interaction":
        changed_fields = tool_data.get("changed_fields") or {}
        if changed_fields:
            return f"Updated {len(changed_fields)} field(s) for {hcp_name}."
        return f"No fields needed changing for {hcp_name}."
    if tool_used == "suggest_followup":
        next_action = updated_fields.get("next_action") or tool_data.get("next_action")
        if next_action:
            return f"Suggested follow-up saved. Next action: {next_action}"
        return "Suggested follow-up saved."
    if tool_used == "generate_summary":
        return f"Generated and saved a summary for {hcp_name}."
    if tool_used == "compliance_check":
        status = tool_data.get("compliance_status") or updated_fields.get("compliance_status")
        if status:
            return f"Compliance check complete: {status}."
        return "Compliance check complete."

    return "I've processed your request."
