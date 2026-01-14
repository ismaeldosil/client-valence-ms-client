"""Unified message processor for Teams integrations.

This module provides a shared message processing layer that can be used
by both Outgoing Webhooks and Bot Framework integrations.
"""

from dataclasses import dataclass
from typing import Optional

import structlog

from src.agent import AgentClient, AgentClientError, AgentTimeoutError
from src.session import SessionStore

logger = structlog.get_logger(__name__)


# Available commands
COMMANDS = {
    "help": "Show available commands",
    "clear": "Clear conversation history (start fresh)",
    "status": "Check agent connection status",
}


@dataclass
class ProcessedMessage:
    """Result of processing a message."""

    text: str
    is_error: bool = False


class UnifiedMessageProcessor:
    """Shared message processing for both webhook and bot modes.

    This processor handles:
    - Command routing (/help, /clear, /status)
    - Session lookup and storage
    - Agent communication
    - Error handling

    Both TeamsMessageHandler (webhook) and ValerieBot (bot framework)
    delegate to this processor for consistent behavior.
    """

    def __init__(
        self,
        agent_client: AgentClient,
        session_store: Optional[SessionStore] = None,
        timeout_message: str = "The request took too long. Please try again.",
        error_message: str = "Sorry, I encountered an error. Please try again later.",
    ):
        """Initialize the processor.

        Args:
            agent_client: Client for communicating with the agent
            session_store: Optional session store for conversation continuity
            timeout_message: Message to show when agent times out
            error_message: Message to show on errors
        """
        self.agent_client = agent_client
        self.session_store = session_store
        self.timeout_message = timeout_message
        self.error_message = error_message

    async def process(
        self,
        user_id: str,
        conversation_id: str,
        text: str,
        reply_to_id: Optional[str] = None,
        user_name: Optional[str] = None,
    ) -> ProcessedMessage:
        """Process a message and return the response.

        This is the main entry point for processing messages from
        any Teams integration (webhook or bot framework).

        Args:
            user_id: Unique user identifier
            conversation_id: Conversation/channel identifier
            text: Message text (already cleaned of @mentions if needed)
            reply_to_id: ID of parent message for thread context
            user_name: Optional user display name for logging

        Returns:
            ProcessedMessage with response text
        """
        log = logger.bind(
            user_id=user_id,
            conversation_id=conversation_id,
            reply_to_id=reply_to_id,
            user_name=user_name,
        )

        # Check if it's a command
        if text.startswith("/"):
            return await self._handle_command(text, user_id, conversation_id, log)

        # Empty text check
        if not text.strip():
            return ProcessedMessage(
                text="I didn't catch that. Please ask a question."
            )

        # Regular message - send to agent
        log.info("processing_query", query_preview=text[:50])
        return await self._handle_query(
            query=text,
            user_id=user_id,
            conversation_id=conversation_id,
            reply_to_id=reply_to_id,
            log=log,
        )

    async def _handle_command(
        self,
        text: str,
        user_id: str,
        conversation_id: str,
        log: structlog.BoundLogger,
    ) -> ProcessedMessage:
        """Handle a command message.

        Args:
            text: Full message text starting with /
            user_id: User identifier
            conversation_id: Conversation identifier
            log: Bound logger

        Returns:
            ProcessedMessage with command result
        """
        parts = text.split(maxsplit=1)
        command = parts[0][1:].lower()  # Remove leading /
        args = parts[1] if len(parts) > 1 else ""

        log.info("processing_command", command=command)

        if command == "help":
            return self._build_help_response()

        elif command == "clear":
            return await self._handle_clear(user_id, conversation_id, log)

        elif command == "status":
            return await self._handle_status()

        else:
            return ProcessedMessage(
                text=f"Unknown command: /{command}\n\nType /help for available commands."
            )

    async def _handle_query(
        self,
        query: str,
        user_id: str,
        conversation_id: str,
        reply_to_id: Optional[str],
        log: structlog.BoundLogger,
    ) -> ProcessedMessage:
        """Send a query to the agent and return the response.

        Args:
            query: The user's query text
            user_id: User identifier
            conversation_id: Conversation identifier
            reply_to_id: Thread parent ID for session key
            log: Bound logger

        Returns:
            ProcessedMessage with agent's answer
        """
        # Build session key with thread awareness
        session_key_conv = self._build_session_key(
            conversation_id, reply_to_id
        )

        # Look up existing session
        session_id = None
        if self.session_store:
            try:
                session_data = await self.session_store.get(user_id, session_key_conv)
                if session_data:
                    session_id = session_data.session_id
                    log.debug(
                        "session_found",
                        session_id=session_id,
                        message_count=session_data.message_count,
                    )
            except Exception as e:
                log.warning("session_lookup_error", error=str(e))

        try:
            # Send to agent with session_id if available
            response = await self.agent_client.chat(
                message=query,
                user_id=user_id,
                session_id=session_id,
            )

            log.info(
                "agent_response_received",
                session_id=response.session_id,
                intent=response.intent,
                confidence=response.confidence,
            )

            # Store the session_id from response for future messages
            if self.session_store and response.session_id:
                try:
                    if not session_id or session_id != response.session_id:
                        await self.session_store.set(
                            user_id, session_key_conv, response.session_id
                        )
                        log.debug("session_stored", session_id=response.session_id)
                except Exception as e:
                    log.warning("session_store_error", error=str(e))

            return ProcessedMessage(text=response.message)

        except AgentTimeoutError:
            log.warning("agent_timeout")
            return ProcessedMessage(text=self.timeout_message, is_error=True)

        except AgentClientError as e:
            log.error("agent_error", error=str(e))
            return ProcessedMessage(text=self.error_message, is_error=True)

    def _build_session_key(
        self,
        conversation_id: str,
        reply_to_id: Optional[str] = None,
    ) -> str:
        """Build session key with thread awareness.

        Args:
            conversation_id: Conversation identifier
            reply_to_id: Thread parent ID (optional)

        Returns:
            Session key string
        """
        if reply_to_id:
            return f"{conversation_id}:{reply_to_id}"
        return conversation_id

    def _build_help_response(self) -> ProcessedMessage:
        """Build the help command response."""
        lines = ["**Available Commands:**\n"]
        for cmd, description in COMMANDS.items():
            lines.append(f"- `/{cmd}` - {description}")
        lines.append("\n**Or just ask me a question!**")
        return ProcessedMessage(text="\n".join(lines))

    async def _handle_clear(
        self,
        user_id: str,
        conversation_id: str,
        log: structlog.BoundLogger,
    ) -> ProcessedMessage:
        """Handle the /clear command.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            log: Bound logger

        Returns:
            Confirmation response
        """
        if self.session_store:
            try:
                deleted = await self.session_store.delete(user_id, conversation_id)
                if deleted:
                    log.info("session_cleared")
            except Exception as e:
                log.warning("session_clear_error", error=str(e))

        return ProcessedMessage(text="Conversation cleared. Starting fresh!")

    async def _handle_status(self) -> ProcessedMessage:
        """Handle the /status command.

        Returns:
            Status response
        """
        try:
            health = await self.agent_client.health_check()
            status = health.get("status", "unknown")
            version = health.get("version", "unknown")

            return ProcessedMessage(
                text=f"**Agent Status:** {status}\n**Version:** {version}"
            )

        except AgentClientError as e:
            return ProcessedMessage(
                text=f"**Agent Status:** Unavailable\n**Error:** {str(e)}",
                is_error=True,
            )
