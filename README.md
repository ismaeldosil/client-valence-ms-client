# Teams Agent Integration Client

Microsoft Teams integration client for AI Agent communication.

## Features

### Phase 0 - Testing & Mocks
- Mock Agent Server (port 8080)
- Mock Webhook Receiver (port 3000)
- Knowledge Base with test responses
- Postman Collection

### Phase 1 - Notifications (Agent → Teams)
- Power Automate Workflow integration (replaces deprecated Incoming Webhooks)
- Adaptive Cards builder (alert, info, report)
- Notification Service with channel registry
- Notifier API with authentication

### Phase 2 - Queries Stateless (Teams → Agent)
- Webhook Receiver for Teams Outgoing Webhooks (port 3001)
- HMAC-SHA256 signature verification
- Agent Client for forwarding queries
- Commands: `/help`, `/status`, `/clear`

## Project Structure

```
client-valence-ms-client/
├── src/
│   ├── core/                   # Core modules (config, logging, exceptions)
│   ├── teams/
│   │   ├── sender/             # Phase 1: Teams sender (Adaptive Cards)
│   │   └── receiver/           # Phase 2: Webhook receiver (HMAC, handler)
│   ├── agent/                  # Phase 2: Agent client
│   ├── notifier/               # Phase 1: Notification service
│   └── api/                    # APIs (notifier, receiver)
├── tests/
│   ├── mocks/                  # Mock servers
│   ├── phase0/                 # Phase 0 tests
│   └── phase1/                 # Phase 1 tests
├── scripts/
│   ├── phase0/                 # Mock server scripts
│   ├── phase1/                 # Notification scripts
│   └── phase2/                 # Receiver scripts
├── postman/                    # Postman collection & environments
├── requirements/               # Dependencies
└── docs/                       # Documentation
```

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/REEA-Global/client-valence-ms-client.git
cd client-valence-ms-client

# Run setup script
./scripts/setup.sh

# Or manually
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/base.txt
cp .env.example .env
```

### Running Servers

```bash
# Activate virtual environment
source .venv/bin/activate

# Phase 0: Start mock servers
python scripts/phase0/start_mock_agent.py &    # port 8080
python scripts/phase0/start_mock_webhook.py &  # port 3000

# Phase 1: Start Notifier API
python scripts/phase1/start_notifier_api.py &  # port 8001

# Phase 2: Start Webhook Receiver (requires HTTPS tunnel for Teams)
python scripts/phase2/start_receiver.py &      # port 3001

# For local testing with Teams, expose via tunnel:
cloudflared tunnel --url http://localhost:3001
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run Phase 0 endpoints demo
python scripts/phase0/run_all_endpoints.py

# Run interactive MS Teams client
python scripts/phase0/msteams_client.py

# Send notification (Phase 1)
python scripts/phase1/send_notification.py --channel alerts --message "Test" --card alert
```

## Configuration

Environment variables (`.env`):

```bash
# Environment
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Phase 0: Mock Servers
MOCK_AGENT_PORT=8080
MOCK_WEBHOOK_PORT=3000

# Phase 1: Power Automate Workflow URLs
# For local testing, use mock webhook. For production, use Power Automate URLs.
TEAMS_WORKFLOW_ALERTS=http://localhost:3000/webhook
TEAMS_WORKFLOW_REPORTS=http://localhost:3000/webhook
TEAMS_WORKFLOW_GENERAL=http://localhost:3000/webhook
NOTIFIER_API_KEY=dev-api-key
NOTIFIER_PORT=8001
```

> **Note:** Legacy Incoming Webhooks (Office 365 Connectors) were deprecated by Microsoft in 2025. This project uses Power Automate Workflows for Teams integration.

## Servers

| Server | Port | Phase | Description |
|--------|------|-------|-------------|
| Mock Agent | 8080 | 0 | Simulates AI Agent |
| Mock Webhook | 3000 | 0 | Simulates Teams webhook receiver |
| Notifier API | 8001 | 1 | Sends notifications to Teams |
| Webhook Receiver | 3001 | 2 | Receives messages from Teams |

## Documentation

- **[API Reference](docs/api-reference.md)** - Endpoints, request/response formats
- **Swagger UI**:
  - Agent: http://localhost:8080/docs
  - Webhook: http://localhost:3000/docs
  - Notifier: http://localhost:8001/docs
- **Postman Collection**: Import `postman/teams-agent-integration.postman_collection.json`

## Development Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Testing & Mocks | Complete |
| 1 | Notifications (Agent → Teams) | Complete |
| 2 | Queries Stateless (Teams → Agent) | Complete |
| 3 | Queries with Memory | Pending |

## Known Limitations

- **5-second timeout**: Teams Outgoing Webhooks require responses within 5 seconds
- **Shared Channels**: Outgoing Webhooks don't work in Shared Channels (Microsoft limitation)
- **Standard Channels only**: Bot can only be @mentioned in standard Team channels

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Mock servers
- **Pydantic** - Configuration and validation
- **Structlog** - Structured logging
- **HTTPX** - Async HTTP client
- **Pytest** - Testing framework

## License

Private - All rights reserved.
