"""
Mock Agent Server.

Simulates the Valerie Supplier Chatbot API v2.2.0 for testing.
Implements the same contract as the real agent.

Usage:
    python -m tests.mocks.mock_agent_server
    # Runs on http://localhost:8080
"""

import asyncio
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .mock_responses import get_response_for_query

logger = structlog.get_logger()

app = FastAPI(
    title="Mock Agent Server",
    description="Simulates the Valerie Supplier Chatbot API v2.2.0 for testing",
    version="2.2.0",
)

# In-memory session storage
_sessions: dict[str, dict[str, Any]] = {}


# === Models (matching real API) ===


class ChatRequest(BaseModel):
    """Request to send a chat message."""

    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    session_id: str | None = Field(None, description="Existing session ID")
    user_id: str | None = Field(None, description="User identifier")


class AgentExecution(BaseModel):
    """Details of an agent's execution."""

    agent_name: str
    display_name: str
    status: str = "completed"
    duration_ms: int = 0
    output: dict[str, Any] = {}


class ChatResponse(BaseModel):
    """Response from chat endpoint."""

    session_id: str
    message: str
    agents_executed: list[AgentExecution] = []
    intent: str | None = None
    confidence: float | None = None
    requires_approval: bool = False


class Message(BaseModel):
    """A single chat message."""

    role: str
    content: str
    timestamp: datetime


class SessionResponse(BaseModel):
    """Response with session details."""

    session_id: str
    status: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    messages: list[Message] = []


class ServiceHealth(BaseModel):
    """Health status of a service."""

    name: str
    status: str
    latency_ms: float | None = None
    message: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: datetime | None = None
    services: list[ServiceHealth] = []


# === Endpoints ===


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="2.2.0-mock",
        timestamp=datetime.now(timezone.utc),
        services=[
            ServiceHealth(name="knowledge_base", status="healthy", latency_ms=5.2),
            ServiceHealth(name="agent_pipeline", status="healthy", latency_ms=12.1),
        ],
    )


@app.get("/ready")
async def readiness() -> dict:
    """Readiness check endpoint."""
    return {"ready": True, "checks": {"database": True, "agents": True}}


@app.get("/live")
async def liveness() -> dict:
    """Liveness check endpoint."""
    return {"alive": True}


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the chatbot.

    Simulates:
    - Session management
    - Agent pipeline execution
    - Intent detection
    - Variable latency (0.3 - 1.5 seconds)
    """
    start_time = time.time()

    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())[:12]
    if session_id not in _sessions:
        _sessions[session_id] = {
            "created_at": datetime.now(timezone.utc),
            "messages": [],
            "status": "active",
        }

    session = _sessions[session_id]

    # Add user message to history
    session["messages"].append(
        {
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now(timezone.utc),
        }
    )
    session["last_activity"] = datetime.now(timezone.utc)

    # Simulate latency (0.3 - 1.5 seconds)
    delay = random.uniform(0.3, 1.5)
    await asyncio.sleep(delay)

    # Get response from knowledge base
    response_data = get_response_for_query(request.message)

    # Detect intent
    intent = _detect_intent(request.message)
    confidence = response_data.get("confidence", 0.85)

    # Simulate agent executions
    processing_time = int((time.time() - start_time) * 1000)
    agents_executed = [
        AgentExecution(
            agent_name="guardrails",
            display_name="Guardrails",
            status="completed",
            duration_ms=int(processing_time * 0.1),
        ),
        AgentExecution(
            agent_name="intent_classifier",
            display_name="Intent Classifier",
            status="completed",
            duration_ms=int(processing_time * 0.2),
            output={"intent": intent, "confidence": confidence},
        ),
        AgentExecution(
            agent_name="knowledge_retrieval",
            display_name="Knowledge Retrieval",
            status="completed",
            duration_ms=int(processing_time * 0.5),
        ),
        AgentExecution(
            agent_name="response_generator",
            display_name="Response Generator",
            status="completed",
            duration_ms=int(processing_time * 0.2),
        ),
    ]

    # Add assistant message to history
    session["messages"].append(
        {
            "role": "assistant",
            "content": response_data["text"],
            "timestamp": datetime.now(timezone.utc),
        }
    )

    logger.info(
        "chat_processed",
        session_id=session_id,
        message_preview=request.message[:50],
        user_id=request.user_id,
        intent=intent,
        confidence=confidence,
        processing_time_ms=processing_time,
    )

    return ChatResponse(
        session_id=session_id,
        message=response_data["text"],
        agents_executed=agents_executed,
        intent=intent,
        confidence=confidence,
        requires_approval=False,
    )


@app.get("/api/v1/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """Get session details and history."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
    messages = [
        Message(
            role=m["role"],
            content=m["content"],
            timestamp=m["timestamp"],
        )
        for m in session["messages"]
    ]

    return SessionResponse(
        session_id=session_id,
        status=session.get("status", "active"),
        created_at=session["created_at"],
        last_activity=session.get("last_activity", session["created_at"]),
        message_count=len(messages),
        messages=messages,
    )


