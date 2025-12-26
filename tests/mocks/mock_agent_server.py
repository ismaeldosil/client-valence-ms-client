"""
Mock Agent Server.

Simulates an AI Agent with a knowledge base for testing.

Usage:
    python -m tests.mocks.mock_agent_server
    # Runs on http://localhost:8080
"""

import asyncio
import random
import time
from typing import Optional

import structlog
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from .mock_responses import get_response_for_query

logger = structlog.get_logger()

app = FastAPI(
    title="Mock Agent Server",
    description="Simulates the AI Agent for testing",
    version="0.1.0",
)


# === Models ===


class QueryContext(BaseModel):
    """Context information for the query."""

    platform: str = "test"
    user_id: str = ""
    user_name: str = ""


class HistoryMessage(BaseModel):
    """A message in conversation history."""

    role: str
    content: str


class QueryRequest(BaseModel):
    """Request model for /query endpoint."""

    message: str
    context: QueryContext = QueryContext()
    conversation_history: Optional[list[HistoryMessage]] = None


class QueryResponse(BaseModel):
    """Response model for /query endpoint."""

    text: str
    sources: list[str] = []
    confidence: float = 0.0
    processing_time_ms: int = 0


# === Endpoints ===


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "mock-agent"}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """
    Query the agent.

    Simulates:
    - Knowledge base search
    - Variable latency (0.3 - 1.5 seconds)
    - Responses with sources and confidence
    """
    start_time = time.time()

    # Simulate latency (0.3 - 1.5 seconds)
    delay = random.uniform(0.3, 1.5)
    await asyncio.sleep(delay)

    # Search in knowledge base
    response_data = get_response_for_query(request.message)

    # Adapt response if there's history
    if request.conversation_history:
        response_data = _adapt_with_history(response_data, request.conversation_history)

    processing_time = int((time.time() - start_time) * 1000)

    logger.info(
        "query_processed",
        message_preview=request.message[:50],
        user_id=request.context.user_id,
        confidence=response_data.get("confidence", 0),
        processing_time_ms=processing_time,
    )

    return QueryResponse(
        text=response_data["text"],
        sources=response_data.get("sources", []),
        confidence=response_data.get("confidence", 0.9),
        processing_time_ms=processing_time,
    )


def _adapt_with_history(response_data: dict, history: list[HistoryMessage]) -> dict:
    """Adapt response based on conversation history."""
    # Get recent history text
    history_text = " ".join([m.content for m in history[-3:]])

    # If vacation was mentioned recently, add context
    if "vacaciones" in history_text.lower() and "vacaciones" not in response_data["text"].lower():
        return {
            **response_data,
            "text": f"Continuando con el tema anterior: {response_data['text']}",
        }

    return response_data


# === Main ===

if __name__ == "__main__":
    print("=" * 60)
    print("  Mock Agent Server")
    print("=" * 60)
    print()
    print("  URL: http://localhost:8080")
    print()
    print("  Endpoints:")
    print("  - GET  /health  - Health check")
    print("  - POST /query   - Query the agent")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()
    uvicorn.run(app, host="0.0.0.0", port=8080)
