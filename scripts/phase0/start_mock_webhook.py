#!/usr/bin/env python
"""
Start the Mock Webhook Receiver.

Usage:
    python scripts/phase0/start_mock_webhook.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uvicorn

from tests.mocks.mock_webhook_receiver import app


def main() -> None:
    print("=" * 60)
    print("  Mock Webhook Receiver")
    print("=" * 60)
    print()
    print("  URL: http://localhost:3000")
    print()
    print("  Endpoints:")
    print("  - GET  /health   - Health check")
    print("  - POST /webhook  - Receive Teams message")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    uvicorn.run(app, host="0.0.0.0", port=3000)


if __name__ == "__main__":
    main()
