"""
Teams Sender Protocol.

Defines the interface for sending messages to Microsoft Teams.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class TeamsSender(Protocol):
    """
    Protocol for sending messages to Microsoft Teams.

    Implementations:
    - WebhookSender: Uses Incoming Webhooks
    """

    async def send_text(self, webhook_url: str, text: str) -> bool:
        """
        Send a simple text message to Teams.

        Args:
            webhook_url: The Incoming Webhook URL for the channel
            text: Plain text message to send

        Returns:
            True if message was sent successfully

        Raises:
            TeamsError: If sending fails after retries
        """
        ...

    async def send_card(self, webhook_url: str, card: dict) -> bool:
        """
        Send an Adaptive Card to Teams.

        Args:
            webhook_url: The Incoming Webhook URL for the channel
            card: Adaptive Card content (dict matching AC schema)

        Returns:
            True if card was sent successfully

        Raises:
            TeamsError: If sending fails after retries

        Note:
            Only 'openURL' action is supported in Outgoing Webhooks.
            Other actions will not work.
        """
        ...

    async def close(self) -> None:
        """Close any open connections."""
        ...
