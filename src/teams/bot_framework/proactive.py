"""Proactive messaging support for Bot Framework.

This module provides utilities for sending unsolicited messages
to conversations where the bot has previously interacted.
"""

from typing import Callable, Dict, Optional

import structlog
from botbuilder.core import BotFrameworkAdapter, TurnContext
from botbuilder.schema import Activity, ConversationReference

logger = structlog.get_logger(__name__)


class ProactiveMessenger:
    """Send unsolicited messages to stored conversations.

    This class stores conversation references from incoming activities
    and allows sending proactive messages to those conversations later.

    Proactive messaging is useful for:
    - Sending alerts or notifications
    - Following up on long-running operations
    - Scheduled reminders

    Example:
        messenger = ProactiveMessenger(adapter)

        # Store reference when receiving a message
        await messenger.store_reference(activity)

        # Later, send a proactive message
        await messenger.send_message(conversation_id, "Task completed!")
    """

    def __init__(self, adapter: BotFrameworkAdapter):
        """Initialize the proactive messenger.

        Args:
            adapter: Bot Framework adapter for sending messages
        """
        self.adapter = adapter
        self._references: Dict[str, ConversationReference] = {}

    async def store_reference(self, activity: Activity) -> None:
        """Store a conversation reference from an activity.

        Call this when receiving any activity to enable proactive
        messaging to that conversation later.

        Args:
            activity: The incoming activity
        """
        if not activity.conversation:
            return

        conversation_id = activity.conversation.id
        reference = TurnContext.get_conversation_reference(activity)
        self._references[conversation_id] = reference

        logger.debug(
            "conversation_reference_stored",
            conversation_id=conversation_id,
        )

    async def send_message(
        self,
        conversation_id: str,
        message: str,
    ) -> bool:
        """Send a proactive message to a stored conversation.

        Args:
            conversation_id: ID of the conversation to message
            message: Text to send

        Returns:
            True if message was sent, False if conversation not found
        """
        reference = self._references.get(conversation_id)
        if not reference:
            logger.warning(
                "proactive_message_failed",
                conversation_id=conversation_id,
                reason="no_reference",
            )
            return False

        async def send_callback(turn_context: TurnContext):
            await turn_context.send_activity(message)

        try:
            await self.adapter.continue_conversation(
                reference,
                send_callback,
                reference.bot.id if reference.bot else None,
            )

            logger.info(
                "proactive_message_sent",
                conversation_id=conversation_id,
            )
            return True

        except Exception as e:
            logger.error(
                "proactive_message_error",
                conversation_id=conversation_id,
                error=str(e),
            )
            return False

    async def send_activity(
        self,
        conversation_id: str,
        activity: Activity,
    ) -> bool:
        """Send a proactive activity to a stored conversation.

        Use this for sending rich content like Adaptive Cards.

        Args:
            conversation_id: ID of the conversation to message
            activity: Activity to send

        Returns:
            True if activity was sent, False if conversation not found
        """
        reference = self._references.get(conversation_id)
        if not reference:
            logger.warning(
                "proactive_activity_failed",
                conversation_id=conversation_id,
                reason="no_reference",
            )
            return False

        async def send_callback(turn_context: TurnContext):
            await turn_context.send_activity(activity)

        try:
            await self.adapter.continue_conversation(
                reference,
                send_callback,
                reference.bot.id if reference.bot else None,
            )

            logger.info(
                "proactive_activity_sent",
                conversation_id=conversation_id,
                activity_type=activity.type,
            )
            return True

        except Exception as e:
            logger.error(
                "proactive_activity_error",
                conversation_id=conversation_id,
                error=str(e),
            )
            return False

    def has_reference(self, conversation_id: str) -> bool:
        """Check if a conversation reference exists.

        Args:
            conversation_id: ID of the conversation to check

        Returns:
            True if reference exists
        """
        return conversation_id in self._references

    def get_stored_conversations(self) -> list[str]:
        """Get list of stored conversation IDs.

        Returns:
            List of conversation IDs with stored references
        """
        return list(self._references.keys())

    def remove_reference(self, conversation_id: str) -> bool:
        """Remove a stored conversation reference.

        Args:
            conversation_id: ID of the conversation to remove

        Returns:
            True if reference was removed, False if not found
        """
        if conversation_id in self._references:
            del self._references[conversation_id]
            logger.debug(
                "conversation_reference_removed",
                conversation_id=conversation_id,
            )
            return True
        return False
