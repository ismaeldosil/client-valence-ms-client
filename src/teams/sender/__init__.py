"""Teams sender module for Incoming Webhooks."""

from .base import TeamsSender
from .webhook_sender import WebhookSender

__all__ = ["TeamsSender", "WebhookSender"]
