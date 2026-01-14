"""Models for Teams Outgoing Webhook messages.

These models represent the JSON payload sent by Microsoft Teams
when a user mentions an Outgoing Webhook bot.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TeamsUser:
    """Represents a Teams user.

    Attributes:
        id: User's unique identifier (AAD object ID format)
        name: User's display name
        aad_object_id: Azure AD object ID (optional)
    """

    id: str
    name: str
    aad_object_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TeamsUser":
        """Create from Teams webhook payload."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unknown"),
            aad_object_id=data.get("aadObjectId"),
        )


@dataclass
class TeamsConversation:
    """Represents a Teams conversation context.

    Attributes:
        id: Conversation identifier
        conversation_type: Type (channel, personal, groupChat)
        tenant_id: Azure AD tenant ID
        name: Channel or chat name
    """

    id: str
    conversation_type: str | None = None
    tenant_id: str | None = None
    name: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TeamsConversation":
        """Create from Teams webhook payload."""
        return cls(
            id=data.get("id", ""),
            conversation_type=data.get("conversationType"),
            tenant_id=data.get("tenantId"),
            name=data.get("name"),
        )


@dataclass
class TeamsMention:
    """Represents a mention in a Teams message.

    Attributes:
        id: ID of the mentioned entity
        name: Display name
        text: The mention text as it appears in the message
    """

    id: str
    name: str
    text: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TeamsMention":
        """Create from Teams webhook payload."""
        mentioned = data.get("mentioned", {})
        return cls(
            id=mentioned.get("id", ""),
            name=mentioned.get("name", ""),
            text=data.get("text", ""),
        )


@dataclass
class TeamsMessage:
    """Represents an incoming message from Teams Outgoing Webhook.

    Attributes:
        id: Message ID
        type: Message type (usually "message")
        text: Raw message text including mentions
        timestamp: When the message was sent
        from_user: User who sent the message
        conversation: Conversation context
        recipient: The bot that was mentioned
        service_url: Teams service URL for replies
        channel_id: Channel identifier (usually "msteams")
        mentions: List of mentions in the message
        reply_to_id: ID of the message being replied to (for thread context)
    """

    id: str
    type: str
    text: str
    timestamp: datetime | None
    from_user: TeamsUser
    conversation: TeamsConversation
    recipient: TeamsUser | None = None
    service_url: str | None = None
    channel_id: str = "msteams"
    mentions: list[TeamsMention] = field(default_factory=list)
    reply_to_id: str | None = None

    # Pattern to match @mentions like <at>Bot Name</at>
    MENTION_PATTERN = re.compile(r"<at>[^<]+</at>\s*")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TeamsMessage":
        """Create from Teams webhook payload."""
        # Parse timestamp
        ts = None
        if data.get("timestamp"):
            try:
                ts_str = data["timestamp"].replace("Z", "+00:00")
                ts = datetime.fromisoformat(ts_str)
            except (ValueError, TypeError):
                pass

        # Parse mentions from entities
        mentions = []
        for entity in data.get("entities", []):
            if entity.get("type") == "mention":
                mentions.append(TeamsMention.from_dict(entity))

        # Parse recipient if present
        recipient = None
        if data.get("recipient"):
            recipient = TeamsUser.from_dict(data["recipient"])

        return cls(
            id=data.get("id", ""),
            type=data.get("type", "message"),
            text=data.get("text", ""),
            timestamp=ts,
            from_user=TeamsUser.from_dict(data.get("from", {})),
            conversation=TeamsConversation.from_dict(data.get("conversation", {})),
            recipient=recipient,
            service_url=data.get("serviceUrl"),
            channel_id=data.get("channelId", "msteams"),
            mentions=mentions,
            reply_to_id=data.get("replyToId"),
        )

    def get_clean_text(self) -> str:
        """Get message text with @mentions removed.

        Returns:
            The message text without @mention tags, stripped of whitespace
        """
        clean = self.MENTION_PATTERN.sub("", self.text)
        return clean.strip()

    def is_command(self) -> bool:
        """Check if the message is a command (starts with /).

        Returns:
            True if the clean text starts with /
        """
        return self.get_clean_text().startswith("/")

    def get_command(self) -> tuple[str, str] | None:
        """Extract command and arguments from the message.

        Returns:
            Tuple of (command, args) or None if not a command
        """
        clean = self.get_clean_text()
        if not clean.startswith("/"):
            return None

        parts = clean.split(maxsplit=1)
        command = parts[0][1:].lower()  # Remove leading /
        args = parts[1] if len(parts) > 1 else ""
        return (command, args)

    def get_user_identifier(self) -> str:
        """Get a unique identifier for the user.

        Uses AAD object ID if available, falls back to user ID.

        Returns:
            User identifier string
        """
        return self.from_user.aad_object_id or self.from_user.id

    def get_session_key(self) -> str:
        """Get a unique key for session tracking.

        Combines user ID and conversation ID for unique sessions.
        If this is a reply to a message, includes the thread root ID
        to maintain separate sessions per thread.

        Returns:
            Session key string
        """
        base_key = f"{self.get_user_identifier()}:{self.conversation.id}"
        if self.reply_to_id:
            return f"{base_key}:{self.reply_to_id}"
        return base_key

    def is_thread_reply(self) -> bool:
        """Check if this message is a reply within a thread.

        Returns:
            True if this is a reply to another message
        """
        return self.reply_to_id is not None


@dataclass
class TeamsResponse:
    """Response to send back to Teams.

    Teams Outgoing Webhooks expect a JSON response with a "text" field
    for simple messages, or an Adaptive Card attachment.

    Attributes:
        text: Plain text or markdown response
        card: Optional Adaptive Card content
    """

    text: str
    card: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to Teams response format."""
        if self.card:
            return {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": self.card,
                    }
                ],
            }
        return {"type": "message", "text": self.text}
