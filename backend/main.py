"""
FastAPI Application — AI-First CRM HCP Module

Provides REST endpoints for the React frontend to communicate with
the LangGraph AI agent for HCP interaction management.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from database import engine, Base, get_db
from models import Interaction
from schemas import ChatRequest, ChatResponse, InteractionInput, UpdatedFields
from agent import run_agent
from groq_client import GroqRateLimitError


# ---------------------------------------------------------------------------
# App Lifespan — create DB tables on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created")
    print("[OK] LangGraph agent initialized")
    print("[OK] AI-CRM backend ready")
    yield


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI-CRM HCP Module",
    description="AI-First CRM for Healthcare Professional interaction management using LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "app": "AI-CRM HCP Module",
        "agent": "LangGraph + Groq llama-3.1-8b-instant",
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Process a chat message through the LangGraph AI agent.
    
    This is the CORE endpoint. It:
    1. Receives the user's natural language message
    2. Passes it to the LangGraph agent
    3. The agent decides which tool to call (if any)
    4. Returns structured JSON with updated form fields
    """
    try:
        result = run_agent(
            user_message=request.message,
            interaction_id=request.interaction_id,
            conversation_history=request.conversation_history,
        )

        # Build structured response
        updated = None
        if result.get("updated_fields"):
            updated = UpdatedFields(**{
                k: v for k, v in result["updated_fields"].items()
                if k in UpdatedFields.model_fields
            })

        return ChatResponse(
            reply=result["reply"],
            tool_used=result.get("tool_used"),
            interaction_id=result.get("interaction_id"),
            updated_fields=updated,
            confidence=result.get("confidence"),
            activity_log=result.get("activity_log"),
        )
    except GroqRateLimitError as e:
        retry_after = str(max(1, int(round(e.retry_after_seconds))))
        print(f"Agent rate limited; retry after {retry_after}s")
        raise HTTPException(
            status_code=429,
            detail=(
                "The AI service is temporarily rate limited. "
                f"Please try again in about {retry_after} seconds."
            ),
            headers={"Retry-After": retry_after},
        )
    except Exception as e:
        print(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.get("/api/interactions")
async def list_interactions(db: Session = Depends(get_db)):
    """List all logged HCP interactions."""
    interactions = db.query(Interaction).order_by(Interaction.created_at.desc()).all()
    return [i.to_dict() for i in interactions]


def _apply_interaction_input(interaction: Interaction, payload: InteractionInput) -> Interaction:
    """Copy structured form fields onto an interaction record."""
    data = payload.model_dump(exclude_unset=True)
    for field_name, value in data.items():
        if hasattr(interaction, field_name):
            setattr(interaction, field_name, value)
    return interaction


@app.post("/api/interactions")
async def create_interaction(payload: InteractionInput, db: Session = Depends(get_db)):
    """Create an HCP interaction from structured manual form input."""
    interaction = _apply_interaction_input(Interaction(), payload)
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction.to_dict()


@app.get("/api/interactions/{interaction_id}")
async def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    """Get a single HCP interaction by ID."""
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction.to_dict()


@app.put("/api/interactions/{interaction_id}")
async def update_interaction(
    interaction_id: int,
    payload: InteractionInput,
    db: Session = Depends(get_db),
):
    """Update an HCP interaction from structured manual form input."""
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    _apply_interaction_input(interaction, payload)
    db.commit()
    db.refresh(interaction)
    return interaction.to_dict()
