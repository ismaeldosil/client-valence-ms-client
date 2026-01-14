"""Bot Framework API endpoints.

This module provides the FastAPI router for Bot Framework messaging
endpoints, handling incoming activities from Microsoft Teams via
the Bot Framework Connector Service.
"""

from typing import TYPE_CHECKING, Optional

import structlog
from botbuilder.schema import Activity
from fastapi import APIRouter, Request, Response

if TYPE_CHECKING:
    from botbuilder.core import BotFrameworkAdapter
    from src.teams.bot_framework import ValerieBot

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Bot Framework"])

# These will be set during app initialization
_bot_adapter: Optional["BotFrameworkAdapter"] = None
_bot_instance: Optional["ValerieBot"] = None


def set_bot_components(
    adapter: "BotFrameworkAdapter",
    bot: "ValerieBot",
) -> None:
    """Set the bot adapter and instance for the API.

    Called during application startup to inject dependencies.

    Args:
        adapter: Configured Bot Framework adapter
        bot: ValerieBot instance
    """
    global _bot_adapter, _bot_instance
    _bot_adapter = adapter
    _bot_instance = bot
    logger.info("bot_api_components_set")


@router.post("/api/messages")
async def bot_messages(request: Request) -> Response:
    """Bot Framework messaging endpoint.

    This endpoint receives all activities from the Bot Framework
    Connector Service, including messages, conversation updates,
    and invoke activities (Adaptive Card actions).

    The Bot Framework authenticates requests using JWT tokens
    in the Authorization header.

    Args:
        request: Incoming HTTP request

    Returns:
        Empty response (Bot Framework expects 200 OK)
    """
    if not _bot_adapter or not _bot_instance:
        logger.error("bot_api_not_initialized")
        return Response(
            content='{"error": "Bot not initialized"}',
            status_code=500,
            media_type="application/json",
        )

    # Get request body and auth header
    body = await request.body()
    auth_header = request.headers.get("Authorization", "")

    # Parse activity
    try:
        body_dict = await request.json()
        activity = Activity().deserialize(body_dict)
    except Exception as e:
        logger.error("bot_activity_parse_error", error=str(e))
        return Response(
            content='{"error": "Invalid activity"}',
            status_code=400,
            media_type="application/json",
        )

    log = logger.bind(
        activity_id=activity.id,
        activity_type=activity.type,
        channel_id=activity.channel_id,
    )

    log.info("bot_activity_received")

    # Process the activity
    try:
        response = await _bot_adapter.process_activity(
            activity,
            auth_header,
            _bot_instance.on_turn,
        )

        # Bot Framework expects specific status codes
        if response:
            return Response(
                content=response.body,
                status_code=response.status,
                media_type="application/json",
            )

        return Response(status_code=200)

    except Exception as e:
        log.error("bot_activity_processing_error", error=str(e))
        return Response(
            content='{"error": "Processing failed"}',
            status_code=500,
            media_type="application/json",
        )


@router.get("/api/messages/health")
async def bot_health() -> dict:
    """Health check for Bot Framework endpoint.

    Returns:
        Health status information
    """
    return {
        "status": "healthy" if _bot_adapter and _bot_instance else "not_configured",
        "bot_framework": True,
        "adapter_initialized": _bot_adapter is not None,
        "bot_initialized": _bot_instance is not None,
    }
