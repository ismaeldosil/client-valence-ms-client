"""Webhook receiver API for Teams Outgoing Webhooks.

This FastAPI application receives messages from Teams Outgoing Webhooks,
processes them through the AI agent, and returns responses.

Phase 2: Stateless - Each message is independent
Phase 3: Will add session management for conversation continuity
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
import structlog

from src.core.config import settings
from src.agent import AgentClient
from src.teams.receiver import (
    HMACVerifier,
    HMACVerificationError,
    TeamsMessage,
    TeamsMessageHandler,
    create_verifier,
)

logger = structlog.get_logger(__name__)

# Global instances (initialized on startup)
_agent_client: AgentClient | None = None
_message_handler: TeamsMessageHandler | None = None
_hmac_verifier: HMACVerifier | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _agent_client, _message_handler, _hmac_verifier

    logger.info(
        "receiver_starting",
        agent_url=settings.agent_base_url,
        hmac_configured=bool(settings.teams_hmac_secret),
    )

    # Initialize agent client
    _agent_client = AgentClient(
        base_url=settings.agent_base_url,
        api_key=settings.agent_api_key,
        timeout=settings.agent_timeout,
        max_retries=settings.agent_max_retries,
    )

    # Initialize message handler
    _message_handler = TeamsMessageHandler(
        agent_client=_agent_client,
        timeout_message="The request is taking longer than expected. Teams has a 5-second limit for responses. Please try a simpler question.",
        error_message="I'm having trouble connecting to my knowledge base. Please try again in a moment.",
    )

    # Initialize HMAC verifier (optional)
    _hmac_verifier = create_verifier(settings.teams_hmac_secret)
    if not _hmac_verifier:
        logger.warning(
            "hmac_verification_disabled",
            reason="TEAMS_HMAC_SECRET not configured",
        )

    yield

    # Cleanup
    if _agent_client:
        await _agent_client.close()
    logger.info("receiver_stopped")


# Create FastAPI app
app = FastAPI(
    title="Teams Webhook Receiver",
    description="Receives messages from Teams Outgoing Webhooks and routes to AI Agent",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint.

    Returns basic health status. Does not require authentication.
    """
    agent_status = "unknown"
    agent_version = "unknown"

    if _agent_client:
        try:
            health = await _agent_client.health_check()
            agent_status = health.get("status", "unknown")
            agent_version = health.get("version", "unknown")
        except Exception as e:
            agent_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "version": "2.0.0",
        "phase": "2-stateless",
        "hmac_enabled": _hmac_verifier is not None,
        "agent": {
            "url": settings.agent_base_url,
            "status": agent_status,
            "version": agent_version,
        },
    }


@app.post("/webhook")
async def webhook_handler(request: Request):
    """Handle incoming Teams Outgoing Webhook messages.

    This endpoint receives messages when users @mention the bot in Teams.
    It verifies the HMAC signature (if configured), processes the message
    through the agent, and returns a response.

    The response must be returned within 5 seconds due to Teams limitations.

    Returns:
        JSON response with text or Adaptive Card for Teams to display
    """
    # Get raw body for HMAC verification
    body = await request.body()

    # Verify HMAC signature if configured
    if _hmac_verifier:
        auth_header = request.headers.get("Authorization")
        try:
            _hmac_verifier.verify(auth_header, body)
        except HMACVerificationError as e:
            logger.warning("hmac_verification_failed", error=str(e))
            raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse the message
    try:
        data = await request.json()
        message = TeamsMessage.from_dict(data)
    except Exception as e:
        logger.error("message_parse_error", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid message format")

    log = logger.bind(
        message_id=message.id,
        user_name=message.from_user.name,
        conversation_id=message.conversation.id,
        clean_text=message.get_clean_text()[:50],
    )

    log.info("webhook_received")

    # Process the message
    if not _message_handler:
        log.error("handler_not_initialized")
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        response = await _message_handler.handle(message)
        log.info("webhook_response_sent")
        return JSONResponse(content=response.to_dict())

    except Exception as e:
        log.error("handler_error", error=str(e))
        return JSONResponse(
            content={
                "type": "message",
                "text": "An unexpected error occurred. Please try again.",
            }
        )


@app.post("/api/v1/test-message")
async def test_message(request: Request):
    """Test endpoint for sending messages without HMAC verification.

    Only available in development mode. Useful for testing with Postman.
    """
    if settings.environment not in ("development", "local", "test"):
        raise HTTPException(status_code=403, detail="Only available in development")

    try:
        data = await request.json()
        message = TeamsMessage.from_dict(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid message: {e}")

    if not _message_handler:
        raise HTTPException(status_code=503, detail="Service not ready")

    response = await _message_handler.handle(message)
    return JSONResponse(content=response.to_dict())


def create_app() -> FastAPI:
    """Factory function to create the app instance."""
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.receiver_api:app",
        host="0.0.0.0",
        port=settings.receiver_port,
        reload=settings.environment == "development",
    )
