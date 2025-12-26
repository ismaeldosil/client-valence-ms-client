# Teams Agent Integration Client

Microsoft Teams integration client for AI Agent communication.

## Features

### Phase 0 - Testing & Mocks
- Mock Agent Server (port 8080)
- Mock Webhook Receiver (port 3000)
- Knowledge Base with test responses
- Postman Collection

### Phase 1 - Notifications (Agent → Teams)
- Incoming Webhook sender with retry logic
- Adaptive Cards builder (alert, info, report)
- Notification Service with channel registry
- Notifier API with authentication

## Project Structure

```
client-valence-ms-client/
├── src/
│   ├── core/                   # Core modules
│   ├── teams/sender/           # Phase 1: Teams sender
│   ├── notifier/               # Phase 1: Notification service
│   └── api/                    # Phase 1: Notifier API
├── tests/
│   ├── mocks/                  # Mock servers
│   ├── phase0/                 # Phase 0 tests
│   └── phase1/                 # Phase 1 tests
├── scripts/
│   ├── phase0/                 # Mock server scripts
│   └── phase1/                 # Notification scripts
├── postman/                    # Postman collection
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

### Running Mock Servers

```bash
# Activate virtual environment
source .venv/bin/activate

# Start mock agent (port 8080)
python scripts/phase0/start_mock_agent.py &

# Start mock webhook (port 3000)
python scripts/phase0/start_mock_webhook.py &
```

### Testing

```bash
# Run all tests
pytest tests/phase0/ -v

# Run all endpoints demo
python scripts/phase0/run_all_endpoints.py

# Run interactive MS Teams client
python scripts/phase0/msteams_client.py
```

## Configuration

Environment variables (`.env`):

```bash
# Environment
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Mock Servers
MOCK_AGENT_PORT=8080
MOCK_WEBHOOK_PORT=3000

# Teams (optional)
TEAMS_INCOMING_WEBHOOK=https://outlook.office.com/webhook/...
```

## Documentation

- **[API Reference](docs/api-reference.md)** - Endpoints, request/response formats
- **Swagger UI**: http://localhost:8080/docs (Agent) | http://localhost:3000/docs (Webhook)
- **Postman Collection**: Import `postman/teams-agent-integration.postman_collection.json`

## Development Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Testing & Mocks | Complete |
| 1 | Notifications (Agent → Teams) | Complete |
| 2 | Queries Stateless (Teams → Agent) | Pending |
| 3 | Queries with Memory | Pending |

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Mock servers
- **Pydantic** - Configuration and validation
- **Structlog** - Structured logging
- **HTTPX** - Async HTTP client
- **Pytest** - Testing framework

## License

Private - All rights reserved.
