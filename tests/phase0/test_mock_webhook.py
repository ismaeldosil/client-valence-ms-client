"""
Tests for Mock Webhook Receiver.
"""

from fastapi.testclient import TestClient


class TestMockWebhookHealth:
    """Tests for /health endpoint."""

    def test_health_returns_ok(self, webhook_test_client: TestClient) -> None:
        """Health check returns status ok."""
        response = webhook_test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "mock-webhook"


class TestMockWebhookMessage:
    """Tests for /webhook endpoint."""

    def test_simple_message(
        self,
        webhook_test_client: TestClient,
        sample_teams_message: dict,
    ) -> None:
        """Simple message is handled correctly."""
        response = webhook_test_client.post("/webhook", json=sample_teams_message)

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "message"
        assert "text" in data

    def test_message_with_mention(
        self,
        webhook_test_client: TestClient,
    ) -> None:
        """Message with @mention has mention stripped."""
        message = {
            "type": "message",
            "id": "test-001",
            "text": "<at>Bot</at> Este es mi mensaje",
            "from": {"id": "user-001", "name": "Test"},
            "conversation": {"id": "conv-001"},
        }

        response = webhook_test_client.post("/webhook", json=message)

        assert response.status_code == 200
        data = response.json()
        # The response should reference the message without the mention
        assert "Este es mi mensaje" in data["text"]

    def test_clear_command(self, webhook_test_client: TestClient) -> None:
        """Command /clear is handled."""
        message = {
            "type": "message",
            "id": "test-001",
            "text": "<at>Bot</at> /clear",
            "from": {"id": "user-001", "name": "Test"},
            "conversation": {"id": "conv-001"},
        }

        response = webhook_test_client.post("/webhook", json=message)

        assert response.status_code == 200
        data = response.json()
        assert "limpiado" in data["text"].lower() or "cleared" in data["text"].lower()

    def test_history_command(self, webhook_test_client: TestClient) -> None:
        """Command /history is handled."""
        message = {
            "type": "message",
            "id": "test-001",
            "text": "<at>Bot</at> /history",
            "from": {"id": "user-001", "name": "Test"},
            "conversation": {"id": "conv-001"},
        }

        response = webhook_test_client.post("/webhook", json=message)

        assert response.status_code == 200
        data = response.json()
        assert "historial" in data["text"].lower() or "history" in data["text"].lower()

    def test_help_command(self, webhook_test_client: TestClient) -> None:
        """Command /help is handled."""
        message = {
            "type": "message",
            "id": "test-001",
            "text": "<at>Bot</at> /help",
            "from": {"id": "user-001", "name": "Test"},
            "conversation": {"id": "conv-001"},
        }

        response = webhook_test_client.post("/webhook", json=message)

        assert response.status_code == 200
        data = response.json()
        assert "comando" in data["text"].lower() or "command" in data["text"].lower()

    def test_response_format(
        self,
        webhook_test_client: TestClient,
        sample_teams_message: dict,
    ) -> None:
        """Response has Teams message format."""
        response = webhook_test_client.post("/webhook", json=sample_teams_message)

        assert response.status_code == 200
        data = response.json()

        # Check required fields for Teams response
        assert "type" in data
        assert data["type"] == "message"
        assert "text" in data
        assert isinstance(data["text"], str)

    def test_message_without_from(self, webhook_test_client: TestClient) -> None:
        """Message without 'from' field is handled."""
        message = {
            "type": "message",
            "id": "test-001",
            "text": "<at>Bot</at> Hello",
            "conversation": {"id": "conv-001"},
        }

        response = webhook_test_client.post("/webhook", json=message)

        assert response.status_code == 200
