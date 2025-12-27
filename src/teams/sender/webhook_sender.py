"""
Webhook Sender for Microsoft Teams.

Sends messages to Teams channels via Incoming Webhooks.
"""

import asyncio
from typing import Optional

import httpx
import structlog

from ...core.exceptions import TeamsError
from .base import TeamsSender

logger = structlog.get_logger()


class WebhookSender(TeamsSender):
    """
    Sends messages to Microsoft Teams using Incoming Webhooks.

    Features:
    - Simple text messages
    - Adaptive Cards
    - Retry logic with exponential backoff
    - Timeout handling

    Usage:
        sender = WebhookSender()
        await sender.send_text(webhook_url, "Hello Teams!")
        await sender.close()
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the webhook sender.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def send_text(self, webhook_url: str, text: str) -> bool:
        """
        Send a simple text message to Teams.

        Args:
            webhook_url: The Incoming Webhook URL
            text: Plain text message

        Returns:
            True if sent successfully
        """
        payload = {"text": text}
        return await self._post_with_retry(webhook_url, payload)

    async def send_card(self, webhook_url: str, card: dict) -> bool:
        """
        Send an Adaptive Card to Teams.

        Args:
            webhook_url: The Incoming Webhook URL
            card: Adaptive Card content

        Returns:
            True if sent successfully

        Note:
            Card must follow Adaptive Cards schema v1.4
            Only 'openURL' action is supported
        """
        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": card,
                }
            ],
        }
        return await self._post_with_retry(webhook_url, payload)

    async def _post_with_retry(self, webhook_url: str, payload: dict) -> bool:
        """
        POST to webhook with retry and exponential backoff.

        Args:
            webhook_url: Target URL
            payload: JSON payload

        Returns:
            True if successful

        Raises:
            TeamsError: If all retries fail
        """
        client = await self._get_client()
        last_error: Optional[str] = None
        delay = self.retry_delay

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await client.post(webhook_url, json=payload)

                if response.status_code == 200:
                    logger.info(
                        "teams_message_sent",
                        attempt=attempt,
                        url_preview=webhook_url[:50],
                    )
                    return True

                # Handle specific error codes
                if response.status_code == 429:
                    # Rate limited - wait longer
                    retry_after = int(response.headers.get("Retry-After", delay * 2))
                    logger.warning(
                        "teams_rate_limited",
                        attempt=attempt,
                        retry_after=retry_after,
                    )
                    await asyncio.sleep(retry_after)
                    continue

                if response.status_code >= 400 and response.status_code < 500:
                    # Client error - don't retry
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    logger.error(
                        "teams_client_error",
                        status=response.status_code,
                        response=response.text[:200],
                    )
                    break

                # Server error - retry
                last_error = f"HTTP {response.status_code}: {response.text}"
                logger.warning(
                    "teams_send_retry",
                    attempt=attempt,
                    status=response.status_code,
                )

            except httpx.TimeoutException as e:
                last_error = f"Timeout: {e}"
                logger.warning(
                    "teams_timeout",
                    attempt=attempt,
                    timeout=self.timeout,
                )

            except httpx.ConnectError as e:
                last_error = f"Connection error: {e}"
                logger.warning(
                    "teams_connection_error",
                    attempt=attempt,
                    error=str(e),
                )

            except Exception as e:
                last_error = f"Unexpected error: {e}"
                logger.error(
                    "teams_unexpected_error",
                    attempt=attempt,
                    error=str(e),
                )

            # Wait before retry with exponential backoff
            if attempt < self.max_retries:
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff

        raise TeamsError(f"Failed to send after {self.max_retries} attempts: {last_error}")

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.debug("teams_sender_closed")
