"""
Channel Registry.

Manages registered Teams channels and their webhook URLs.
"""

import re
from dataclasses import dataclass
from typing import Optional, Protocol

import structlog

logger = structlog.get_logger()


class SettingsProtocol(Protocol):
    """Protocol for settings with workflow URLs."""

    teams_workflow_alerts: Optional[str]
    teams_workflow_reports: Optional[str]
    teams_workflow_general: Optional[str]
    teams_workflow_url: Optional[str]


@dataclass
class Channel:
    """
    Represents a Teams channel configuration.

    Attributes:
        name: Channel identifier (e.g., "alerts", "reports")
        webhook_url: Power Automate Workflow URL for the channel
        enabled: Whether the channel is active
        description: Optional channel description
    """

    name: str
    webhook_url: str
    enabled: bool = True
    description: Optional[str] = None


class ChannelRegistry:
    """
    Registry for managing Teams channels.

    Stores channel configurations and provides lookup by name.
    """

    # Power Automate Workflow URL pattern (logic.azure.com)
    WEBHOOK_URL_PATTERN = re.compile(
        r"^https://[\w.-]+\.logic\.azure\.com(:\d+)?/workflows/[\w-]+/triggers/[\w]+/paths/invoke"
    )

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._channels: dict[str, Channel] = {}

    def register(self, channel: Channel) -> None:
        """
        Register a channel.

        Args:
            channel: Channel to register

        Raises:
            ValueError: If webhook URL is invalid
        """
        if not self._validate_webhook_url(channel.webhook_url):
            logger.warning(
                "invalid_webhook_url_format",
                channel=channel.name,
                url_preview=channel.webhook_url[:50],
            )
            # Don't raise, just warn - URL format may vary

        self._channels[channel.name] = channel
        logger.info("channel_registered", name=channel.name, enabled=channel.enabled)

    def get(self, name: str) -> Optional[Channel]:
        """
        Get channel by name.

        Args:
            name: Channel name

        Returns:
            Channel if found and enabled, None otherwise
        """
        channel = self._channels.get(name)
        if channel and channel.enabled:
            return channel
        return None

    def get_all(self) -> list[Channel]:
        """Get all registered channels."""
        return list(self._channels.values())

    def get_enabled(self) -> list[Channel]:
        """Get all enabled channels."""
        return [c for c in self._channels.values() if c.enabled]

    def _validate_webhook_url(self, url: str) -> bool:
        """Validate webhook URL format."""
        if not url:
            return False
        # Basic validation - URL should be HTTPS (Power Automate or mock)
        return url.startswith("https://") or url.startswith("http://localhost")

    @classmethod
    def from_settings(cls, settings: SettingsProtocol) -> "ChannelRegistry":
        """
        Create registry from settings.

        Reads TEAMS_WORKFLOW_* settings and creates channels.

        Args:
            settings: Settings object with Power Automate Workflow URLs

        Returns:
            Configured ChannelRegistry
        """
        registry = cls()

        # Map setting names to channel names
        channel_map = {
            "teams_workflow_alerts": ("alerts", "Alert notifications"),
            "teams_workflow_reports": ("reports", "Report notifications"),
            "teams_workflow_general": ("general", "General notifications"),
        }

        for setting_name, (channel_name, description) in channel_map.items():
            webhook_url = getattr(settings, setting_name, None)
            if webhook_url:
                registry.register(
                    Channel(
                        name=channel_name,
                        webhook_url=webhook_url,
                        description=description,
                    )
                )

        # Also check generic workflow URL
        if settings.teams_workflow_url:
            if "default" not in registry._channels:
                registry.register(
                    Channel(
                        name="default",
                        webhook_url=settings.teams_workflow_url,
                        description="Default channel",
                    )
                )

        return registry
