"""
Tests for Notification Service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.notifier.models import Notification, NotificationStatus, Priority
from src.notifier.channels import Channel, ChannelRegistry
from src.notifier.service import NotificationService
from src.teams.sender.cards import AdaptiveCardBuilder
from src.core.exceptions import TeamsError


class TestNotificationModels:
    """Tests for notification models."""

    def test_notification_creation(self) -> None:
        """Test creating a notification."""
        notification = Notification(
            channel="alerts",
            message="Test message",
            title="Test Title",
            priority=Priority.HIGH,
        )

        assert notification.channel == "alerts"
        assert notification.message == "Test message"
        assert notification.status == NotificationStatus.PENDING
        assert notification.id is not None

    def test_notification_mark_sent(self) -> None:
        """Test marking notification as sent."""
        notification = Notification(channel="alerts", message="Test")
        notification.mark_sent()

        assert notification.status == NotificationStatus.SENT
        assert notification.sent_at is not None

    def test_notification_mark_failed(self) -> None:
        """Test marking notification as failed."""
        notification = Notification(channel="alerts", message="Test")
        notification.mark_failed("Connection error")

        assert notification.status == NotificationStatus.FAILED
        assert notification.error == "Connection error"

    def test_notification_to_dict(self) -> None:
        """Test converting notification to dict."""
        notification = Notification(
            channel="alerts",
            message="Test",
            priority=Priority.CRITICAL,
        )
        data = notification.to_dict()

        assert data["channel"] == "alerts"
        assert data["priority"] == "critical"
        assert data["status"] == "pending"


class TestChannelRegistry:
    """Tests for ChannelRegistry."""

    def test_register_and_get_channel(self) -> None:
        """Test registering and retrieving a channel."""
        registry = ChannelRegistry()
        channel = Channel(
            name="alerts",
            webhook_url="https://outlook.office.com/webhook/test",
            description="Alert channel",
        )

        registry.register(channel)
        retrieved = registry.get("alerts")

        assert retrieved is not None
        assert retrieved.name == "alerts"
        assert retrieved.webhook_url == "https://outlook.office.com/webhook/test"

    def test_get_nonexistent_channel(self) -> None:
        """Test getting a channel that doesn't exist."""
        registry = ChannelRegistry()
        result = registry.get("nonexistent")

        assert result is None

    def test_get_disabled_channel(self) -> None:
        """Test that disabled channels return None."""
        registry = ChannelRegistry()
        channel = Channel(
            name="disabled",
            webhook_url="https://test.com",
            enabled=False,
        )
        registry.register(channel)

        result = registry.get("disabled")
        assert result is None

    def test_get_all_channels(self) -> None:
        """Test getting all channels."""
        registry = ChannelRegistry()
        registry.register(Channel(name="a", webhook_url="https://a.com"))
        registry.register(Channel(name="b", webhook_url="https://b.com"))

        all_channels = registry.get_all()
        assert len(all_channels) == 2

    def test_get_enabled_channels(self) -> None:
        """Test getting only enabled channels."""
        registry = ChannelRegistry()
        registry.register(Channel(name="enabled", webhook_url="https://a.com", enabled=True))
        registry.register(Channel(name="disabled", webhook_url="https://b.com", enabled=False))

        enabled = registry.get_enabled()
        assert len(enabled) == 1
        assert enabled[0].name == "enabled"


class TestNotificationService:
    """Tests for NotificationService."""

    @pytest.fixture
    def mock_sender(self) -> AsyncMock:
        """Create a mock sender."""
        sender = AsyncMock()
        sender.send_text.return_value = True
        sender.send_card.return_value = True
        return sender

    @pytest.fixture
    def registry(self) -> ChannelRegistry:
        """Create a channel registry with test channels."""
        registry = ChannelRegistry()
        registry.register(Channel(
            name="alerts",
            webhook_url="https://outlook.office.com/webhook/alerts",
        ))
        registry.register(Channel(
            name="reports",
            webhook_url="https://outlook.office.com/webhook/reports",
        ))
        return registry

    @pytest.fixture
    def service(self, mock_sender: AsyncMock, registry: ChannelRegistry) -> NotificationService:
        """Create a notification service."""
        return NotificationService(mock_sender, registry)

    @pytest.mark.asyncio
    async def test_notify_text(self, service: NotificationService, mock_sender: AsyncMock) -> None:
        """Test sending a text notification."""
        notification = await service.notify(
            channel="alerts",
            message="Test message",
            priority="high",
        )

        assert notification.status == NotificationStatus.SENT
        mock_sender.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_card(self, service: NotificationService, mock_sender: AsyncMock) -> None:
        """Test sending a card notification."""
        notification = await service.notify(
            channel="alerts",
            message="Test message",
            title="Alert",
            card_type="alert",
            priority="critical",
        )

        assert notification.status == NotificationStatus.SENT
        mock_sender.send_card.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_unknown_channel(self, service: NotificationService) -> None:
        """Test error when channel not found."""
        with pytest.raises(ValueError) as exc_info:
            await service.notify(
                channel="nonexistent",
                message="Test",
            )

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_notify_sender_failure(
        self,
        service: NotificationService,
        mock_sender: AsyncMock,
    ) -> None:
        """Test handling sender failure."""
        mock_sender.send_text.side_effect = TeamsError("Send failed")

        with pytest.raises(TeamsError):
            await service.notify(
                channel="alerts",
                message="Test",
            )

    @pytest.mark.asyncio
    async def test_notify_all(self, service: NotificationService, mock_sender: AsyncMock) -> None:
        """Test sending to all channels."""
        notifications = await service.notify_all(
            message="Broadcast message",
            priority="high",
        )

        assert len(notifications) == 2
        assert mock_sender.send_text.call_count == 2
