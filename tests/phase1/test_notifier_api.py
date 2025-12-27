"""
Tests for Notifier API.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.notifier_api import app
from src.notifier.channels import Channel, ChannelRegistry
from src.notifier.models import Notification


class TestNotifierAPI:
    """Tests for the Notifier API."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def api_key(self) -> str:
        """Test API key matching settings default."""
        return "dev-api-key"

    @pytest.fixture
    def mock_channels(self) -> ChannelRegistry:
        """Create mock channels."""
        registry = ChannelRegistry()
        registry.register(
            Channel(
                name="alerts",
                webhook_url="https://test.webhook.com/alerts",
                description="Alert channel",
            )
        )
        return registry

    def test_health_no_auth(self, client: TestClient) -> None:
        """Test health endpoint doesn't require auth."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "notifier"

    def test_notify_requires_auth(self, client: TestClient) -> None:
        """Test notify endpoint requires API key."""
        response = client.post(
            "/api/v1/notify",
            json={"channel": "alerts", "message": "Test"},
        )

        assert response.status_code == 422  # Missing header

    def test_notify_invalid_auth(self, client: TestClient) -> None:
        """Test notify rejects invalid API key."""
        response = client.post(
            "/api/v1/notify",
            json={"channel": "alerts", "message": "Test"},
            headers={"X-API-Key": "wrong-key"},
        )

        assert response.status_code == 401

    def test_notify_success(
        self,
        client: TestClient,
        api_key: str,
        mock_channels: ChannelRegistry,
    ) -> None:
        """Test successful notification."""
        mock_notification = Notification(
            channel="alerts",
            message="Test message",
        )
        mock_notification.mark_sent()

        mock_service = MagicMock()
        mock_service.notify = AsyncMock(return_value=mock_notification)

        with patch("src.api.notifier_api.get_service", return_value=mock_service):
            response = client.post(
                "/api/v1/notify",
                json={
                    "channel": "alerts",
                    "message": "Test message",
                    "priority": "high",
                },
                headers={"X-API-Key": api_key},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["channel"] == "alerts"
        assert data["status"] == "sent"

    def test_notify_channel_not_found(
        self,
        client: TestClient,
        api_key: str,
    ) -> None:
        """Test notification to unknown channel."""
        mock_service = MagicMock()
        mock_service.notify = AsyncMock(side_effect=ValueError("Channel 'unknown' not found"))

        with patch("src.api.notifier_api.get_service", return_value=mock_service):
            response = client.post(
                "/api/v1/notify",
                json={
                    "channel": "unknown",
                    "message": "Test",
                },
                headers={"X-API-Key": api_key},
            )

        assert response.status_code == 404

    def test_list_channels(
        self,
        client: TestClient,
        api_key: str,
        mock_channels: ChannelRegistry,
    ) -> None:
        """Test listing channels."""
        with patch("src.api.notifier_api.get_channels", return_value=mock_channels):
            response = client.get(
                "/api/v1/channels",
                headers={"X-API-Key": api_key},
            )

        assert response.status_code == 200
        data = response.json()
        assert "channels" in data
        assert len(data["channels"]) == 1
        assert data["channels"][0]["name"] == "alerts"

    def test_list_channels_requires_auth(self, client: TestClient) -> None:
        """Test channels endpoint requires auth."""
        response = client.get("/api/v1/channels")
        assert response.status_code == 422

    def test_notify_validation(self, client: TestClient, api_key: str) -> None:
        """Test request validation."""
        # Missing required field
        response = client.post(
            "/api/v1/notify",
            json={"channel": "alerts"},  # Missing message
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 422

    def test_notify_with_card(
        self,
        client: TestClient,
        api_key: str,
    ) -> None:
        """Test notification with card type."""
        mock_notification = Notification(
            channel="alerts",
            message="Test",
            card_type="alert",
        )
        mock_notification.mark_sent()

        mock_service = MagicMock()
        mock_service.notify = AsyncMock(return_value=mock_notification)

        with patch("src.api.notifier_api.get_service", return_value=mock_service):
            response = client.post(
                "/api/v1/notify",
                json={
                    "channel": "alerts",
                    "message": "Alert message",
                    "title": "System Alert",
                    "card_type": "alert",
                    "priority": "critical",
                },
                headers={"X-API-Key": api_key},
            )

        assert response.status_code == 200
        mock_service.notify.assert_called_once()
        call_kwargs = mock_service.notify.call_args[1]
        assert call_kwargs["card_type"] == "alert"
        assert call_kwargs["priority"] == "critical"
