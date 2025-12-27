"""HTTP client for communicating with the AI Agent API."""

from types import TracebackType
from typing import Any

import httpx
import structlog

from .models import ChatRequest, ChatResponse, SessionResponse

logger = structlog.get_logger(__name__)


class AgentClientError(Exception):
    """Base exception for agent client errors."""

    pass


class AgentTimeoutError(AgentClientError):
    """Raised when agent request times out."""

    pass


class AgentConnectionError(AgentClientError):
    """Raised when connection to agent fails."""

    pass


class AgentAPIError(AgentClientError):
    """Raised when agent returns an error response."""

    def __init__(self, message: str, status_code: int, detail: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class AgentClient:
    """Async HTTP client for the AI Agent API.

    Handles communication with the agent's chat and session endpoints.
    Implements retry logic, timeout handling, and structured logging.

    Example:
        async with AgentClient(base_url="http://localhost:8000") as client:
            response = await client.chat("What suppliers do heat treatment?")
            print(response.message)
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        """Initialize the agent client.

        Args:
            base_url: Base URL of the agent API (e.g., http://localhost:8000)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds (default 30s)
            max_retries: Maximum retry attempts for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AgentClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> dict[str, Any]:
        """Check agent health status.

        Returns:
            Health status dictionary

        Raises:
            AgentConnectionError: If connection fails
        """
        client = await self._ensure_client()
        try:
            response = await client.get("/health")
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except httpx.ConnectError as e:
            raise AgentConnectionError(f"Failed to connect to agent: {e}") from e
        except httpx.HTTPStatusError as e:
            raise AgentAPIError(
                f"Health check failed: {e}",
                status_code=e.response.status_code,
            ) from e

    async def chat(
        self,
        message: str,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> ChatResponse:
        """Send a chat message to the agent.

        Args:
            message: The user's message
            session_id: Optional session ID for conversation continuity
            user_id: Optional user identifier

        Returns:
            ChatResponse with agent's reply

        Raises:
            AgentTimeoutError: If request times out
            AgentConnectionError: If connection fails
            AgentAPIError: If agent returns an error
        """
        request = ChatRequest(
            message=message,
            session_id=session_id,
            user_id=user_id,
        )

        log = logger.bind(
            message_preview=message[:50] + "..." if len(message) > 50 else message,
            session_id=session_id,
            user_id=user_id,
        )

        client = await self._ensure_client()
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                log.debug("sending_chat_request", attempt=attempt + 1)

                response = await client.post(
                    "/api/v1/chat",
                    json=request.to_dict(),
                )

                if response.status_code == 200:
                    data = response.json()
                    result = ChatResponse.from_dict(data)
                    log.info(
                        "chat_response_received",
                        response_session_id=result.session_id,
                        intent=result.intent,
                        confidence=result.confidence,
                        agents_count=len(result.agents_executed),
                    )
                    return result

                # Handle specific error codes
                if response.status_code == 422:
                    detail = response.json().get("detail", "Validation error")
                    raise AgentAPIError(
                        "Invalid request",
                        status_code=422,
                        detail=str(detail),
                    )

                if response.status_code == 429:
                    log.warning("rate_limited", attempt=attempt + 1)
                    if attempt < self.max_retries:
                        import asyncio

                        await asyncio.sleep(2**attempt)
                        continue

                response.raise_for_status()

            except httpx.TimeoutException as e:
                last_error = AgentTimeoutError(f"Request timed out after {self.timeout}s")
                log.warning("request_timeout", attempt=attempt + 1, error=str(e))
                if attempt < self.max_retries:
                    continue

            except httpx.ConnectError as e:
                last_error = AgentConnectionError(f"Failed to connect: {e}")
                log.error("connection_failed", attempt=attempt + 1, error=str(e))
                break  # Don't retry connection errors

            except httpx.HTTPStatusError as e:
                last_error = AgentAPIError(
                    f"Agent returned error: {e}",
                    status_code=e.response.status_code,
                )
                log.error(
                    "api_error",
                    status_code=e.response.status_code,
                    attempt=attempt + 1,
                )
                break  # Don't retry HTTP errors

        if last_error:
            raise last_error

        raise AgentAPIError("Unexpected error", status_code=500)

    async def get_session(self, session_id: str) -> SessionResponse:
        """Get session details and history.

        Args:
            session_id: The session identifier

        Returns:
            SessionResponse with session details

        Raises:
            AgentAPIError: If session not found or error occurs
        """
        client = await self._ensure_client()
        log = logger.bind(session_id=session_id)

        try:
            response = await client.get(f"/api/v1/sessions/{session_id}")

            if response.status_code == 404:
                raise AgentAPIError(
                    f"Session not found: {session_id}",
                    status_code=404,
                )

            response.raise_for_status()
            data = response.json()
            result = SessionResponse.from_dict(data)
            log.debug("session_retrieved", message_count=result.message_count)
            return result

        except httpx.HTTPStatusError as e:
            raise AgentAPIError(
                f"Failed to get session: {e}",
                status_code=e.response.status_code,
            ) from e

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: The session identifier

        Returns:
            True if deleted successfully

        Raises:
            AgentAPIError: If deletion fails
        """
        client = await self._ensure_client()
        log = logger.bind(session_id=session_id)

        try:
            response = await client.delete(f"/api/v1/sessions/{session_id}")
            response.raise_for_status()
            log.info("session_deleted")
            return True

        except httpx.HTTPStatusError as e:
            raise AgentAPIError(
                f"Failed to delete session: {e}",
                status_code=e.response.status_code,
            ) from e
