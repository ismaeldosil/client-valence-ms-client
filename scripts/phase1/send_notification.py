#!/usr/bin/env python3
"""
Send Notification Script.

Send notifications to Teams channels via the Notifier API or directly.

Usage:
    # Via API (requires API to be running)
    python scripts/phase1/send_notification.py --channel alerts --message "Test"

    # Direct (requires webhook URL in env)
    python scripts/phase1/send_notification.py --direct --message "Test"

    # With card
    python scripts/phase1/send_notification.py --channel alerts --message "Alert!" \\
        --title "System Alert" --card alert --priority critical
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx

from src.core.config import settings
from src.teams.sender.webhook_sender import WebhookSender
from src.teams.sender.cards import AdaptiveCardBuilder


async def send_via_api(
    channel: str,
    message: str,
    title: str = None,
    card_type: str = None,
    priority: str = "medium",
) -> None:
    """Send notification via the API."""
    api_url = f"http://localhost:{settings.notifier_port}/api/v1/notify"

    payload = {
        "channel": channel,
        "message": message,
        "priority": priority,
    }

    if title:
        payload["title"] = title
    if card_type:
        payload["card_type"] = card_type

    async with httpx.AsyncClient() as client:
        response = await client.post(
            api_url,
            json=payload,
            headers={"X-API-Key": settings.notifier_api_key},
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Notification sent: {data['notification_id']}")
        else:
            print(f"[ERROR] {response.status_code}: {response.text}")


async def send_direct(
    message: str,
    title: str = None,
    card_type: str = None,
    priority: str = "medium",
    webhook_url: str = None,
) -> None:
    """Send notification directly to webhook."""
    url = webhook_url or settings.teams_workflow_url

    if not url:
        print("[ERROR] No workflow URL. Set TEAMS_WORKFLOW_URL or use --webhook")
        return

    sender = WebhookSender()

    try:
        if card_type:
            builder = AdaptiveCardBuilder()
            card = builder.build(
                card_type=card_type,
                title=title or "Notification",
                message=message,
                priority=priority,
            )
            await sender.send_card(url, card)
        else:
            text = message
            if title:
                text = f"**{title}**\n\n{message}"
            await sender.send_text(url, text)

        print("[OK] Notification sent directly to webhook")

    finally:
        await sender.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Send notification to Teams")

    parser.add_argument("--channel", "-c", help="Channel name (for API mode)")
    parser.add_argument("--message", "-m", required=True, help="Notification message")
    parser.add_argument("--title", "-t", help="Notification title")
    parser.add_argument(
        "--card",
        choices=["alert", "info", "report"],
        help="Card type",
    )
    parser.add_argument(
        "--priority",
        "-p",
        choices=["low", "medium", "high", "critical"],
        default="medium",
        help="Priority level",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Send directly to webhook (bypass API)",
    )
    parser.add_argument("--webhook", help="Webhook URL (for direct mode)")

    args = parser.parse_args()

    if args.direct:
        asyncio.run(
            send_direct(
                message=args.message,
                title=args.title,
                card_type=args.card,
                priority=args.priority,
                webhook_url=args.webhook,
            )
        )
    else:
        if not args.channel:
            print("[ERROR] --channel required for API mode")
            sys.exit(1)

        asyncio.run(
            send_via_api(
                channel=args.channel,
                message=args.message,
                title=args.title,
                card_type=args.card,
                priority=args.priority,
            )
        )


if __name__ == "__main__":
    main()