@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete a session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del _sessions[session_id]
    logger.info("session_deleted", session_id=session_id)
    return {"deleted": True, "session_id": session_id}


# === Legacy endpoint (for backward compatibility) ===


class LegacyQueryRequest(BaseModel):
    """Legacy request model for /query endpoint."""

    message: str
    context: dict = {}
    conversation_history: list[dict] | None = None


class LegacyQueryResponse(BaseModel):
    """Legacy response model for /query endpoint."""

    text: str
    sources: list[str] = []
    confidence: float = 0.0
    processing_time_ms: int = 0


@app.post("/query", response_model=LegacyQueryResponse)
async def legacy_query(request: LegacyQueryRequest) -> LegacyQueryResponse:
    """
    Legacy query endpoint (deprecated).

    Use /api/v1/chat instead.
    """
    start_time = time.time()

    # Simulate latency
    delay = random.uniform(0.3, 1.5)
    await asyncio.sleep(delay)

    response_data = get_response_for_query(request.message)
    processing_time = int((time.time() - start_time) * 1000)

    return LegacyQueryResponse(
        text=response_data["text"],
        sources=response_data.get("sources", []),
        confidence=response_data.get("confidence", 0.9),
        processing_time_ms=processing_time,
    )


# === Helper functions ===


def _detect_intent(message: str) -> str:
    """Detect the user's intent from the message."""
    message_lower = message.lower()

    if any(word in message_lower for word in ["supplier", "proveedor", "vendor"]):
        return "supplier_search"
    elif any(word in message_lower for word in ["certif", "nadcap", "as9100"]):
        return "certification_check"
    elif any(word in message_lower for word in ["risk", "riesgo", "quality", "calidad"]):
        return "risk_assessment"
    elif any(word in message_lower for word in ["hola", "hello", "hi", "hey"]):
        return "greeting"
    elif any(word in message_lower for word in ["help", "ayuda", "?"]):
        return "help_request"
    else:
        return "general_query"


# === Main ===

if __name__ == "__main__":
    print("=" * 60)
    print("  Mock Agent Server (Valerie API v2.2.0)")
    print("=" * 60)
    print()
    print("  URL: http://localhost:8080")
    print()
    print("  Endpoints:")
    print("  - GET  /health              - Health check")
    print("  - GET  /ready               - Readiness check")
    print("  - GET  /live                - Liveness check")
    print("  - POST /api/v1/chat         - Chat with agent")
    print("  - GET  /api/v1/sessions/:id - Get session")
    print("  - DEL  /api/v1/sessions/:id - Delete session")
    print("  - POST /query               - Legacy endpoint (deprecated)")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()
    uvicorn.run(app, host="0.0.0.0", port=8080)
