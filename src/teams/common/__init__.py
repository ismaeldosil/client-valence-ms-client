"""Common module for shared Teams processing logic.

This module provides platform-agnostic message processing
that can be used by both Outgoing Webhooks and Bot Framework.
"""

from .processor import UnifiedMessageProcessor

__all__ = ["UnifiedMessageProcessor"]
