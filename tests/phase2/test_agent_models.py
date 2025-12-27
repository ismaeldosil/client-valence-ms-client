"""Tests for Agent API models."""

import pytest
from datetime import datetime, timezone

from src.agent.models import (
    AgentStatus,
    SessionStatus,
    MessageRole,
    ChatRequest,
    AgentExecution,
    ChatResponse,
    Message,
    SessionResponse,
)


class TestEnums:
    """Tests for enum types."""

    def test_agent_status_values(self):
        """Test AgentStatus enum values."""
        assert AgentStatus.PENDING == "pending"
        assert AgentStatus.RUNNING == "running"
        assert AgentStatus.COMPLETED == "completed"
        assert AgentStatus.ERROR == "error"
        assert AgentStatus.SKIPPED == "skipped"

    def test_session_status_values(self):
        """Test SessionStatus enum values."""
        assert SessionStatus.ACTIVE == "active"
        assert SessionStatus.COMPLETED == "completed"
        assert SessionStatus.EXPIRED == "expired"
        assert SessionStatus.ERROR == "error"

    def test_message_role_values(self):
        """Test MessageRole enum values."""
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"


class TestChatRequest:
    """Tests for ChatRequest dataclass."""

    def test_to_dict_minimal(self):
        """Test conversion with only required field."""
        request = ChatRequest(message="Hello")
        result = request.to_dict()

        assert result == {"message": "Hello"}

    def test_to_dict_with_session_id(self):
        """Test conversion with session_id."""
        request = ChatRequest(message="Hello", session_id="sess-123")
        result = request.to_dict()

        assert result == {"message": "Hello", "session_id": "sess-123"}

    def test_to_dict_with_user_id(self):
        """Test conversion with user_id."""
        request = ChatRequest(message="Hello", user_id="user-456")
        result = request.to_dict()

        assert result == {"message": "Hello", "user_id": "user-456"}

    def test_to_dict_full(self):
        """Test conversion with all fields."""
        request = ChatRequest(
            message="Hello",
            session_id="sess-123",
            user_id="user-456",
        )
        result = request.to_dict()

        assert result == {
            "message": "Hello",
            "session_id": "sess-123",
            "user_id": "user-456",
        }


class TestAgentExecution:
    """Tests for AgentExecution dataclass."""

    def test_from_dict_full(self):
        """Test creating from full dictionary."""
        data = {
            "agent_name": "intent_classifier",
            "display_name": "Intent Classifier",
            "status": "completed",
            "duration_ms": 50,
            "output": {"intent": "greeting", "confidence": 0.95},
        }
        execution = AgentExecution.from_dict(data)

        assert execution.agent_name == "intent_classifier"
        assert execution.display_name == "Intent Classifier"
        assert execution.status == AgentStatus.COMPLETED
        assert execution.duration_ms == 50
        assert execution.output == {"intent": "greeting", "confidence": 0.95}

    def test_from_dict_minimal(self):
        """Test creating from minimal dictionary."""
        data = {
            "agent_name": "test",
            "display_name": "Test",
            "status": "pending",
        }
        execution = AgentExecution.from_dict(data)

        assert execution.agent_name == "test"
        assert execution.status == AgentStatus.PENDING
        assert execution.duration_ms == 0
        assert execution.output == {}


class TestChatResponse:
    """Tests for ChatResponse dataclass."""

    def test_from_dict_full(self):
        """Test creating from full dictionary."""
        data = {
            "session_id": "sess-123",
            "message": "Hello! How can I help?",
            "agents_executed": [
                {
                    "agent_name": "intent",
                    "display_name": "Intent",
                    "status": "completed",
                    "duration_ms": 30,
                    "output": {},
                }
            ],
            "intent": "greeting",
            "confidence": 0.98,
            "requires_approval": True,
        }
        response = ChatResponse.from_dict(data)

        assert response.session_id == "sess-123"
        assert response.message == "Hello! How can I help?"
        assert len(response.agents_executed) == 1
        assert response.agents_executed[0].agent_name == "intent"
        assert response.intent == "greeting"
        assert response.confidence == 0.98
        assert response.requires_approval is True

    def test_from_dict_minimal(self):
        """Test creating from minimal dictionary."""
        data = {
            "session_id": "sess-123",
            "message": "Response",
        }
        response = ChatResponse.from_dict(data)

        assert response.session_id == "sess-123"
        assert response.message == "Response"
        assert response.agents_executed == []
        assert response.intent is None
        assert response.confidence is None
        assert response.requires_approval is False


class TestMessage:
    """Tests for Message dataclass."""

    def test_from_dict_with_timestamp(self):
        """Test creating message with timestamp."""
        data = {
            "role": "user",
            "content": "What is the policy?",
            "timestamp": "2024-01-15T10:30:00Z",
        }
        message = Message.from_dict(data)

        assert message.role == MessageRole.USER
        assert message.content == "What is the policy?"
        assert message.timestamp is not None

    def test_from_dict_without_timestamp(self):
        """Test creating message without timestamp."""
        data = {
            "role": "assistant",
            "content": "Here is the information.",
        }
        message = Message.from_dict(data)

        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Here is the information."
        assert message.timestamp is None

    def test_from_dict_system_role(self):
        """Test creating system message."""
        data = {
            "role": "system",
            "content": "You are a helpful assistant.",
        }
        message = Message.from_dict(data)

        assert message.role == MessageRole.SYSTEM


class TestSessionResponse:
    """Tests for SessionResponse dataclass."""

    def test_from_dict_full(self):
        """Test creating from full dictionary."""
        data = {
            "session_id": "sess-123",
            "status": "active",
            "created_at": "2024-01-15T10:00:00Z",
            "last_activity": "2024-01-15T10:30:00Z",
            "message_count": 5,
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        }
        session = SessionResponse.from_dict(data)

        assert session.session_id == "sess-123"
        assert session.status == SessionStatus.ACTIVE
        assert session.message_count == 5
        assert len(session.messages) == 2
        assert session.messages[0].role == MessageRole.USER
        assert session.messages[1].role == MessageRole.ASSISTANT

    def test_from_dict_empty_messages(self):
        """Test creating session with no messages."""
        data = {
            "session_id": "sess-123",
            "status": "active",
            "created_at": "2024-01-15T10:00:00Z",
            "last_activity": "2024-01-15T10:00:00Z",
            "message_count": 0,
        }
        session = SessionResponse.from_dict(data)

        assert session.messages == []
        assert session.message_count == 0
