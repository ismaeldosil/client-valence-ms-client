"""
Notification Service.

Main service for sending notifications to Teams channels.
"""

from typing import Optional

import structlog

from .channels import ChannelRegistry
from .models import Notification, Priority
from ..teams.sender.base import TeamsSender
from ..teams.sender.cards import AdaptiveCardBuilder
from ..core.exceptions import TeamsError

logger = structlog.get_logger()


class NotificationService:
    """
    Service for sending notifications to Microsoft Teams.

    Handles:
    - Channel resolution
    - Card building
    - Notification delivery
    - Status tracking
    """

    def __init__(
        self,
        sender: TeamsSender,
        channels: ChannelRegistry,
        card_builder: Optional[AdaptiveCardBuilder] = None,
    ) -> None:
        """
        Initialize the notification service.

        Args:
            sender: Teams sender implementation
            channels: Channel registry
            card_builder: Optional card builder (created if not provided)
        """
        self.sender = sender
        self.channels = channels
        self.cards = card_builder or AdaptiveCardBuilder()

    async def notify(
        self,
        channel: str,
        message: str,
        title: Optional[str] = None,
        card_type: Optional[str] = None,
        priority: str = "medium",
        metadata: Optional[dict] = None,
    ) -> Notification:
        """
        Send a notification to a Teams channel.

        Args:
            channel: Channel name (must be registered)
            message: Notification message
            title: Optional title
            card_type: Card type (alert, info, report) or None for text
            priority: Priority level
            metadata: Additional data for card templates

        Returns:
            Notification object with delivery status

        Raises:
            ValueError: If channel not found
            TeamsError: If delivery fails
        """
        # Resolve channel
        channel_config = self.channels.get(channel)
        if not channel_config:
            raise ValueError(f"Channel '{channel}' not found or disabled")

        # Create notification
        notification = Notification(
            channel=channel,
            message=message,
            title=title,
            card_type=card_type,
            priority=Priority(priority),
            metadata=metadata or {},
        )

        logger.info(
            "sending_notification",
            notification_id=notification.id,
            channel=channel,
            priority=priority,
            card_type=card_type,
        )

        try:
            if card_type:
                # Build and send card
                card = self.cards.build(
                    card_type=card_type,
                    title=title or "Notificación",
                    message=message,
                    priority=priority,
                    **(metadata or {}),
                )
                await self.sender.send_card(channel_config.webhook_url, card)
            else:
                # Send as plain text with priority emoji
                text = self._format_text(notification)
                await self.sender.send_text(channel_config.webhook_url, text)

            notification.mark_sent()
            logger.info(
                "notification_sent",
                notification_id=notification.id,
                channel=channel,
            )

        except TeamsError as e:
            notification.mark_failed(str(e))
            logger.error(
                "notification_failed",
                notification_id=notification.id,
                channel=channel,
                error=str(e),
            )
            raise

        return notification

    async def notify_all(
        self,
        message: str,
        title: Optional[str] = None,
        card_type: Optional[str] = None,
        priority: str = "medium",
        metadata: Optional[dict] = None,
    ) -> list[Notification]:
        """
        Send notification to all enabled channels.

        Args:
            message: Notification message
            title: Optional title
            card_type: Card type or None for text
            priority: Priority level
            metadata: Additional card data

        Returns:
            List of Notification objects
        """
        notifications = []

        for channel in self.channels.get_enabled():
            try:
                notification = await self.notify(
                    channel=channel.name,
                    message=message,
                    title=title,
                    card_type=card_type,
                    priority=priority,
                    metadata=metadata,
                )
                notifications.append(notification)
            except Exception as e:
                # Create failed notification
                notification = Notification(
                    channel=channel.name,
                    message=message,
                    title=title,
                    card_type=card_type,
                    priority=Priority(priority),
                )
                notification.mark_failed(str(e))
                notifications.append(notification)

        return notifications

    def _format_text(self, notification: Notification) -> str:
        """Format text message with priority emoji."""
        emoji = {
            Priority.LOW: "ℹ️",
            Priority.MEDIUM: "📢",
            Priority.HIGH: "⚠️",
            Priority.CRITICAL: "🚨",
        }.get(notification.priority, "📢")

        if notification.title:
            return f"{emoji} **{notification.title}**\n\n{notification.message}"
        return f"{emoji} {notification.message}"
