"""Tests for UnifiedMessageProcessor."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agent import AgentClientError, AgentTimeoutError
from src.agent.models import ChatResponse
from src.teams.common.processor import ProcessedMessage, UnifiedMessageProcessor


class TestUnifiedMessageProcessor:
    """Tests for UnifiedMessageProcessor class."""

    @pytest.fixture
    def mock_agent_client(self):
        """Create a mock agent client."""
        client = MagicMock()
        client.chat = AsyncMock()
        client.health_check = AsyncMock()
        return client

    @pytest.fixture
    def mock_session_store(self):
        """Create a mock session store."""
        store = MagicMock()
        store.get = AsyncMock(return_value=None)
        store.set = AsyncMock()
        store.delete = AsyncMock(return_value=True)
        return store

    @pytest.fixture
    def processor(self, mock_agent_client, mock_session_store):
        """Create a processor with mocked dependencies."""
        return UnifiedMessageProcessor(
            agent_client=mock_agent_client,
            session_store=mock_session_store,
        )

    @pytest.fixture
    def agent_response(self):
        """Create a sample agent response."""
        return ChatResponse(
            session_id="sess-123",
            message="Here is your answer.",
            agents_executed=["policy_agent"],
            intent="general_inquiry",
            confidence=0.9,
        )

    async def test_process_regular_message(
        self, processor, mock_agent_client, agent_response
    ):
        """Test processing a regular message."""
        mock_agent_client.chat.return_value = agent_response

        result = await processor.process(
            user_id="user-123",
            conversation_id="conv-456",
            text="What is the policy?",
        )

        assert isinstance(result, ProcessedMessage)
        assert result.text == "Here is your answer."
        assert result.is_error is False
        mock_agent_client.chat.assert_called_once()

    async def test_process_help_command(self, processor):
        """Test processing /help command."""
        result = await processor.process(
            user_id="user-123",
            conversation_id="conv-456",
            text="/help",
        )

        assert isinstance(result, ProcessedMessage)
        assert "Available Commands" in result.text
        assert "/help" in result.text
        assert "/clear" in result.text
        assert "/status" in result.text

    async def test_process_clear_command(
        self, processor, mock_session_store
    ):
        """Test processing /clear command."""
        result = await processor.process(
            user_id="user-123",
            conversation_id="conv-456",
            text="/clear",
        )

        assert isinstance(result, ProcessedMessage)
        assert "Conversation cleared" in result.text
        mock_session_store.delete.assert_called_once()

    async def test_process_status_command(
        self, processor, mock_agent_client
    ):
        """Test processing /status command."""
        mock_agent_client.health_check.return_value = {
            "status": "healthy",
            "version": "2.0.0",
        }

        result = await processor.process(
            user_id="user-123",
            conversation_id="conv-456",
            text="/status",
        )

        assert isinstance(result, ProcessedMessage)
        assert "healthy" in result.text
        assert "2.0.0" in result.text

    async def test_process_unknown_command(self, processor):
        """Test processing unknown command."""
        result = await processor.process(
            user_id="user-123",
            conversation_id="conv-456",
            text="/unknown",
        )

        assert isinstance(result, ProcessedMessage)
        assert "Unknown command" in result.text
        assert "/help" in result.text

    async def test_process_empty_text(self, processor):
        """Test processing empty message."""
        result = await processor.process(
            user_id="user-123",
            conversation_id="conv-456",
            text="",
        )

        assert isinstance(result, ProcessedMessage)
        assert "didn't catch that" in result.text

    async def test_process_timeout_error(
        self, processor, mock_agent_client
    ):
        """Test handling agent timeout."""
        mock_agent_client.chat.side_effect = AgentTimeoutError("Timeout")

        result = await processor.process(
            user_id="user-123",
            conversation_id="conv-456",
            text="What is the policy?",
        )

        assert isinstance(result, ProcessedMessage)
        assert result.is_error is True
        assert "took too long" in result.text

    async def test_process_agent_error(
        self, processor, mock_agent_client
    ):
        """Test handling agent error."""
        mock_agent_client.chat.side_effect = AgentClientError("Connection failed")

        result = await processor.process(
            user_id="user-123",
            conversation_id="conv-456",
            text="What is the policy?",
        )

        assert isinstance(result, ProcessedMessage)
        assert result.is_error is True
        assert "encountered an error" in result.text

    async def test_process_with_thread_reply(
        self, processor, mock_agent_client, mock_session_store, agent_response
    ):
        """Test processing a thread reply."""
        mock_agent_client.chat.return_value = agent_response

        result = await processor.process(
            user_id="user-123",
            conversation_id="conv-456",
            text="Follow up question",
            reply_to_id="parent-msg-789",
        )

        assert isinstance(result, ProcessedMessage)
        assert result.is_error is False

        # Verify session key includes reply_to_id
        mock_session_store.get.assert_called_once()
        call_args = mock_session_store.get.call_args
        assert "conv-456:parent-msg-789" in str(call_args)

    async def test_session_key_without_reply(self, processor):
        """Test session key without reply_to_id."""
        key = processor._build_session_key("conv-123", None)
        assert key == "conv-123"

    async def test_session_key_with_reply(self, processor):
        """Test session key with reply_to_id."""
        key = processor._build_session_key("conv-123", "parent-456")
        assert key == "conv-123:parent-456"
