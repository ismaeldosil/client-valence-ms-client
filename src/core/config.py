"""
Configuration module.

Centralized configuration using pydantic-settings.
All settings are loaded from environment variables or .env file.
"""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized project configuration."""

    # Core
    environment: str = "development"
    log_level: str = "INFO"

    # Mock servers (Phase 0)
    mock_agent_port: int = 8080
    mock_webhook_port: int = 3000

    # Teams real (optional in Phase 0)
    teams_workflow_url: Optional[str] = None

    # Phase 1: Notifications (Power Automate Workflows)
    teams_workflow_alerts: Optional[str] = None
    teams_workflow_reports: Optional[str] = None
    teams_workflow_general: Optional[str] = None
    notifier_api_key: str = "dev-api-key"
    notifier_port: int = 8001

    # Phase 2: Queries (Outgoing Webhooks)
    teams_hmac_secret: Optional[str] = None
    receiver_port: int = 3000
    agent_base_url: str = "http://localhost:8000"
    agent_api_key: Optional[str] = None
    agent_timeout: float = 4.5  # Must be < 5s for Teams Outgoing Webhooks
    agent_max_retries: int = 1  # Limited retries due to Teams timeout

    # Phase 3: Memory
    session_store: str = "memory"
    session_ttl_hours: int = 24
    session_max_messages: int = 50
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton instance
settings = Settings()
