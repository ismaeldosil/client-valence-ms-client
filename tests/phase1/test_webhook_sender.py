"""
Tests for WebhookSender.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.exceptions import TeamsError
from src.teams.sender.webhook_sender import WebhookSender


class TestWebhookSender:
    """Tests for WebhookSender class."""

    @pytest.fixture
    def sender(self) -> WebhookSender:
        """Create a WebhookSender instance."""
        return WebhookSender(timeout=5.0, max_retries=2, retry_delay=0.1)

    @pytest.fixture
    def webhook_url(self) -> str:
        """Sample webhook URL."""
        return "https://outlook.office.com/webhook/test-webhook-url"

    @pytest.mark.asyncio
    async def test_send_text_success(self, sender: WebhookSender, webhook_url: str) -> None:
        """Test successful text message send."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(sender, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await sender.send_text(webhook_url, "Hello Teams!")

            assert result is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == webhook_url
            assert call_args[1]["json"] == {"text": "Hello Teams!"}

    @pytest.mark.asyncio
    async def test_send_card_success(self, sender: WebhookSender, webhook_url: str) -> None:
        """Test successful Adaptive Card send."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        card = {
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [{"type": "TextBlock", "text": "Test"}],
        }

        with patch.object(sender, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await sender.send_card(webhook_url, card)

            assert result is True
            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert payload["type"] == "message"
            assert (
                payload["attachments"][0]["contentType"]
                == "application/vnd.microsoft.card.adaptive"
            )
            assert payload["attachments"][0]["content"] == card

    @pytest.mark.asyncio
    async def test_send_retry_on_server_error(
        self, sender: WebhookSender, webhook_url: str
    ) -> None:
        """Test retry on 5xx errors."""
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Internal Server Error"

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200

        with patch.object(sender, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.side_effect = [mock_response_fail, mock_response_success]
            mock_get_client.return_value = mock_client

            result = await sender.send_text(webhook_url, "Test")

            assert result is True
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_send_fails_after_retries(self, sender: WebhookSender, webhook_url: str) -> None:
        """Test failure after exhausting retries."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"

        with patch.object(sender, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            with pytest.raises(TeamsError) as exc_info:
                await sender.send_text(webhook_url, "Test")

            assert "Failed to send after 2 attempts" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_no_retry_on_client_error(
        self, sender: WebhookSender, webhook_url: str
    ) -> None:
        """Test no retry on 4xx errors."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch.object(sender, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            with pytest.raises(TeamsError):
                await sender.send_text(webhook_url, "Test")

            # Should only try once for client errors
            assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_close(self, sender: WebhookSender) -> None:
        """Test close method."""
        mock_client = AsyncMock()
        sender._client = mock_client
        await sender.close()
        mock_client.aclose.assert_called_once()
        assert sender._client is None
