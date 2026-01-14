"""Bot Framework adapter configuration.

This module provides factory functions for creating and configuring
the Bot Framework adapter with proper authentication.
"""

from typing import Optional

import structlog
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
)

logger = structlog.get_logger(__name__)


def create_bot_adapter(
    app_id: Optional[str] = None,
    app_password: Optional[str] = None,
) -> BotFrameworkAdapter:
    """Create and configure a Bot Framework adapter.

    The adapter handles authentication and message routing for
    Bot Framework activities.

    Args:
        app_id: Microsoft App ID from Azure Bot registration
        app_password: Microsoft App Password (client secret)

    Returns:
        Configured BotFrameworkAdapter

    Note:
        If app_id and app_password are not provided, the adapter
        will work in "no auth" mode (useful for local testing
        with Bot Framework Emulator).
    """
    settings = BotFrameworkAdapterSettings(
        app_id=app_id or "",
        app_password=app_password or "",
    )

    adapter = BotFrameworkAdapter(settings)

    # Add error handler
    async def on_error(context, error):
        logger.error(
            "bot_adapter_error",
            error=str(error),
            error_type=type(error).__name__,
        )

        # Send error message to user
        await context.send_activity(
            "Sorry, I encountered an error. Please try again."
        )

    adapter.on_turn_error = on_error

    logger.info(
        "bot_adapter_created",
        has_credentials=bool(app_id and app_password),
    )

    return adapter
