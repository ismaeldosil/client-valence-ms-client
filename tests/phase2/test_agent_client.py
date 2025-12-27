"""Tests for AgentClient."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from src.agent.client import (
    AgentClient,
    AgentClientError,
    AgentTimeoutError,
    AgentConnectionError,
    AgentAPIError,
)
from src.agent.models import ChatResponse, AgentStatus


class TestAgentClient:
    """Tests for AgentClient class."""

    @pytest.fixture
    def client(self):
        """Create an agent client."""
        return AgentClient(
            base_url="http://localhost:8000",
            api_key="test-key",
            timeout=5.0,
            max_retries=2,
        )

    @pytest.fixture
    def chat_response_data(self):
        """Sample chat response data."""
        return {
            "session_id": "sess-123",
            "message": "Here are the suppliers for heat treatment.",
            "agents_executed": [
                {
                    "agent_name": "intent_classifier",
                    "display_name": "Intent Classifier",
                    "status": "completed",
                    "duration_ms": 50,
                    "output": {"intent": "supplier_search"},
                }
            ],
            "intent": "supplier_search",
            "confidence": 0.95,
            "requires_approval": False,
        }

    async def test_init(self, client):
        """Test client initialization."""
        assert client.base_url == "http://localhost:8000"
        assert client.api_key == "test-key"
        assert client.timeout == 5.0
        assert client.max_retries == 2

    async def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from base URL."""
        client = AgentClient(base_url="http://localhost:8000/")
        assert client.base_url == "http://localhost:8000"

    async def test_context_manager(self, client):
        """Test async context manager."""
        async with client:
            assert client._client is not None
        assert client._client is None

    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy", "version": "2.0.0"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_ensure.return_value = mock_client

            result = await client.health_check()

            assert result == {"status": "healthy", "version": "2.0.0"}
            mock_client.get.assert_called_once_with("/health")

    @pytest.mark.asyncio
    async def test_health_check_connection_error(self, client):
        """Test health check with connection error."""
        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("Connection refused")
            mock_ensure.return_value = mock_client

            with pytest.raises(AgentConnectionError, match="Failed to connect"):
                await client.health_check()

    @pytest.mark.asyncio
    async def test_chat_success(self, client, chat_response_data):
        """Test successful chat request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = chat_response_data

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_ensure.return_value = mock_client

            result = await client.chat(
                message="Find suppliers for heat treatment",
                session_id="sess-123",
                user_id="user-456",
            )

            assert isinstance(result, ChatResponse)
            assert result.session_id == "sess-123"
            assert result.message == "Here are the suppliers for heat treatment."
            assert result.intent == "supplier_search"
            assert result.confidence == 0.95

    @pytest.mark.asyncio
    async def test_chat_timeout(self, client):
        """Test chat request timeout."""
        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Timeout")
            mock_ensure.return_value = mock_client

            with pytest.raises(AgentTimeoutError, match="timed out"):
                await client.chat(message="Test")

    @pytest.mark.asyncio
    async def test_chat_connection_error(self, client):
        """Test chat with connection error."""
        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_ensure.return_value = mock_client

            with pytest.raises(AgentConnectionError, match="Failed to connect"):
                await client.chat(message="Test")

    @pytest.mark.asyncio
    async def test_chat_validation_error(self, client):
        """Test chat with validation error (422)."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.json.return_value = {"detail": "Message too long"}

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_ensure.return_value = mock_client

            with pytest.raises(AgentAPIError) as exc_info:
                await client.chat(message="Test")

            assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_retries_on_timeout(self, client):
        """Test that chat retries on timeout."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "session_id": "sess-123",
            "message": "Success after retry",
            "agents_executed": [],
        }

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TimeoutException("Timeout")
            return mock_response

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_ensure.return_value = mock_client

            result = await client.chat(message="Test")

            assert result.message == "Success after retry"
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_get_session_success(self, client):
        """Test successful get session."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "session_id": "sess-123",
            "status": "active",
            "created_at": "2024-01-15T10:00:00Z",
            "last_activity": "2024-01-15T10:30:00Z",
            "message_count": 5,
            "messages": [],
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_ensure.return_value = mock_client

            result = await client.get_session("sess-123")

            assert result.session_id == "sess-123"
            assert result.message_count == 5

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client):
        """Test get session when not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_ensure.return_value = mock_client

            with pytest.raises(AgentAPIError) as exc_info:
                await client.get_session("nonexistent")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_session_success(self, client):
        """Test successful delete session."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.delete.return_value = mock_response
            mock_ensure.return_value = mock_client

            result = await client.delete_session("sess-123")

            assert result is True

    async def test_close(self, client):
        """Test closing the client."""
        async with client:
            assert client._client is not None

        assert client._client is None
