"""Handler for processing Teams messages and routing to the agent."""

import structlog

from src.agent import AgentClient, AgentClientError, AgentTimeoutError
from .models import TeamsMessage, TeamsResponse

logger = structlog.get_logger(__name__)


# Available commands
COMMANDS = {
    "help": "Show available commands",
    "clear": "Clear conversation history (start fresh)",
    "status": "Check agent connection status",
}


class TeamsMessageHandler:
    """Handles incoming Teams messages and coordinates with the agent.

    This handler processes messages from Teams Outgoing Webhooks,
    extracts the user's query, sends it to the agent, and formats
    the response for Teams.

    Example:
        handler = TeamsMessageHandler(agent_client)

        # In your webhook endpoint:
        message = TeamsMessage.from_dict(request_data)
        response = await handler.handle(message)
        return response.to_dict()
    """

    def __init__(
        self,
        agent_client: AgentClient,
        timeout_message: str = "The request took too long. Please try again.",
        error_message: str = "Sorry, I encountered an error. Please try again later.",
    ):
        """Initialize the handler.

        Args:
            agent_client: Client for communicating with the agent
            timeout_message: Message to show when agent times out
            error_message: Message to show on errors
        """
        self.agent_client = agent_client
        self.timeout_message = timeout_message
        self.error_message = error_message

    async def handle(self, message: TeamsMessage) -> TeamsResponse:
        """Handle an incoming Teams message.

        Routes the message to the appropriate handler based on whether
        it's a command or a regular query.

        Args:
            message: The incoming Teams message

        Returns:
            TeamsResponse to send back to Teams
        """
        log = logger.bind(
            message_id=message.id,
            user_id=message.get_user_identifier(),
            user_name=message.from_user.name,
            conversation_id=message.conversation.id,
        )

        # Check if it's a command
        if message.is_command():
            cmd = message.get_command()
            if cmd:
                command, args = cmd
                log.info("processing_command", command=command)
                return await self._handle_command(command, args, message)

        # Regular message - send to agent
        query = message.get_clean_text()
        if not query:
            return TeamsResponse(
                text="I didn't catch that. Please mention me and ask a question."
            )

        log.info("processing_query", query_preview=query[:50])
        return await self._handle_query(query, message)

    async def _handle_command(
        self,
        command: str,
        args: str,
        message: TeamsMessage,
    ) -> TeamsResponse:
        """Handle a command message.

        Args:
            command: The command name (without /)
            args: Command arguments
            message: The original message

        Returns:
            TeamsResponse with command result
        """
        if command == "help":
            return self._build_help_response()

        elif command == "clear":
            return await self._handle_clear(message)

        elif command == "status":
            return await self._handle_status()

        else:
            return TeamsResponse(
                text=f"Unknown command: /{command}\n\nType /help for available commands."
            )

    async def _handle_query(
        self,
        query: str,
        message: TeamsMessage,
    ) -> TeamsResponse:
        """Send a query to the agent and format the response.

        Args:
            query: The user's query text
            message: The original Teams message

        Returns:
            TeamsResponse with agent's answer
        """
        log = logger.bind(
            user_id=message.get_user_identifier(),
            conversation_id=message.conversation.id,
        )

        try:
            # Send to agent
            response = await self.agent_client.chat(
                message=query,
                user_id=message.get_user_identifier(),
                # Note: For stateless, we don't pass session_id
                # Phase 3 will add session management
            )

            log.info(
                "agent_response_received",
                session_id=response.session_id,
                intent=response.intent,
                confidence=response.confidence,
            )

            # Format response for Teams
            return self._format_agent_response(response.message, response.intent)

        except AgentTimeoutError:
            log.warning("agent_timeout")
            return TeamsResponse(text=self.timeout_message)

        except AgentClientError as e:
            log.error("agent_error", error=str(e))
            return TeamsResponse(text=self.error_message)

    def _format_agent_response(
        self,
        message: str,
        intent: str | None = None,
    ) -> TeamsResponse:
        """Format the agent's response for Teams.

        Args:
            message: The agent's response text
            intent: Detected intent (optional)

        Returns:
            Formatted TeamsResponse
        """
        # For now, return as plain text
        # Future: Could add Adaptive Cards for rich responses
        return TeamsResponse(text=message)

    def _build_help_response(self) -> TeamsResponse:
        """Build the help command response."""
        lines = ["**Available Commands:**\n"]
        for cmd, description in COMMANDS.items():
            lines.append(f"- `/{cmd}` - {description}")
        lines.append("\n**Or just ask me a question!**")
        return TeamsResponse(text="\n".join(lines))

    async def _handle_clear(self, message: TeamsMessage) -> TeamsResponse:
        """Handle the /clear command.

        In stateless mode, this is a no-op since there's no session.
        Phase 3 will implement actual session clearing.

        Args:
            message: The original message

        Returns:
            Confirmation response
        """
        # In stateless mode, just acknowledge
        # Phase 3 will actually clear the session
        return TeamsResponse(
            text="Conversation cleared. Starting fresh!"
        )

    async def _handle_status(self) -> TeamsResponse:
        """Handle the /status command.

        Checks the connection to the agent.

        Returns:
            Status response
        """
        try:
            health = await self.agent_client.health_check()
            status = health.get("status", "unknown")
            version = health.get("version", "unknown")

            return TeamsResponse(
                text=f"**Agent Status:** {status}\n**Version:** {version}"
            )

        except AgentClientError as e:
            return TeamsResponse(
                text=f"**Agent Status:** Unavailable\n**Error:** {str(e)}"
            )
