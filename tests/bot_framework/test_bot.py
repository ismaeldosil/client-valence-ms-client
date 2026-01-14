"""Tests for ValerieBot."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ChannelAccount, ConversationAccount

from src.teams.bot_framework.bot import ValerieBot
from src.teams.common.processor import ProcessedMessage


class TestValerieBot:
    """Tests for ValerieBot class."""

    @pytest.fixture
    def mock_processor(self):
        """Create a mock unified processor."""
        processor = MagicMock()
        processor.process = AsyncMock(
            return_value=ProcessedMessage(text="Test response")
        )
        return processor

    @pytest.fixture
    def mock_proactive_messenger(self):
        """Create a mock proactive messenger."""
        messenger = MagicMock()
        messenger.store_reference = AsyncMock()
        return messenger

    @pytest.fixture
    def bot(self, mock_processor, mock_proactive_messenger):
        """Create a bot with mocked dependencies."""
        return ValerieBot(
            processor=mock_processor,
            proactive_messenger=mock_proactive_messenger,
        )

    @pytest.fixture
    def sample_activity(self):
        """Create a sample activity."""
        return Activity(
            id="activity-123",
            type="message",
            text="Hello bot",
            channel_id="msteams",
            from_property=ChannelAccount(
                id="user-456",
                name="Test User",
                aad_object_id="aad-789",
            ),
            conversation=ConversationAccount(
                id="conv-abc",
            ),
            recipient=ChannelAccount(
                id="bot-123",
                name="Valerie",
            ),
        )

    @pytest.fixture
    def mock_turn_context(self, sample_activity):
        """Create a mock turn context."""
        context = MagicMock(spec=TurnContext)
        context.activity = sample_activity
        context.send_activity = AsyncMock()
        return context

    async def test_on_message_activity(
        self, bot, mock_processor, mock_turn_context
    ):
        """Test handling a message activity."""
        await bot.on_message_activity(mock_turn_context)

        mock_processor.process.assert_called_once_with(
            user_id="aad-789",  # Uses AAD object ID
            conversation_id="conv-abc",
            text="Hello bot",
            reply_to_id=None,
            user_name="Test User",
        )
        mock_turn_context.send_activity.assert_called_once_with("Test response")

    async def test_on_message_activity_with_reply(
        self, bot, mock_processor, mock_turn_context
    ):
        """Test handling a message in a thread."""
        mock_turn_context.activity.reply_to_id = "parent-msg-xyz"

        await bot.on_message_activity(mock_turn_context)

        mock_processor.process.assert_called_once()
        call_kwargs = mock_processor.process.call_args.kwargs
        assert call_kwargs["reply_to_id"] == "parent-msg-xyz"

    async def test_on_message_activity_empty_text(
        self, bot, mock_processor, mock_turn_context
    ):
        """Test handling empty message."""
        mock_turn_context.activity.text = ""

        await bot.on_message_activity(mock_turn_context)

        mock_processor.process.assert_not_called()
        mock_turn_context.send_activity.assert_called_once()
        call_args = mock_turn_context.send_activity.call_args[0][0]
        assert "didn't catch that" in call_args

    async def test_on_turn_stores_reference(
        self, bot, mock_proactive_messenger, mock_turn_context
    ):
        """Test that on_turn stores conversation reference."""
        # Need to patch super().on_turn to avoid full processing
        with patch.object(
            ValerieBot.__bases__[0], "on_turn", new_callable=AsyncMock
        ):
            await bot.on_turn(mock_turn_context)

        mock_proactive_messenger.store_reference.assert_called_once_with(
            mock_turn_context.activity
        )

    async def test_get_user_id_with_aad(self, bot, sample_activity):
        """Test user ID extraction prefers AAD object ID."""
        user_id = bot._get_user_id(sample_activity)
        assert user_id == "aad-789"

    async def test_get_user_id_without_aad(self, bot, sample_activity):
        """Test user ID extraction falls back to user ID."""
        sample_activity.from_property.aad_object_id = None
        user_id = bot._get_user_id(sample_activity)
        assert user_id == "user-456"

    async def test_get_user_id_no_from_property(self, bot, sample_activity):
        """Test user ID extraction with no from property."""
        sample_activity.from_property = None
        user_id = bot._get_user_id(sample_activity)
        assert user_id == ""

    async def test_remove_bot_mention_no_entities(self, bot, sample_activity):
        """Test mention removal with no entities."""
        result = bot._remove_bot_mention("Hello bot", sample_activity)
        assert result == "Hello bot"

    async def test_remove_bot_mention_with_mention(self, bot, sample_activity):
        """Test mention removal when bot is mentioned."""
        sample_activity.entities = [
            MagicMock(
                type="mention",
                additional_properties={
                    "mentioned": {"id": "bot-123"},
                    "text": "<at>Valerie</at>",
                },
            )
        ]
        result = bot._remove_bot_mention("<at>Valerie</at> Hello", sample_activity)
        assert result == "Hello"


class TestValerieBotConversationUpdate:
    """Tests for conversation update handling."""

    @pytest.fixture
    def mock_processor(self):
        """Create a mock processor."""
        return MagicMock()

    @pytest.fixture
    def bot(self, mock_processor):
        """Create a bot."""
        return ValerieBot(processor=mock_processor)

    async def test_on_conversation_update_bot_added(self, bot):
        """Test welcome message when bot is added."""
        activity = Activity(
            type="conversationUpdate",
            members_added=[
                ChannelAccount(id="bot-123", name="Valerie"),
            ],
            recipient=ChannelAccount(id="bot-123"),
            conversation=ConversationAccount(id="conv-abc"),
        )

        context = MagicMock(spec=TurnContext)
        context.activity = activity
        context.send_activity = AsyncMock()

        await bot.on_conversation_update_activity(context)

        context.send_activity.assert_called_once()
        call_args = context.send_activity.call_args[0][0]
        assert "Hello" in call_args
        assert "Valerie" in call_args

    async def test_on_conversation_update_user_added(self, bot):
        """Test no message when user (not bot) is added."""
        activity = Activity(
            type="conversationUpdate",
            members_added=[
                ChannelAccount(id="user-456", name="New User"),
            ],
            recipient=ChannelAccount(id="bot-123"),
            conversation=ConversationAccount(id="conv-abc"),
        )

        context = MagicMock(spec=TurnContext)
        context.activity = activity
        context.send_activity = AsyncMock()

        await bot.on_conversation_update_activity(context)

        context.send_activity.assert_not_called()
