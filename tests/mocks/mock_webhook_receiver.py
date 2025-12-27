"""
Mock Webhook Receiver.

Simulates our future webhook receiver for testing.

Usage:
    python -m tests.mocks.mock_webhook_receiver
    # Runs on http://localhost:3000
"""

from typing import Any, Optional

import structlog
import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel

logger = structlog.get_logger()

app = FastAPI(
    title="Mock Webhook Receiver",
    description="Simulates the Teams webhook receiver for testing",
    version="0.1.0",
)


# === Models ===


class TeamsUser(BaseModel):
    """Teams user information."""

    id: str
    name: str


class TeamsConversation(BaseModel):
    """Teams conversation information."""

    id: str


class TeamsMessage(BaseModel):
    """Teams message format from Outgoing Webhook."""

    type: str = "message"
    id: str
    text: str
    from_: Optional[TeamsUser] = None
    conversation: Optional[TeamsConversation] = None

    class Config:
        populate_by_name = True

    def __init__(self, **data: Any):
        # Handle 'from' reserved keyword
        if "from" in data:
            data["from_"] = data.pop("from")
        super().__init__(**data)


class WebhookResponse(BaseModel):
    """Response format for Teams."""

    type: str = "message"
    text: str


# === Endpoints ===


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "mock-webhook"}


@app.post("/webhook", response_model=WebhookResponse)
async def webhook(request: Request) -> WebhookResponse:
    """
    Receive message from Teams.

    Simulates:
    - Message parsing
    - @mention removal
    - Command handling
    """
    body = await request.json()

    try:
        message = TeamsMessage(**body)
    except Exception as e:
        logger.error("parse_error", error=str(e))
        return WebhookResponse(text="Error parsing message")

    # Extract text without @mention
    text = message.text
    if "</at>" in text:
        text = text.split("</at>", 1)[1].strip()

    user_name = message.from_.name if message.from_ else "Unknown"

    logger.info(
        "webhook_received",
        user=user_name,
        text_preview=text[:50] if text else "",
        message_id=message.id,
    )

    # Handle commands
    text_lower = text.lower().strip()

    if text_lower == "/clear":
        return WebhookResponse(text="Historial limpiado (mock)")

    if text_lower == "/history":
        return WebhookResponse(text="No hay historial disponible (mock)")

    if text_lower == "/help":
        return WebhookResponse(
            text=(
                "**Comandos disponibles:**\n\n"
                "- `/clear` - Limpiar historial\n"
                "- `/history` - Ver historial\n"
                "- `/help` - Mostrar ayuda"
            )
        )

    # Default response
    return WebhookResponse(
        text=(f"Recibido: '{text[:100]}'\n\n_(Respuesta mock del webhook receiver)_")
    )


# === Main ===

if __name__ == "__main__":
    print("=" * 60)
    print("  Mock Webhook Receiver")
    print("=" * 60)
    print()
    print("  URL: http://localhost:3000")
    print()
    print("  Endpoints:")
    print("  - GET  /health   - Health check")
    print("  - POST /webhook  - Receive Teams message")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()
    uvicorn.run(app, host="0.0.0.0", port=3000)
