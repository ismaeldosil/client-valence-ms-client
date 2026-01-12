#!/usr/bin/env python3
"""Start the MS Teams Client Dashboard.

Usage:
    python scripts/start_dashboard.py [--port PORT] [--host HOST]

Example:
    python scripts/start_dashboard.py
    python scripts/start_dashboard.py --port 8004
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn

from src.dashboard import create_dashboard_app


def main():
    parser = argparse.ArgumentParser(description="Start the MS Teams Client Dashboard")
    parser.add_argument("--port", type=int, default=8004, help="Port to run on (default: 8004)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print("  Valerie MS Teams Client - Dashboard")
    print(f"{'='*50}")
    print(f"  URL: http://localhost:{args.port}")
    print(f"  API: http://localhost:{args.port}/api/status")
    print(f"{'='*50}\n")

    app = create_dashboard_app()

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
