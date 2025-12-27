"""Integration tests for Teams Webhook Receiver API."""

import base64
import hashlib
import hmac
import json
from unittest.mock import patch

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
    """Tests for HMAC verification in webhook endpoint."""

    @pytest.fixture
    def hmac_secret(self):
        """Valid HMAC secret."""
        return base64.b64encode(b"test-secret").decode()

    def _compute_hmac(self, secret: str, body: bytes) -> str:
        """Compute HMAC signature."""
        secret_bytes = base64.b64decode(secret)
        signature = hmac.new(secret_bytes, body, hashlib.sha256).digest()
        return base64.b64encode(signature).decode()

    def test_webhook_missing_auth_header(self, hmac_secret):
        """Test webhook fails without Authorization header when HMAC is configured."""
        with patch.dict("os.environ", {"TEAMS_HMAC_SECRET": hmac_secret}, clear=False):
            from importlib import reload

            import src.api.receiver_api as api_module

            reload(api_module)

            with TestClient(api_module.app) as client:
                response = client.post(
                    "/webhook",
                    json={"id": "1", "text": "test", "from": {}, "conversation": {}},
                )

                assert response.status_code == 401

    def test_webhook_invalid_signature(self, hmac_secret):
        """Test webhook fails with invalid HMAC signature."""
        with patch.dict("os.environ", {"TEAMS_HMAC_SECRET": hmac_secret}, clear=False):
            from importlib import reload

            import src.api.receiver_api as api_module

            reload(api_module)

            with TestClient(api_module.app) as client:
                response = client.post(
                    "/webhook",
                    json={"id": "1", "text": "test", "from": {}, "conversation": {}},
                    headers={"Authorization": "HMAC invalid-signature"},
                )

                assert response.status_code == 401
