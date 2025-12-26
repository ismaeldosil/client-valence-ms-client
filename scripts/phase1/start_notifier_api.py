#!/usr/bin/env python3
"""
Start Notifier API.

Usage:
    python scripts/phase1/start_notifier_api.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uvicorn

from src.core.config import settings


def main() -> None:
    print("=" * 60)
    print("  Teams Notifier API")
    print("=" * 60)
    print()
    print(f"  URL: http://localhost:{settings.notifier_port}")
    print()
    print("  Endpoints:")
    print("  - GET  /health           - Health check")
    print("  - POST /api/v1/notify    - Send notification")
    print("  - GET  /api/v1/channels  - List channels")
    print()
    print(f"  Docs: http://localhost:{settings.notifier_port}/docs")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    uvicorn.run(
        "src.api.notifier_api:app",
        host="0.0.0.0",
        port=settings.notifier_port,
        reload=settings.environment == "development",
    )


if __name__ == "__main__":
    main()
