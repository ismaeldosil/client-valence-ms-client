"""Models for Agent API requests and responses.

Based on the Valerie Supplier Chatbot API v2.2.0 OpenAPI specification.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentStatus(str, Enum):
    """Status of an agent execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"


class SessionStatus(str, Enum):
    """Status of a chat session."""

    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ERROR = "error"


class MessageRole(str, Enum):
    """Role of message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatRequest:
    """Request to send a chat message to the agent.

    Attributes:
        message: The user's message (required, 1-5000 chars)
        session_id: Existing session ID for conversation continuity
        user_id: User identifier for tracking
    """

    message: str
    session_id: str | None = None
    user_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API request."""
        data: dict[str, Any] = {"message": self.message}
        if self.session_id:
            data["session_id"] = self.session_id
        if self.user_id:
            data["user_id"] = self.user_id
        return data


@dataclass
class AgentExecution:
    """Details of an agent's execution in the pipeline.

    Attributes:
        agent_name: Internal name of the agent
        display_name: Human-readable name
        status: Execution status
        duration_ms: Execution time in milliseconds
        output: Agent output data
    """

    agent_name: str
    display_name: str
    status: AgentStatus
    duration_ms: int = 0
    output: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentExecution":
        """Create from API response dictionary."""
        return cls(
            agent_name=data["agent_name"],
            display_name=data["display_name"],
            status=AgentStatus(data["status"]),
            duration_ms=data.get("duration_ms", 0),
            output=data.get("output", {}),
        )


@dataclass
class ChatResponse:
    """Response from the chat endpoint.

    Attributes:
        session_id: Session identifier for conversation continuity
        message: The agent's response message
        agents_executed: List of agents that processed the request
        intent: Detected user intent
        confidence: Confidence score (0-1)
        requires_approval: Whether action requires user approval
    """

    session_id: str
    message: str
    agents_executed: list[AgentExecution] = field(default_factory=list)
    intent: str | None = None
    confidence: float | None = None
    requires_approval: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatResponse":
        """Create from API response dictionary."""
        agents = [
            AgentExecution.from_dict(a) for a in data.get("agents_executed", [])
        ]
        return cls(
            session_id=data["session_id"],
            message=data["message"],
            agents_executed=agents,
            intent=data.get("intent"),
            confidence=data.get("confidence"),
            requires_approval=data.get("requires_approval", False),
        )


@dataclass
class Message:
    """A single chat message in session history.

    Attributes:
        role: Who sent the message (user/assistant/system)
        content: Message content
        timestamp: When the message was sent
    """

    role: MessageRole
    content: str
    timestamp: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create from API response dictionary."""
        ts = None
        if data.get("timestamp"):
            ts = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=ts,
        )


@dataclass
class SessionResponse:
    """Response with session details.

    Attributes:
        session_id: Session identifier
        status: Session status
        created_at: When session was created
        last_activity: Last activity timestamp
        message_count: Number of messages in session
        messages: List of messages in session
    """

    session_id: str
    status: SessionStatus
    created_at: datetime
    last_activity: datetime
    message_count: int
    messages: list[Message] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionResponse":
        """Create from API response dictionary."""
        messages = [Message.from_dict(m) for m in data.get("messages", [])]
        return cls(
            session_id=data["session_id"],
            status=SessionStatus(data["status"]),
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ),
            last_activity=datetime.fromisoformat(
                data["last_activity"].replace("Z", "+00:00")
            ),
            message_count=data["message_count"],
            messages=messages,
        )
