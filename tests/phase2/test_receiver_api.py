"""Integration tests for Teams Webhook Receiver API."""

import base64
import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from src.agent.models import ChatResponse


class TestReceiverAPI:
    """Integration tests for the receiver API."""

    @pytest.fixture
    def hmac_secret(self):
        """Valid HMAC secret."""
        return base64.b64encode(b"test-secret-key").decode()

    @pytest.fixture
    def sample_teams_payload(self):
        """Sample Teams webhook payload."""
        return {
            "id": "msg-123",
            "type": "message",
            "text": "<at>Bot</at> What suppliers do heat treatment?",
            "timestamp": "2024-01-15T10:30:00Z",
            "from": {
                "id": "user-456",
                "name": "Test User",
                "aadObjectId": "aad-789",
            },
            "conversation": {
                "id": "conv-abc",
                "conversationType": "channel",
            },
            "entities": [
                {
                    "type": "mention",
                    "mentioned": {"id": "bot-id", "name": "Bot"},
                    "text": "<at>Bot</at>",
                }
            ],
        }

    def _compute_hmac(self, secret: str, body: bytes) -> str:
        """Compute HMAC signature."""
        secret_bytes = base64.b64decode(secret)
        signature = hmac.new(secret_bytes, body, hashlib.sha256).digest()
        return base64.b64encode(signature).decode()

    @pytest.fixture
    def mock_agent_response(self):
        """Mock agent response."""
        return ChatResponse(
            session_id="sess-123",
            message="Here are the suppliers for heat treatment: AeroTech, MetalTreat",
            agents_executed=[],
            intent="supplier_search",
            confidence=0.95,
        )

    def test_health_check(self):
        """Test health endpoint."""
        from src.api.receiver_api import app

        with TestClient(app) as client:
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["version"] == "2.0.0"
            assert data["phase"] == "2-stateless"

    def test_webhook_processes_valid_message(self, sample_teams_payload):
        """Test webhook processes a valid Teams message and returns response."""
        from src.api.receiver_api import app
        from src.core.config import settings

        body = json.dumps(sample_teams_payload).encode()

        if settings.teams_hmac_secret:
            signature = self._compute_hmac(settings.teams_hmac_secret, body)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"HMAC {signature}",
            }
        else:
            headers = {"Content-Type": "application/json"}

        with TestClient(app) as client:
            response = client.post("/webhook", content=body, headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["type"] == "message"
            assert "text" in data

    def test_webhook_handles_invalid_json(self):
        """Test webhook returns 400 for invalid JSON (when HMAC is valid)."""
        from src.api.receiver_api import app
        from src.core.config import settings

        body = b"not json"

        if settings.teams_hmac_secret:
            signature = self._compute_hmac(settings.teams_hmac_secret, body)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"HMAC {signature}",
            }
        else:
            headers = {"Content-Type": "application/json"}

        with TestClient(app) as client:
            response = client.post("/webhook", content=body, headers=headers)
            assert response.status_code == 400


class TestWebhookHMAC:
    """Tests for HMAC verification in webhook endpoint.

    Note: Full HMAC verification tests are in test_hmac.py.
    These tests verify the API integration when HMAC is configured via env.
    """

    @pytest.fixture
    def hmac_secret(self):
        """Valid HMAC secret."""
        return base64.b64encode(b"test-secret").decode()

    def _compute_hmac(self, secret: str, body: bytes) -> str:
        """Compute HMAC signature."""
        secret_bytes = base64.b64decode(secret)
        signature = hmac.new(secret_bytes, body, hashlib.sha256).digest()
        return base64.b64encode(signature).decode()

    def test_webhook_with_valid_hmac_when_configured(self, hmac_secret):
        """Test webhook works with valid HMAC when secret is configured via env."""
        from src.core.config import settings

        # Only run if HMAC is configured in the environment
        if not settings.teams_hmac_secret:
            pytest.skip("HMAC not configured - skipping integration test")

        from src.api.receiver_api import app

        body = json.dumps({"id": "1", "text": "test", "from": {}, "conversation": {}}).encode()
        signature = self._compute_hmac(settings.teams_hmac_secret, body)

        with TestClient(app) as client:
            response = client.post(
                "/webhook",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"HMAC {signature}",
                },
            )
            # Should get 200 (message processed) not 401 (auth failed)
            assert response.status_code == 200
