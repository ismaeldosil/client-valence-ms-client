"""
Core module - shared utilities.
"""

from .config import settings
from .exceptions import (
    TeamsAgentError,
    AgentError,
    AgentTimeoutError,
    AgentConnectionError,
    TeamsError,
    WebhookVerificationError,
)
from .logging import get_logger, setup_logging

__all__ = [
    "settings",
    "TeamsAgentError",
    "AgentError",
    "AgentTimeoutError",
    "AgentConnectionError",
    "TeamsError",
    "WebhookVerificationError",
    "get_logger",
    "setup_logging",
]
