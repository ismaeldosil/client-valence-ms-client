"""
Pytest common fixtures.
"""

import pytest
from fastapi.testclient import TestClient as FastAPITestClient

from tests.mocks.mock_agent_server import app as agent_app
from tests.mocks.mock_webhook_receiver import app as webhook_app


@pytest.fixture
def mock_agent_url() -> str:
    """URL of the mock agent server."""
    return "http://localhost:8080"


@pytest.fixture
def mock_webhook_url() -> str:
    """URL of the mock webhook receiver."""
    return "http://localhost:3000"


@pytest.fixture
def agent_test_client() -> FastAPITestClient:
    """Sync test client for mock agent (no server needed)."""
    return FastAPITestClient(agent_app)


@pytest.fixture
def webhook_test_client() -> FastAPITestClient:
    """Sync test client for mock webhook (no server needed)."""
    return FastAPITestClient(webhook_app)


@pytest.fixture
def sample_query_request() -> dict:
    """Sample request for /query endpoint."""
    return {
        "message": "Cual es la politica de vacaciones?",
        "context": {
            "platform": "test",
            "user_id": "test-user",
            "user_name": "Test User",
        },
    }


@pytest.fixture
def sample_teams_message() -> dict:
    """Sample Teams message."""
    return {
        "type": "message",
        "id": "test-msg-001",
        "text": "<at>Bot</at> Hola, necesito ayuda",
        "from": {
            "id": "user-001",
            "name": "Test User",
        },
        "conversation": {
            "id": "conv-001",
        },
    }


@pytest.fixture
def sample_query_with_history() -> dict:
    """Sample request with conversation history."""
    return {
        "message": "Y si no los uso todos?",
        "context": {
            "platform": "test",
            "user_id": "test-user",
        },
        "conversation_history": [
            {"role": "user", "content": "Cual es la politica de vacaciones?"},
            {
                "role": "assistant",
                "content": "La politica de vacaciones permite 15 dias...",
            },
        ],
    }
