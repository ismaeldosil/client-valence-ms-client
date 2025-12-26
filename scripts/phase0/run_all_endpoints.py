#!/usr/bin/env python3
"""
Run All Endpoints - Tests all mock server endpoints.

Usage:
    python scripts/phase0/run_all_endpoints.py
"""

import httpx
import json
from dataclasses import dataclass
from typing import Any


@dataclass
class EndpointResult:
    name: str
    method: str
    url: str
    status: int
    success: bool
    response: Any
    error: str | None = None


def print_header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def print_result(result: EndpointResult) -> None:
    status_icon = "[OK]" if result.success else "[FAIL]"
    print(f"\n{status_icon} {result.name}")
    print(f"    {result.method} {result.url}")
    print(f"    Status: {result.status}")
    if result.error:
        print(f"    Error: {result.error}")
    else:
        response_str = json.dumps(result.response, ensure_ascii=False, indent=2)
        # Truncate long responses
        if len(response_str) > 300:
            response_str = response_str[:300] + "..."
        for line in response_str.split('\n'):
            print(f"    {line}")


def run_endpoint(
    client: httpx.Client,
    name: str,
    method: str,
    url: str,
    json_data: dict | None = None
) -> EndpointResult:
    try:
        if method == "GET":
            response = client.get(url)
        else:
            response = client.post(url, json=json_data)

        return EndpointResult(
            name=name,
            method=method,
            url=url,
            status=response.status_code,
            success=response.status_code == 200,
            response=response.json()
        )
    except Exception as e:
        return EndpointResult(
            name=name,
            method=method,
            url=url,
            status=0,
            success=False,
            response=None,
            error=str(e)
        )


def main() -> None:
    agent_url = "http://localhost:8080"
    webhook_url = "http://localhost:3000"

    results: list[EndpointResult] = []

    with httpx.Client(timeout=10.0) as client:

        # ==========================================
        # HEALTH CHECKS
        # ==========================================
        print_header("Health Checks")

        results.append(run_endpoint(
            client, "Mock Agent Health", "GET", f"{agent_url}/health"
        ))
        print_result(results[-1])

        results.append(run_endpoint(
            client, "Mock Webhook Health", "GET", f"{webhook_url}/health"
        ))
        print_result(results[-1])

        # ==========================================
        # MOCK AGENT - QUERIES
        # ==========================================
        print_header("Mock Agent - Queries")

        # Query Simple
        results.append(run_endpoint(
            client, "Query - Simple (Saludo)", "POST", f"{agent_url}/query",
            {"message": "Hola, como estas?", "context": {"platform": "test"}}
        ))
        print_result(results[-1])

        # Query Vacaciones
        results.append(run_endpoint(
            client, "Query - Vacaciones", "POST", f"{agent_url}/query",
            {"message": "Cual es la politica de vacaciones?", "context": {"platform": "test"}}
        ))
        print_result(results[-1])

        # Query Horario
        results.append(run_endpoint(
            client, "Query - Horario", "POST", f"{agent_url}/query",
            {"message": "Cual es el horario de trabajo?", "context": {"platform": "test"}}
        ))
        print_result(results[-1])

        # Query Trabajo Remoto
        results.append(run_endpoint(
            client, "Query - Trabajo Remoto", "POST", f"{agent_url}/query",
            {"message": "Puedo trabajar desde casa?", "context": {"platform": "test"}}
        ))
        print_result(results[-1])

        # Query Beneficios
        results.append(run_endpoint(
            client, "Query - Beneficios", "POST", f"{agent_url}/query",
            {"message": "Cuales son los beneficios?", "context": {"platform": "test"}}
        ))
        print_result(results[-1])

        # Query Unknown
        results.append(run_endpoint(
            client, "Query - Unknown (Default)", "POST", f"{agent_url}/query",
            {"message": "Cual es el color del universo?", "context": {"platform": "test"}}
        ))
        print_result(results[-1])

        # Query with History
        results.append(run_endpoint(
            client, "Query - With History", "POST", f"{agent_url}/query",
            {
                "message": "Y si no los uso todos?",
                "context": {"platform": "test"},
                "conversation_history": [
                    {"role": "user", "content": "Cual es la politica de vacaciones?"},
                    {"role": "assistant", "content": "La politica permite 15 dias..."}
                ]
            }
        ))
        print_result(results[-1])

        # ==========================================
        # MOCK WEBHOOK - MESSAGES
        # ==========================================
        print_header("Mock Webhook - Messages")

        # Simple Message
        results.append(run_endpoint(
            client, "Message - Simple", "POST", f"{webhook_url}/webhook",
            {
                "type": "message",
                "id": "msg-001",
                "text": "Hola, como estas?",
                "from": {"id": "user-001", "name": "Test User"},
                "conversation": {"id": "conv-001"}
            }
        ))
        print_result(results[-1])

        # Message with Mention
        results.append(run_endpoint(
            client, "Message - With @Mention", "POST", f"{webhook_url}/webhook",
            {
                "type": "message",
                "id": "msg-002",
                "text": "<at>Bot</at> Cual es la politica de vacaciones?",
                "from": {"id": "user-001", "name": "Test User"},
                "conversation": {"id": "conv-001"}
            }
        ))
        print_result(results[-1])

        # Command /help
        results.append(run_endpoint(
            client, "Command - /help", "POST", f"{webhook_url}/webhook",
            {
                "type": "message",
                "id": "msg-003",
                "text": "/help",
                "from": {"id": "user-001", "name": "Test User"},
                "conversation": {"id": "conv-001"}
            }
        ))
        print_result(results[-1])

        # Command /clear
        results.append(run_endpoint(
            client, "Command - /clear", "POST", f"{webhook_url}/webhook",
            {
                "type": "message",
                "id": "msg-004",
                "text": "/clear",
                "from": {"id": "user-001", "name": "Test User"},
                "conversation": {"id": "conv-001"}
            }
        ))
        print_result(results[-1])

        # Command /history
        results.append(run_endpoint(
            client, "Command - /history", "POST", f"{webhook_url}/webhook",
            {
                "type": "message",
                "id": "msg-005",
                "text": "/history",
                "from": {"id": "user-001", "name": "Test User"},
                "conversation": {"id": "conv-001"}
            }
        ))
        print_result(results[-1])

        # Message without from (anonymous)
        results.append(run_endpoint(
            client, "Message - Anonymous (no from)", "POST", f"{webhook_url}/webhook",
            {
                "type": "message",
                "id": "msg-006",
                "text": "Mensaje anonimo",
                "conversation": {"id": "conv-002"}
            }
        ))
        print_result(results[-1])

    # ==========================================
    # SUMMARY
    # ==========================================
    print_header("Summary")

    passed = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)
    total = len(results)

    print(f"\n  Total:  {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    if failed > 0:
        print("\n  Failed endpoints:")
        for r in results:
            if not r.success:
                print(f"    - {r.name}: {r.error or f'Status {r.status}'}")

    print(f"\n{'=' * 60}\n")

    # Exit with error if any failed
    if failed > 0:
        exit(1)


if __name__ == "__main__":
    main()
