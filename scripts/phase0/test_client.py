#!/usr/bin/env python
"""
Test client for Teams Agent Integration.

Allows testing:
- Health checks of all services
- Query to mock agent
- Simulate Teams messages

Usage:
    python scripts/phase0/test_client.py
"""

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx


@dataclass
class TestClient:
    """Test client for mock services."""

    agent_url: str = "http://localhost:8080"
    webhook_url: str = "http://localhost:3000"

    async def check_health(self) -> dict[str, bool]:
        """
        Check health of all services.

        Returns:
            Dict with status of each service
        """
        results = {}

        async with httpx.AsyncClient() as client:
            # Check agent
            try:
                r = await client.get(f"{self.agent_url}/health", timeout=5.0)
                results["agent"] = r.status_code == 200
            except Exception:
                results["agent"] = False

            # Check webhook
            try:
                r = await client.get(f"{self.webhook_url}/health", timeout=5.0)
                results["webhook"] = r.status_code == 200
            except Exception:
                results["webhook"] = False

        return results

    async def query_agent(
        self,
        message: str,
        history: Optional[list[dict]] = None,
    ) -> dict:
        """
        Query the mock agent.

        Args:
            message: Message to send
            history: Optional conversation history

        Returns:
            Agent response
        """
        payload = {
            "message": message,
            "context": {"platform": "test"},
        }
        if history:
            payload["conversation_history"] = history

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.agent_url}/query",
                json=payload,
                timeout=30.0,
            )
            return r.json()

    async def simulate_teams_message(
        self,
        text: str,
        user_name: str = "Test User",
    ) -> dict:
        """
        Simulate a Teams message to the webhook.

        Args:
            text: Message text (without @mention)
            user_name: User name

        Returns:
            Webhook response
        """
        payload = {
            "type": "message",
            "id": "test-msg-001",
            "text": f"<at>Bot</at> {text}",
            "from": {
                "id": "test-user-001",
                "name": user_name,
            },
            "conversation": {
                "id": "test-conv-001",
            },
        }

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.webhook_url}/webhook",
                json=payload,
                timeout=30.0,
            )
            return r.json()


async def main() -> None:
    """Demo the test client."""
    client = TestClient()

    print("=" * 60)
    print("  Test Client Demo")
    print("=" * 60)

    # Health checks
    print("\n[1] Health Checks")
    print("-" * 40)
    health = await client.check_health()
    for service, status in health.items():
        icon = "OK" if status else "FAIL"
        state = "healthy" if status else "unreachable"
        print(f"  [{icon}] {service}: {state}")

    if not all(health.values()):
        print("\n  Some services are not running.")
        print("  Start them with:")
        print("    python scripts/phase0/start_mock_agent.py")
        print("    python scripts/phase0/start_mock_webhook.py")
        return

    # Query agent
    print("\n[2] Query Agent")
    print("-" * 40)
    message = "Cual es la politica de vacaciones?"
    response = await client.query_agent(message)
    print(f"  Message: {message}")
    print(f"  Response: {response['text'][:80]}...")
    print(f"  Confidence: {response['confidence']}")
    print(f"  Processing: {response['processing_time_ms']}ms")

    # Query agent - unknown
    print("\n[3] Query Agent (Unknown)")
    print("-" * 40)
    message = "Cual es el color del cielo?"
    response = await client.query_agent(message)
    print(f"  Message: {message}")
    print(f"  Response: {response['text'][:80]}...")
    print(f"  Confidence: {response['confidence']}")

    # Simulate Teams message
    print("\n[4] Simulate Teams Message")
    print("-" * 40)
    response = await client.simulate_teams_message("Hola, como estas?")
    print(f"  Message: Hola, como estas?")
    print(f"  Response: {response['text']}")

    # Test command
    print("\n[5] Test Command (/help)")
    print("-" * 40)
    response = await client.simulate_teams_message("/help")
    print(f"  Response: {response['text'][:100]}...")

    print("\n" + "=" * 60)
    print("  Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
