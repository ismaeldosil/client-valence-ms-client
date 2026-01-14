"""Bot Framework module for MS Teams integration.

This module provides Microsoft Bot Framework support for the Teams client,
enabling features not available with Outgoing Webhooks:
- Automatic thread reply handling (no @mention required)
- Proactive messaging
- Interactive Adaptive Cards with submit actions
- No 5-second timeout constraint
"""

from .adapter import create_bot_adapter
from .bot import ValerieBot
from .proactive import ProactiveMessenger

__all__ = ["ValerieBot", "create_bot_adapter", "ProactiveMessenger"]
