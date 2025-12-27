"""
Mock servers for testing.
"""

from .mock_responses import DEFAULT_RESPONSE, KNOWLEDGE_BASE, get_response_for_query

__all__ = [
    "KNOWLEDGE_BASE",
    "DEFAULT_RESPONSE",
    "get_response_for_query",
]
