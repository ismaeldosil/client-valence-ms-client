"""Tests for TeamsMessageHandler."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agent.client import AgentClientError, AgentTimeoutError
from src.agent.models import ChatResponse, AgentExecution, AgentStatus
from src.teams.receiver.handler import TeamsMessageHandler, COMMANDS
from src.teams.receiver.models import TeamsMessage, TeamsResponse


class TestTeamsMessageHandler:
    """Tests for TeamsMessageHandler class."""

    @pytest.fixture
    def mock_agent_client(self):
        """Create a mock agent client."""
        client = MagicMock()
        client.chat = AsyncMock()
        client.health_check = AsyncMock()
        return client

    @pytest.fixture
    def handler(self, mock_agent_client):
        """Create a handler with mock client."""
        return TeamsMessageHandler(
            agent_client=mock_agent_client,
            timeout_message="Request timed out",
            error_message="An error occurred",
        )

    @pytest.fixture
    def sample_message(self):
        """Create a sample Teams message."""
        return TeamsMessage.from_dict({
            "id": "msg-123",
            "text": "<at>Bot</at> What is the vacation policy?",
            "from": {"id": "user-456", "name": "Test User", "aadObjectId": "aad-789"},
            "conversation": {"id": "conv-abc"},
        })

    @pytest.fixture
    def command_message(self):
        """Create a command message."""
        return TeamsMessage.from_dict({
            "id": "msg-cmd",
            "text": "<at>Bot</at> /help",
            "from": {"id": "user-1", "name": "User"},
            "conversation": {"id": "conv-1"},
        })

    @pytest.fixture
    def agent_response(self):
        """Create a sample agent response."""
        return ChatResponse(
            session_id="sess-123",
            message="You have 15 vacation days per year.",
            agents_executed=[
                AgentExecution(
                    agent_name="intent",
                    display_name="Intent Classifier",
                    status=AgentStatus.COMPLETED,
                    duration_ms=50,
                )
            ],
            intent="hr_inquiry",
            confidence=0.95,
        )

    async def test_handle_regular_message(
        self, handler, mock_agent_client, sample_message, agent_response
    ):
        """Test handling a regular query message."""
        mock_agent_client.chat.return_value = agent_response

        response = await handler.handle(sample_message)

        assert isinstance(response, TeamsResponse)
        assert response.text == "You have 15 vacation days per year."
        mock_agent_client.chat.assert_called_once_with(
            message="What is the vacation policy?",
            user_id="aad-789",
        )

    async def test_handle_help_command(self, handler, command_message):
        """Test handling /help command."""
        response = await handler.handle(command_message)

        assert isinstance(response, TeamsResponse)
        assert "Available Commands" in response.text
        for cmd in COMMANDS:
            assert f"/{cmd}" in response.text

    async def test_handle_clear_command(self, handler):
        """Test handling /clear command."""
        message = TeamsMessage.from_dict({
            "id": "msg-1",
            "text": "<at>Bot</at> /clear",
            "from": {"id": "u1", "name": "User"},
            "conversation": {"id": "c1"},
        })

        response = await handler.handle(message)

        assert "cleared" in response.text.lower()

    async def test_handle_status_command_healthy(self, handler, mock_agent_client):
        """Test handling /status command when agent is healthy."""
        mock_agent_client.health_check.return_value = {
            "status": "healthy",
            "version": "2.0.0",
        }

        message = TeamsMessage.from_dict({
            "id": "msg-1",
            "text": "<at>Bot</at> /status",
            "from": {"id": "u1", "name": "User"},
            "conversation": {"id": "c1"},
        })

        response = await handler.handle(message)

        assert "healthy" in response.text
        assert "2.0.0" in response.text

    async def test_handle_status_command_error(self, handler, mock_agent_client):
        """Test handling /status command when agent is unavailable."""
        mock_agent_client.health_check.side_effect = AgentClientError("Connection refused")

        message = TeamsMessage.from_dict({
            "id": "msg-1",
            "text": "<at>Bot</at> /status",
            "from": {"id": "u1", "name": "User"},
            "conversation": {"id": "c1"},
        })

        response = await handler.handle(message)

        assert "Unavailable" in response.text

    async def test_handle_unknown_command(self, handler):
        """Test handling unknown command."""
        message = TeamsMessage.from_dict({
            "id": "msg-1",
            "text": "<at>Bot</at> /unknown",
            "from": {"id": "u1", "name": "User"},
            "conversation": {"id": "c1"},
        })

        response = await handler.handle(message)

        assert "Unknown command" in response.text
        assert "/unknown" in response.text

    async def test_handle_empty_message(self, handler):
        """Test handling message with only mention (no text)."""
        message = TeamsMessage.from_dict({
            "id": "msg-1",
            "text": "<at>Bot</at>",
            "from": {"id": "u1", "name": "User"},
            "conversation": {"id": "c1"},
        })

        response = await handler.handle(message)

        assert "didn't catch that" in response.text.lower()

    async def test_handle_agent_timeout(
        self, handler, mock_agent_client, sample_message
    ):
        """Test handling agent timeout."""
        mock_agent_client.chat.side_effect = AgentTimeoutError("Timeout")

        response = await handler.handle(sample_message)

        assert response.text == "Request timed out"

    async def test_handle_agent_error(
        self, handler, mock_agent_client, sample_message
    ):
        """Test handling agent error."""
        mock_agent_client.chat.side_effect = AgentClientError("Server error")

        response = await handler.handle(sample_message)

        assert response.text == "An error occurred"

    async def test_format_agent_response(self, handler, agent_response):
        """Test formatting agent response."""
        response = handler._format_agent_response(
            agent_response.message,
            agent_response.intent,
        )

        assert isinstance(response, TeamsResponse)
        assert response.text == agent_response.message

    def test_build_help_response(self, handler):
        """Test building help response."""
        response = handler._build_help_response()

        assert "Available Commands" in response.text
        assert "/help" in response.text
        assert "/clear" in response.text
        assert "/status" in response.text

    async def test_handle_command_case_insensitive(self, handler):
        """Test that commands are case-insensitive."""
        message = TeamsMessage.from_dict({
            "id": "msg-1",
            "text": "<at>Bot</at> /HELP",
            "from": {"id": "u1", "name": "User"},
            "conversation": {"id": "c1"},
        })

        response = await handler.handle(message)

        assert "Available Commands" in response.text
