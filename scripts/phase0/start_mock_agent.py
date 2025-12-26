#!/usr/bin/env python
"""
Start the Mock Agent Server.

Usage:
    python scripts/phase0/start_mock_agent.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uvicorn

from tests.mocks.mock_agent_server import app


def main() -> None:
    print("=" * 60)
    print("  Mock Agent Server")
    print("=" * 60)
    print()
    print("  URL: http://localhost:8080")
    print()
    print("  Endpoints:")
    print("  - GET  /health  - Health check")
    print("  - POST /query   - Query the agent")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
