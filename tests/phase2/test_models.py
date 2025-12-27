"""Tests for Teams receiver models."""

import pytest
from datetime import datetime, timezone

from src.teams.receiver.models import (
    TeamsUser,
    TeamsConversation,
    TeamsMention,
    TeamsMessage,
    TeamsResponse,
)


class TestTeamsUser:
    """Tests for TeamsUser dataclass."""

    def test_from_dict_full(self):
        """Test creating user with all fields."""
        data = {
            "id": "user-123",
            "name": "John Doe",
            "aadObjectId": "aad-456",
        }
        user = TeamsUser.from_dict(data)

        assert user.id == "user-123"
        assert user.name == "John Doe"
        assert user.aad_object_id == "aad-456"

    def test_from_dict_minimal(self):
        """Test creating user with minimal fields."""
        data = {"id": "user-123"}
        user = TeamsUser.from_dict(data)

        assert user.id == "user-123"
        assert user.name == "Unknown"
        assert user.aad_object_id is None

    def test_from_dict_empty(self):
        """Test creating user from empty dict."""
        user = TeamsUser.from_dict({})

        assert user.id == ""
        assert user.name == "Unknown"
        assert user.aad_object_id is None


class TestTeamsConversation:
    """Tests for TeamsConversation dataclass."""

    def test_from_dict_full(self):
        """Test creating conversation with all fields."""
        data = {
            "id": "conv-123",
            "conversationType": "channel",
            "tenantId": "tenant-456",
            "name": "General",
        }
        conv = TeamsConversation.from_dict(data)

        assert conv.id == "conv-123"
        assert conv.conversation_type == "channel"
        assert conv.tenant_id == "tenant-456"
        assert conv.name == "General"

    def test_from_dict_minimal(self):
        """Test creating conversation with minimal fields."""
        data = {"id": "conv-123"}
        conv = TeamsConversation.from_dict(data)

        assert conv.id == "conv-123"
        assert conv.conversation_type is None
        assert conv.tenant_id is None
        assert conv.name is None


class TestTeamsMention:
    """Tests for TeamsMention dataclass."""

    def test_from_dict(self):
        """Test creating mention from Teams entity."""
        data = {
            "type": "mention",
            "mentioned": {
                "id": "bot-123",
                "name": "MyBot",
            },
            "text": "<at>MyBot</at>",
        }
        mention = TeamsMention.from_dict(data)

        assert mention.id == "bot-123"
        assert mention.name == "MyBot"
        assert mention.text == "<at>MyBot</at>"

    def test_from_dict_missing_mentioned(self):
        """Test creating mention without mentioned object."""
        data = {"type": "mention", "text": "<at>Bot</at>"}
        mention = TeamsMention.from_dict(data)

        assert mention.id == ""
        assert mention.name == ""
        assert mention.text == "<at>Bot</at>"


