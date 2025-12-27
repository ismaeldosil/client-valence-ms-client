# Usage Guide

This guide explains how to set up and use the Microsoft Teams integration client.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Services](#running-the-services)
5. [Sending Notifications (Agent → Teams)](#sending-notifications-agent--teams)
6. [Receiving Queries (Teams → Agent)](#receiving-queries-teams--agent)
7. [Development Workflow](#development-workflow)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Python 3.11+
- pip
- Microsoft Teams with admin access
- Power Automate Workflows configured (see setup guides)
- Outgoing Webhook configured (see setup guides)

---

## Installation

```bash
# Clone the repository
git clone git@github.com:REEA-Global-LLC/client-valence-ms-client.git
cd client-valence-ms-client

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install base dependencies
pip install -r requirements/base.txt

# Install development dependencies (includes testing tools)
pip install -r requirements/dev.txt

# Copy environment file
cp .env.example .env

# Install pre-commit hooks (recommended)
pre-commit install
pre-commit install --hook-type pre-push
```

---

## Configuration

Edit the `.env` file with your settings:

```bash
# Environment
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Notifications (Agent → Teams)
# Get these URLs from Power Automate Workflows
TEAMS_WORKFLOW_ALERTS=https://...powerplatform.com/.../workflows/...
TEAMS_WORKFLOW_REPORTS=https://...powerplatform.com/.../workflows/...
TEAMS_WORKFLOW_GENERAL=https://...powerplatform.com/.../workflows/...
NOTIFIER_API_KEY=your-secure-api-key
NOTIFIER_PORT=8001

# Queries (Teams → Agent)
AGENT_BASE_URL=http://localhost:8000      # Your AI Agent URL
AGENT_TIMEOUT=4.5                          # Must be < 5 seconds (Teams limit)
AGENT_MAX_RETRIES=1                        # Retry attempts
RECEIVER_PORT=3001
TEAMS_HMAC_SECRET=your-base64-secret       # From Outgoing Webhook creation
```

### Getting the Configuration Values

| Value | Source |
|-------|--------|
| `TEAMS_WORKFLOW_*` | Power Automate Workflow URLs (see setup guide) |
| `TEAMS_HMAC_SECRET` | Generated when creating Outgoing Webhook in Teams |
| `AGENT_BASE_URL` | Your AI Agent's API endpoint |

---

## Running the Services

### Notifier API (for sending notifications)

```bash
source .venv/bin/activate
python scripts/phase1/start_notifier_api.py
```

The API runs on `http://localhost:8001` by default.

### Webhook Receiver (for receiving queries)

```bash
source .venv/bin/activate
python scripts/phase2/start_receiver.py
```

The receiver runs on `http://localhost:3001` by default.

### Exposing the Receiver to the Internet

Teams requires an HTTPS URL. For development, use a tunnel:

```bash
# Using Cloudflare Tunnel (free, no account required)
cloudflared tunnel --url http://localhost:3001

# You'll get a URL like: https://random-words.trycloudflare.com
# Use this URL + /webhook when creating the Outgoing Webhook in Teams
```

For production, deploy behind a reverse proxy with SSL (nginx, AWS ALB, etc.)

---

## Sending Notifications (Agent → Teams)

### Using the Notifier API

**Send a notification:**

```bash
curl -X POST http://localhost:8001/api/v1/notify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{
    "channel": "alerts",
    "title": "High CPU Alert",
    "message": "Server CPU usage exceeded 90%",
    "card_type": "alert",
    "priority": "critical"
  }'
```

**Available channels:** `alerts`, `reports`, `general`

**Card types:** `alert`, `info`, `report`

**Priorities:** `low`, `medium`, `high`, `critical`

### Using Python

```python
import httpx

async def send_notification():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/v1/notify",
            headers={"X-API-Key": "your-secure-api-key"},
            json={
                "channel": "alerts",
                "title": "Alert Title",
                "message": "Alert message content",
                "card_type": "alert",
                "priority": "high"
            }
        )
        return response.json()
```

### List Available Channels

```bash
curl http://localhost:8001/api/v1/channels \
  -H "X-API-Key: your-secure-api-key"
```

---

## Receiving Queries (Teams → Agent)

Once the Outgoing Webhook is configured in Teams, users can interact with the bot:

### In Microsoft Teams

1. Go to any channel in the Team where the webhook was created
2. Type `@BotName` followed by your message:
   ```
   @Valerie find suppliers with Nadcap certification
   ```
3. The bot will respond in the channel (supports Spanish and English)

### Available Commands

| Command | Description |
|---------|-------------|
| `@Valerie hello` | Send a greeting |
| `@Valerie /help` | Show available commands |
| `@Valerie /status` | Check agent connection status |
| `@Valerie /clear` | Clear conversation history |

### How It Works

1. User mentions the bot in Teams
2. Teams sends the message to your receiver URL (`/webhook`)
3. Receiver verifies HMAC signature
4. Receiver forwards query to your AI Agent
5. Agent response is sent back to Teams
6. Response appears in the channel

---

## Development Workflow

### Quality Commands (Makefile)

```bash
# Linting and auto-fix
make lint

# Type checking with MyPy
make type-check

# Security scan with Bandit
make security

# Run tests with coverage
make test

# Full pre-push analysis (lint + types + security + tests)
make pre-push

# Find code without tests
make find-gaps

# Run all quality checks
make all
```

### Pre-commit Hooks

The project uses pre-commit hooks for quality assurance:

**On commit:**
- Ruff linting and formatting
- Trailing whitespace removal
- YAML validation

**On push:**
- Full static analysis (lint, type-check, security, tests)

```bash
# Install hooks
pre-commit install
pre-commit install --hook-type pre-push

# Run manually
pre-commit run --all-files
```

### CI/CD Pipeline

GitHub Actions runs on every push/PR to main:

| Job | Tool | Description |
|-----|------|-------------|
| Lint & Format | Ruff | Code style and formatting |
| Type Check | MyPy | Static type analysis |
| Security | Bandit | SAST vulnerability scan |
| Tests | Pytest | Unit/integration tests + coverage |

---

## Testing

### Run Tests

```bash
# All tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=src --cov-report=html

# Specific phase
pytest tests/phase2/ -v

# Single test file
pytest tests/phase2/test_handler.py -v
```

### Health Checks

```bash
# Notifier API
curl http://localhost:8001/health

# Webhook Receiver
curl http://localhost:3001/health
```

### Test Message (Development Only)

Send a test message without HMAC verification:

```bash
curl -X POST http://localhost:3001/api/v1/test-message \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-1",
    "text": "<at>Bot</at> Hello, how are you?",
    "from": {"id": "user-1", "name": "Test User"},
    "conversation": {"id": "conv-1"}
  }'
```

### Using Postman

Import the Postman collection and environment:

1. Open Postman
2. Import `postman/teams-agent-integration.postman_collection.json`
3. Import `postman/environments/local.postman_environment.json`
4. Select the "Microsoft Client - Environment" environment
5. Run the requests

### Test Coverage

Current coverage: **83%** (174 tests)

```bash
# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Check coverage threshold (must be >= 70%)
pytest tests/ --cov=src --cov-fail-under=70
```

---

## Troubleshooting

### Notifications not appearing in Teams

1. Verify the Workflow URL is correct in `.env`
2. Check the Notifier API logs for errors
3. Test the workflow directly in Power Automate

### Bot not responding in Teams

1. Check that the receiver is running and accessible via HTTPS
2. Verify the HMAC secret matches what Teams generated
3. Check receiver logs for incoming requests
4. Ensure the AI Agent is running and accessible

### "Request timed out" errors

Teams Outgoing Webhooks have a 5-second timeout. If your agent takes longer:
- Optimize agent response time
- Use simpler, more specific queries
- Consider implementing async responses

### HMAC verification failing

1. Ensure `TEAMS_HMAC_SECRET` is the exact Base64 string from Teams
2. Don't decode or modify the secret
3. Check that the request body hasn't been modified

### Pre-commit hook failures

```bash
# See what failed
pre-commit run --all-files

# Fix linting issues automatically
make lint

# Check type errors
make type-check
```

### Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 401 | Invalid HMAC signature | Check TEAMS_HMAC_SECRET |
| 400 | Invalid message format | Check request JSON structure |
| 503 | Agent unavailable | Verify AGENT_BASE_URL |
| 504 | Agent timeout | Query took > 5 seconds |

---

## API Reference

See [docs/api-reference.md](docs/api-reference.md) for detailed endpoint documentation.

## Support

For issues or questions, contact the development team.
