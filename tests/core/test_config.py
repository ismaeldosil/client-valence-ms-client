"""Tests for configuration module."""

import os
from unittest.mock import patch

from src.core.config import Settings


class TestSettings:
    """Tests for Settings configuration."""

    def test_default_values(self):
        """Test default configuration values by creating Settings with explicit _env_file=None."""
        settings = Settings(_env_file=None)

        assert settings.environment == "development"
        assert settings.log_level == "INFO"
        assert settings.mock_agent_port == 8080
        assert settings.mock_webhook_port == 3000
        assert settings.receiver_port == 3000
        assert settings.agent_base_url == "http://localhost:8000"
        assert settings.agent_timeout == 4.5
        assert settings.agent_max_retries == 1

    def test_environment_override(self):
        """Test that environment variables override defaults."""
        env_vars = {
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "DEBUG",
            "AGENT_BASE_URL": "http://agent.example.com",
            "AGENT_TIMEOUT": "10.0",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings(_env_file=None)

            assert settings.environment == "production"
            assert settings.log_level == "DEBUG"
            assert settings.agent_base_url == "http://agent.example.com"
            assert settings.agent_timeout == 10.0

    def test_optional_fields_default_none(self):
        """Test that optional fields default to None when no env vars set."""
        settings = Settings(_env_file=None)

        assert settings.teams_workflow_url is None
        assert settings.teams_hmac_secret is None
        assert settings.agent_api_key is None

    def test_phase1_settings(self):
        """Test Phase 1 notification settings."""
        env_vars = {
            "TEAMS_WORKFLOW_ALERTS": "https://webhook.alerts",
            "TEAMS_WORKFLOW_REPORTS": "https://webhook.reports",
            "NOTIFIER_API_KEY": "secret-key",
            "NOTIFIER_PORT": "9000",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings(_env_file=None)

            assert settings.teams_workflow_alerts == "https://webhook.alerts"
            assert settings.teams_workflow_reports == "https://webhook.reports"
            assert settings.notifier_api_key == "secret-key"
            assert settings.notifier_port == 9000

    def test_phase2_settings(self):
        """Test Phase 2 outgoing webhook settings."""
        env_vars = {
            "TEAMS_HMAC_SECRET": "base64secret",
            "RECEIVER_PORT": "4000",
            "AGENT_MAX_RETRIES": "3",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings(_env_file=None)

            assert settings.teams_hmac_secret == "base64secret"
            assert settings.receiver_port == 4000
            assert settings.agent_max_retries == 3

    def test_phase3_settings(self):
        """Test Phase 3 session settings."""
        env_vars = {
            "SESSION_STORE": "redis",
            "SESSION_TTL_HOURS": "48",
            "SESSION_MAX_MESSAGES": "100",
            "REDIS_URL": "redis://redis.example.com:6379/1",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings(_env_file=None)

            assert settings.session_store == "redis"
            assert settings.session_ttl_hours == 48
            assert settings.session_max_messages == 100
            assert settings.redis_url == "redis://redis.example.com:6379/1"

    def test_extra_env_vars_ignored(self):
        """Test that extra environment variables are ignored."""
        env_vars = {
            "UNKNOWN_SETTING": "value",
            "ANOTHER_UNKNOWN": "123",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings(_env_file=None)
            assert not hasattr(settings, "unknown_setting")
