#!/usr/bin/env python
"""
Send message to Teams via Power Automate Workflow.

Usage:
    python scripts/phase0/send_to_teams.py "Your message"
    python scripts/phase0/send_to_teams.py --card "Title" "Message"
    python scripts/phase0/send_to_teams.py --dry-run "Test message"
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx

from src.core.config import settings


def send_text(webhook_url: str, text: str, dry_run: bool = False) -> bool:
    """Send simple text message."""
    payload = {"text": text}

    if dry_run:
        print(f"[DRY RUN] Would send to: {webhook_url[:50]}...")
        print(f"[DRY RUN] Payload: {payload}")
        return True

    response = httpx.post(webhook_url, json=payload, timeout=30.0)
    return response.status_code == 200


def send_card(
    webhook_url: str,
    title: str,
    message: str,
    dry_run: bool = False,
) -> bool:
    """Send Adaptive Card."""
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": title,
                            "weight": "Bolder",
                            "size": "Medium",
                        },
                        {
                            "type": "TextBlock",
                            "text": message,
                            "wrap": True,
                        },
                    ],
                },
            }
        ],
    }

    if dry_run:
        print(f"[DRY RUN] Would send to: {webhook_url[:50]}...")
        print(f"[DRY RUN] Card title: {title}")
        print(f"[DRY RUN] Card message: {message[:50]}...")
        return True

    response = httpx.post(webhook_url, json=payload, timeout=30.0)
    return response.status_code == 200


def main() -> None:
    parser = argparse.ArgumentParser(description="Send message to Teams")
    parser.add_argument("message", help="Message to send")
    parser.add_argument("--card", metavar="TITLE", help="Send as card with title")
    parser.add_argument("--webhook-url", help="Override webhook URL")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually send",
    )

    args = parser.parse_args()

    # Get workflow URL
    webhook_url = args.webhook_url or settings.teams_workflow_url

    if not webhook_url:
        print("[ERROR] No workflow URL configured.")
        print("  Set TEAMS_WORKFLOW_URL in .env or use --webhook-url")
        sys.exit(1)

    # Send message
    try:
        if args.card:
            success = send_card(
                webhook_url,
                args.card,
                args.message,
                args.dry_run,
            )
        else:
            success = send_text(webhook_url, args.message, args.dry_run)

        if success:
            print("[OK] Message sent successfully!")
        else:
            print("[ERROR] Failed to send message")
            sys.exit(1)

    except httpx.ConnectError:
        print("[ERROR] Could not connect to Teams webhook")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
