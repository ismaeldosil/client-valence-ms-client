"""
Notification Models.

Data models for the notification service.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class Priority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Notification delivery status."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


@dataclass
class Notification:
    """
    Represents a notification to be sent to Teams.

    Attributes:
        id: Unique notification identifier
        channel: Target channel name
        message: Notification message
        title: Optional title
        card_type: Type of card (alert, info, report) or None for text
        priority: Priority level
        metadata: Additional data for card templates
        status: Delivery status
        created_at: Creation timestamp
        sent_at: Delivery timestamp
        error: Error message if failed
    """

    channel: str
    message: str
    title: Optional[str] = None
    card_type: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    error: Optional[str] = None

    def mark_sent(self) -> None:
        """Mark notification as successfully sent."""
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now()

    def mark_failed(self, error: str) -> None:
        """Mark notification as failed with error message."""
        self.status = NotificationStatus.FAILED
        self.error = error

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "channel": self.channel,
            "message": self.message,
            "title": self.title,
            "card_type": self.card_type,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "error": self.error,
        }
