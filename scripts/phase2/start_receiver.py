#!/usr/bin/env python3
"""
Start the Teams Webhook Receiver.

This server receives messages from Teams Outgoing Webhooks,
processes them through the AI Agent, and returns responses.

Usage:
    python scripts/phase2/start_receiver.py

Environment:
    AGENT_BASE_URL - URL of the AI Agent API (default: http://localhost:8000)
    AGENT_API_KEY - API key for agent authentication (optional)
    AGENT_TIMEOUT - Request timeout in seconds (default: 4.5)
    TEAMS_HMAC_SECRET - Base64 HMAC secret from Teams (optional but recommended)
    RECEIVER_PORT - Port to run receiver on (default: 3000)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import uvicorn

from src.core.config import settings


def main():
    """Start the webhook receiver."""
    print("=" * 60)
    print("  Teams Webhook Receiver - Phase 2 (Stateless)")
    print("=" * 60)
    print()
    print(f"  Receiver URL: http://localhost:{settings.receiver_port}")
    print(f"  Agent URL:    {settings.agent_base_url}")
    print(f"  HMAC Enabled: {bool(settings.teams_hmac_secret)}")
    print(f"  Timeout:      {settings.agent_timeout}s")
    print()
    print("  Endpoints:")
    print("  - GET  /health         - Health check")
    print("  - POST /webhook        - Teams Outgoing Webhook")
    print("  - POST /api/v1/test-message - Test endpoint (dev only)")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    uvicorn.run(
        "src.api.receiver_api:app",
        host="0.0.0.0",
        port=settings.receiver_port,
        reload=settings.environment == "development",
    )


if __name__ == "__main__":
    main()
