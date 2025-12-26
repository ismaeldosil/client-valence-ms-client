"""
Notifier API.

FastAPI application for receiving notification requests from the Agent.
"""

from typing import Optional

import structlog
import uvicorn
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from ..core.config import settings
from ..notifier.channels import ChannelRegistry
from ..notifier.service import NotificationService
from ..teams.sender.webhook_sender import WebhookSender

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Teams Notifier API",
    description="API for sending notifications to Microsoft Teams",
    version="1.0.0",
)

# Initialize services (lazy initialization)
_sender: Optional[WebhookSender] = None
_channels: Optional[ChannelRegistry] = None
_service: Optional[NotificationService] = None


def get_service() -> NotificationService:
    """Get or create the notification service."""
    global _sender, _channels, _service

    if _service is None:
        _sender = WebhookSender()
        _channels = ChannelRegistry.from_settings(settings)
        _service = NotificationService(_sender, _channels)

    return _service


def get_channels() -> ChannelRegistry:
    """Get or create the channel registry."""
    global _channels

    if _channels is None:
        _channels = ChannelRegistry.from_settings(settings)

    return _channels


# Request/Response Models


class NotifyRequest(BaseModel):
    """Request body for sending a notification."""

    channel: str = Field(..., description="Target channel name")
    message: str = Field(..., description="Notification message", min_length=1)
    title: Optional[str] = Field(None, description="Optional title")
    card_type: Optional[str] = Field(
        None,
        description="Card type: alert, info, report (or null for text)",
    )
    priority: str = Field(
        "medium",
        description="Priority: low, medium, high, critical",
    )
    metadata: Optional[dict] = Field(
        default_factory=dict,
        description="Additional data for card templates",
    )


class NotifyResponse(BaseModel):
    """Response after sending a notification."""

    success: bool
    notification_id: str
    channel: str
    status: str
    error: Optional[str] = None


class ChannelInfo(BaseModel):
    """Channel information."""

    name: str
    enabled: bool
    description: Optional[str] = None


class ChannelsResponse(BaseModel):
    """Response for listing channels."""

    channels: list[ChannelInfo]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str


# Authentication


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """
    Verify the API key from request header.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        The API key if valid

    Raises:
        HTTPException: 401 if API key is invalid
    """
    if x_api_key != settings.notifier_api_key:
        logger.warning("invalid_api_key", key_preview=x_api_key[:8] + "...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )
    return x_api_key


# Endpoints


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint (no auth required)."""
    return HealthResponse(status="ok", service="notifier")


@app.post("/api/v1/notify", response_model=NotifyResponse)
async def notify(
    request: NotifyRequest,
    api_key: str = Header(..., alias="X-API-Key"),
) -> NotifyResponse:
    """
    Send a notification to a Teams channel.

    Requires X-API-Key header for authentication.
    """
    verify_api_key(api_key)

    service = get_service()

    try:
        notification = await service.notify(
            channel=request.channel,
            message=request.message,
            title=request.title,
            card_type=request.card_type,
            priority=request.priority,
            metadata=request.metadata,
        )

        return NotifyResponse(
            success=True,
            notification_id=notification.id,
            channel=notification.channel,
            status=notification.status.value,
        )

    except ValueError as e:
        # Channel not found
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error("notification_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/channels", response_model=ChannelsResponse)
async def list_channels(
    api_key: str = Header(..., alias="X-API-Key"),
) -> ChannelsResponse:
    """
    List available notification channels.

    Requires X-API-Key header for authentication.
    """
    verify_api_key(api_key)

    channels = get_channels()

    return ChannelsResponse(
        channels=[
            ChannelInfo(
                name=c.name,
                enabled=c.enabled,
                description=c.description,
            )
            for c in channels.get_all()
        ]
    )


# Startup/Shutdown events


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    logger.info("notifier_api_starting", port=settings.notifier_port)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    global _sender
    if _sender:
        await _sender.close()
    logger.info("notifier_api_stopped")


# Main entry point


if __name__ == "__main__":
    print("=" * 60)
    print("  Teams Notifier API")
    print("=" * 60)
    print()
    print(f"  URL: http://localhost:{settings.notifier_port}")
    print()
    print("  Endpoints:")
    print("  - GET  /health           - Health check")
    print("  - POST /api/v1/notify    - Send notification")
    print("  - GET  /api/v1/channels  - List channels")
    print()
    print("  Docs: http://localhost:{}/docs".format(settings.notifier_port))
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    uvicorn.run(app, host="0.0.0.0", port=settings.notifier_port)
