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
    teams_incoming_webhook: Optional[str] = None

    # Phase 1: Notifications
    teams_webhook_alerts: Optional[str] = None
    teams_webhook_reports: Optional[str] = None
    teams_webhook_general: Optional[str] = None
    notifier_api_key: str = "dev-api-key"
    notifier_port: int = 8001

    # Phase 2: Queries
    teams_webhook_secret: Optional[str] = None
    receiver_port: int = 3000
    agent_protocol: str = "rest"
    agent_base_url: Optional[str] = None
    agent_api_key: Optional[str] = None
    agent_timeout: float = 30.0

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
