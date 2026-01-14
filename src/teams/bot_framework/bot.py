"""Bot Framework bot implementation.

This module provides the ValerieBot class that handles incoming
Bot Framework activities from Microsoft Teams.
"""

from typing import TYPE_CHECKING, Optional

import structlog
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity, ChannelAccount

if TYPE_CHECKING:
    from src.teams.common import UnifiedMessageProcessor
    from .proactive import ProactiveMessenger

logger = structlog.get_logger(__name__)


class ValerieBot(ActivityHandler):
    """Bot Framework activity handler for Valerie.

    This bot receives all messages in conversations where it's a member,
    including thread replies (no @mention required). It delegates message
    processing to the UnifiedMessageProcessor for consistent behavior
    with the webhook integration.

    Features enabled by Bot Framework:
    - Automatic thread reply handling
    - Proactive messaging
    - Interactive Adaptive Card actions
    - No timeout constraints

    Example:
        processor = UnifiedMessageProcessor(agent_client, session_store)
        bot = ValerieBot(processor)

        # In your /api/messages endpoint:
        await adapter.process_activity(activity, auth_header, bot.on_turn)
    """

    def __init__(
        self,
        processor: "UnifiedMessageProcessor",
        proactive_messenger: Optional["ProactiveMessenger"] = None,
    ):
        """Initialize the bot.

        Args:
            processor: Unified message processor for handling queries
            proactive_messenger: Optional proactive messenger for storing
                                conversation references
        """
        super().__init__()
        self.processor = processor
        self.proactive_messenger = proactive_messenger

    async def on_turn(self, turn_context: TurnContext) -> None:
        """Handle each turn (incoming activity).

        This is called for every activity received by the bot.
        Store conversation references for proactive messaging.

        Args:
            turn_context: Context for the current turn
        """
        # Store conversation reference for proactive messaging
        if self.proactive_messenger:
            await self.proactive_messenger.store_reference(turn_context.activity)

        await super().on_turn(turn_context)

    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """Handle incoming message activities.

        This method receives ALL messages in conversations where the bot
        is a member, including thread replies without @mentions.

        Args:
            turn_context: Context for the current turn
        """
        activity = turn_context.activity

        # Extract user information
        user_id = self._get_user_id(activity)
        user_name = activity.from_property.name if activity.from_property else None

        log = logger.bind(
            activity_id=activity.id,
            user_id=user_id,
            user_name=user_name,
            conversation_id=activity.conversation.id if activity.conversation else None,
            reply_to_id=activity.reply_to_id,
            channel_id=activity.channel_id,
        )

        log.info("bot_message_received", text_preview=activity.text[:50] if activity.text else "")

        # Get text (Bot Framework already strips @mentions for us in Teams)
        text = activity.text or ""

        # Remove bot mention if present (Teams sometimes includes it)
        text = self._remove_bot_mention(text, activity)

        if not text.strip():
            await turn_context.send_activity(
                "I didn't catch that. Please ask a question."
            )
            return

        # Process message through unified processor
        result = await self.processor.process(
            user_id=user_id,
            conversation_id=activity.conversation.id if activity.conversation else "",
            text=text,
            reply_to_id=activity.reply_to_id,
            user_name=user_name,
        )

        log.info("bot_response_sent", is_error=result.is_error)

        # Send response
        await turn_context.send_activity(result.text)

    async def on_conversation_update_activity(self, turn_context: TurnContext) -> None:
        """Handle conversation update activities.

        Called when members are added/removed from a conversation
        or when the bot is added to a team.

        Args:
            turn_context: Context for the current turn
        """
        activity = turn_context.activity

        # Check if bot was added to the conversation
        if activity.members_added:
            for member in activity.members_added:
                if member.id != activity.recipient.id:
                    # A user was added, not the bot
                    continue

                # Bot was added - send welcome message
                logger.info(
                    "bot_added_to_conversation",
                    conversation_id=activity.conversation.id if activity.conversation else None,
                )

                await turn_context.send_activity(
                    "Hello! I'm Valerie, your AI assistant. "
                    "Ask me anything or type /help for available commands."
                )

    async def on_invoke_activity(self, turn_context: TurnContext):
        """Handle invoke activities (Adaptive Card actions).

        Called when a user clicks a button or submits a form
        in an Adaptive Card.

        Args:
            turn_context: Context for the current turn

        Returns:
            InvokeResponse for the activity
        """
        activity = turn_context.activity

        logger.info(
            "bot_invoke_received",
            name=activity.name,
            value=activity.value,
        )

        # Handle Adaptive Card submit actions
        if activity.name == "adaptiveCard/action":
            data = activity.value or {}
            action = data.get("action")

            if action:
                # Process the action
                await turn_context.send_activity(
                    f"Action '{action}' received. Processing..."
                )

        # Return success response
        from botbuilder.schema import InvokeResponse
        return InvokeResponse(status=200)

    def _get_user_id(self, activity: Activity) -> str:
        """Extract user ID from activity.

        Prefers AAD object ID for Teams users.

        Args:
            activity: The incoming activity

        Returns:
            User identifier string
        """
        if activity.from_property:
            # Prefer AAD object ID (more stable for Teams)
            if activity.from_property.aad_object_id:
                return activity.from_property.aad_object_id
            return activity.from_property.id or ""
        return ""

    def _remove_bot_mention(self, text: str, activity: Activity) -> str:
        """Remove bot @mention from text if present.

        Teams usually strips this, but sometimes includes it.

        Args:
            text: Message text
            activity: The incoming activity

        Returns:
            Text with bot mention removed
        """
        if not activity.entities:
            return text

        for entity in activity.entities:
            if entity.type == "mention":
                mentioned = entity.additional_properties.get("mentioned", {})
                if mentioned.get("id") == activity.recipient.id:
                    # This is a mention of the bot
                    mention_text = entity.additional_properties.get("text", "")
                    if mention_text:
                        text = text.replace(mention_text, "").strip()

        return text
