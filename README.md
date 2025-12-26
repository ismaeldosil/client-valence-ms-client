# Teams Agent Integration Client

**Phase 0**: Mock servers and testing infrastructure for Teams-Agent integration.

## Features (Phase 0)

- **Mock Agent Server**: Simulates AI Agent responses on port 8080
- **Mock Webhook Receiver**: Simulates Teams webhook on port 3000
- **Knowledge Base**: Pre-configured responses for testing
- **Test Client**: Interactive testing script
- **Postman Collection**: Ready-to-use API collection

## Project Structure

```
client-valence-ms-client/
├── src/
│   └── core/
│       ├── config.py          # Configuration (pydantic-settings)
│       ├── exceptions.py      # Custom exceptions
│       └── logging.py         # Structured logging (structlog)
├── tests/
│   ├── mocks/
│   │   ├── mock_agent_server.py     # Mock AI Agent (:8080)
│   │   ├── mock_webhook_receiver.py # Mock webhook (:3000)
│   │   └── mock_responses.py        # Knowledge base
│   └── phase0/
│       └── test_*.py                # Unit tests
├── scripts/
│   ├── setup.sh
│   └── phase0/
│       ├── start_mock_agent.py
│       ├── start_mock_webhook.py
│       ├── test_client.py
│       ├── run_all_endpoints.py
│       └── send_to_teams.py
├── postman/
│   ├── teams-agent-integration.postman_collection.json
│   └── environments/
│       └── local.postman_environment.json
├── requirements/
│   └── base.txt
└── pyproject.toml
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

# Run interactive test client
python scripts/phase0/test_client.py
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
| 1 | Notifications (Agent → Teams) | Pending |
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
