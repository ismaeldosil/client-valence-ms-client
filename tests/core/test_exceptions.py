"""Tests for custom exceptions."""

import pytest

from src.core.exceptions import (
    AgentConnectionError,
    AgentError,
    AgentTimeoutError,
    TeamsAgentError,
    TeamsError,
    WebhookVerificationError,
)


class TestTeamsAgentError:
    """Tests for base TeamsAgentError."""

    def test_default_message(self):
        """Test default error message."""
        error = TeamsAgentError()
        assert str(error) == "An error occurred"

    def test_custom_message(self):
        """Test custom error message."""
        error = TeamsAgentError("Custom error message")
        assert str(error) == "Custom error message"
        assert error.message == "Custom error message"

    def test_is_exception(self):
        """Test that it's a proper Exception."""
        error = TeamsAgentError("test")
        assert isinstance(error, Exception)


class TestAgentError:
    """Tests for AgentError."""

    def test_inheritance(self):
        """Test that AgentError inherits from TeamsAgentError."""
        error = AgentError("Agent failed")
        assert isinstance(error, TeamsAgentError)
        assert isinstance(error, Exception)


class TestAgentTimeoutError:
    """Tests for AgentTimeoutError."""

    def test_default_message(self):
        """Test default timeout message."""
        error = AgentTimeoutError()
        assert "timed out" in str(error).lower()

    def test_custom_message(self):
        """Test custom timeout message."""
        error = AgentTimeoutError("Request took 30 seconds")
        assert str(error) == "Request took 30 seconds"

    def test_inheritance(self):
        """Test inheritance chain."""
        error = AgentTimeoutError()
        assert isinstance(error, AgentError)
        assert isinstance(error, TeamsAgentError)


class TestAgentConnectionError:
    """Tests for AgentConnectionError."""

    def test_default_message(self):
        """Test default connection error message."""
        error = AgentConnectionError()
        assert "connect" in str(error).lower()

    def test_custom_message(self):
        """Test custom connection error message."""
        error = AgentConnectionError("Connection refused on port 8000")
        assert str(error) == "Connection refused on port 8000"

    def test_inheritance(self):
        """Test inheritance chain."""
        error = AgentConnectionError()
        assert isinstance(error, AgentError)
        assert isinstance(error, TeamsAgentError)


class TestTeamsError:
    """Tests for TeamsError."""

    def test_inheritance(self):
        """Test that TeamsError inherits from TeamsAgentError."""
        error = TeamsError("Teams issue")
        assert isinstance(error, TeamsAgentError)


class TestWebhookVerificationError:
    """Tests for WebhookVerificationError."""

    def test_default_message(self):
        """Test default verification error message."""
        error = WebhookVerificationError()
        assert "verification" in str(error).lower()

    def test_custom_message(self):
        """Test custom verification error message."""
        error = WebhookVerificationError("Invalid HMAC signature")
        assert str(error) == "Invalid HMAC signature"

    def test_inheritance(self):
        """Test inheritance chain."""
        error = WebhookVerificationError()
        assert isinstance(error, TeamsError)
        assert isinstance(error, TeamsAgentError)


class TestExceptionHierarchy:
    """Test the complete exception hierarchy."""

    def test_catch_all_with_base(self):
        """Test that base class catches all derived exceptions."""
        exceptions = [
            AgentTimeoutError(),
            AgentConnectionError(),
            WebhookVerificationError(),
        ]

        for exc in exceptions:
            try:
                raise exc
            except TeamsAgentError:
                assert True
            except Exception:
                pytest.fail(f"{type(exc).__name__} not caught by TeamsAgentError")

    def test_catch_agent_errors(self):
        """Test catching agent-specific errors."""
        agent_exceptions = [
            AgentTimeoutError("timeout"),
            AgentConnectionError("connection failed"),
        ]

        for exc in agent_exceptions:
            try:
                raise exc
            except AgentError:
                assert True
            except Exception:
                pytest.fail(f"{type(exc).__name__} not caught by AgentError")

    def test_catch_teams_errors(self):
        """Test catching teams-specific errors."""
        try:
            raise WebhookVerificationError("invalid")
        except TeamsError:
            assert True
        except Exception:
            pytest.fail("WebhookVerificationError not caught by TeamsError")