class TestTeamsMessage:
    """Tests for TeamsMessage dataclass."""

    @pytest.fixture
    def full_message_data(self):
        """Complete Teams message payload."""
        return {
            "id": "msg-123",
            "type": "message",
            "text": "<at>Bot</at> What is the vacation policy?",
            "timestamp": "2024-01-15T10:30:00Z",
            "from": {
                "id": "user-456",
                "name": "Jane Doe",
                "aadObjectId": "aad-789",
            },
            "conversation": {
                "id": "conv-abc",
                "conversationType": "channel",
                "tenantId": "tenant-xyz",
            },
            "recipient": {
                "id": "bot-123",
                "name": "MyBot",
            },
            "serviceUrl": "https://smba.trafficmanager.net/",
            "channelId": "msteams",
            "entities": [
                {
                    "type": "mention",
                    "mentioned": {"id": "bot-123", "name": "MyBot"},
                    "text": "<at>Bot</at>",
                }
            ],
        }

    def test_from_dict_full(self, full_message_data):
        """Test creating message with all fields."""
        msg = TeamsMessage.from_dict(full_message_data)

        assert msg.id == "msg-123"
        assert msg.type == "message"
        assert msg.text == "<at>Bot</at> What is the vacation policy?"
        assert msg.timestamp is not None
        assert msg.from_user.name == "Jane Doe"
        assert msg.conversation.id == "conv-abc"
        assert msg.recipient is not None
        assert msg.recipient.name == "MyBot"
        assert msg.service_url == "https://smba.trafficmanager.net/"
        assert len(msg.mentions) == 1

    def test_from_dict_minimal(self):
        """Test creating message with minimal fields."""
        data = {
            "id": "msg-123",
            "text": "Hello",
            "from": {"id": "user-1"},
            "conversation": {"id": "conv-1"},
        }
        msg = TeamsMessage.from_dict(data)

        assert msg.id == "msg-123"
        assert msg.type == "message"
        assert msg.text == "Hello"
        assert msg.timestamp is None
        assert msg.recipient is None
        assert msg.channel_id == "msteams"
        assert len(msg.mentions) == 0

    def test_from_dict_invalid_timestamp(self):
        """Test that invalid timestamp is handled gracefully."""
        data = {
            "id": "msg-123",
            "text": "Hello",
            "timestamp": "not-a-date",
            "from": {"id": "user-1"},
            "conversation": {"id": "conv-1"},
        }
        msg = TeamsMessage.from_dict(data)

        assert msg.timestamp is None

    def test_get_clean_text(self, full_message_data):
        """Test removing @mentions from text."""
        msg = TeamsMessage.from_dict(full_message_data)
        clean = msg.get_clean_text()

        assert clean == "What is the vacation policy?"

    def test_get_clean_text_multiple_mentions(self):
        """Test removing multiple @mentions."""
        data = {
            "id": "msg-1",
            "text": "<at>Bot</at> hello <at>User</at> how are you",
            "from": {"id": "u1"},
            "conversation": {"id": "c1"},
        }
        msg = TeamsMessage.from_dict(data)

        assert msg.get_clean_text() == "hello how are you"

    def test_get_clean_text_no_mentions(self):
        """Test clean text without mentions."""
        data = {
            "id": "msg-1",
            "text": "Just a regular message",
            "from": {"id": "u1"},
            "conversation": {"id": "c1"},
        }
        msg = TeamsMessage.from_dict(data)

        assert msg.get_clean_text() == "Just a regular message"

    def test_is_command_true(self):
        """Test command detection."""
        data = {
            "id": "msg-1",
            "text": "<at>Bot</at> /help",
            "from": {"id": "u1"},
            "conversation": {"id": "c1"},
        }
        msg = TeamsMessage.from_dict(data)

        assert msg.is_command() is True

    def test_is_command_false(self):
        """Test non-command detection."""
        data = {
            "id": "msg-1",
            "text": "<at>Bot</at> hello",
            "from": {"id": "u1"},
            "conversation": {"id": "c1"},
        }
        msg = TeamsMessage.from_dict(data)

        assert msg.is_command() is False

    def test_get_command(self):
        """Test extracting command and args."""
        data = {
            "id": "msg-1",
            "text": "<at>Bot</at> /search suppliers",
            "from": {"id": "u1"},
            "conversation": {"id": "c1"},
        }
        msg = TeamsMessage.from_dict(data)
        result = msg.get_command()

        assert result is not None
        command, args = result
        assert command == "search"
        assert args == "suppliers"

    def test_get_command_no_args(self):
        """Test extracting command without args."""
        data = {
            "id": "msg-1",
            "text": "<at>Bot</at> /help",
            "from": {"id": "u1"},
            "conversation": {"id": "c1"},
        }
        msg = TeamsMessage.from_dict(data)
        result = msg.get_command()

        assert result is not None
        command, args = result
        assert command == "help"
        assert args == ""

    def test_get_command_not_command(self):
        """Test get_command returns None for non-commands."""
        data = {
            "id": "msg-1",
            "text": "hello",
            "from": {"id": "u1"},
            "conversation": {"id": "c1"},
        }
        msg = TeamsMessage.from_dict(data)

        assert msg.get_command() is None

    def test_get_user_identifier_with_aad(self, full_message_data):
        """Test user identifier prefers AAD object ID."""
        msg = TeamsMessage.from_dict(full_message_data)

        assert msg.get_user_identifier() == "aad-789"

    def test_get_user_identifier_without_aad(self):
        """Test user identifier falls back to user ID."""
        data = {
            "id": "msg-1",
            "text": "hello",
            "from": {"id": "user-123", "name": "User"},
            "conversation": {"id": "c1"},
        }
        msg = TeamsMessage.from_dict(data)

        assert msg.get_user_identifier() == "user-123"

    def test_get_session_key(self, full_message_data):
        """Test session key generation."""
        msg = TeamsMessage.from_dict(full_message_data)

        assert msg.get_session_key() == "aad-789:conv-abc"


class TestTeamsResponse:
    """Tests for TeamsResponse dataclass."""

    def test_to_dict_text_only(self):
        """Test response with text only."""
        response = TeamsResponse(text="Hello, how can I help?")
        result = response.to_dict()

        assert result == {"type": "message", "text": "Hello, how can I help?"}

    def test_to_dict_with_card(self):
        """Test response with Adaptive Card."""
        card = {
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [{"type": "TextBlock", "text": "Hello"}],
        }
        response = TeamsResponse(text="", card=card)
        result = response.to_dict()

        assert result["type"] == "message"
        assert "attachments" in result
        assert len(result["attachments"]) == 1
        assert result["attachments"][0]["contentType"] == "application/vnd.microsoft.card.adaptive"
        assert result["attachments"][0]["content"] == card
