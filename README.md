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
- Agent Client with retry logic and timeout handling
- Commands: `/help`, `/status`, `/clear`
- Full Spanish language support

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
│   ├── phase1/                 # Phase 1 tests
│   ├── phase2/                 # Phase 2 tests (handler, hmac, models, client)
│   └── core/                   # Core module tests
├── scripts/
│   ├── phase0/                 # Mock server scripts
│   ├── phase1/                 # Notification scripts
│   └── phase2/                 # Receiver scripts
├── .github/workflows/          # CI/CD (GitHub Actions)
├── postman/                    # Postman collection & environments
├── requirements/               # Dependencies (base, dev)
└── docs/                       # Documentation
```

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/REEA-Global-LLC/client-valence-ms-client.git
cd client-valence-ms-client

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements/base.txt

# For development (includes testing tools)
pip install -r requirements/dev.txt

# Copy environment file
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

## Development

### Quality Commands (Makefile)

```bash
# Linting and formatting
make lint

# Type checking
make type-check

# Security scan
make security

# Run tests with coverage
make test

# Full analysis (pre-push)
make pre-push

# Find untested code
make find-gaps

# Run all quality checks
make all
```

### Pre-commit Hooks

```bash
# Install hooks
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push

# Run manually
pre-commit run --all-files
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific phase
pytest tests/phase2/ -v

# Run Phase 0 endpoints demo
python scripts/phase0/run_all_endpoints.py

# Run interactive MS Teams client
python scripts/phase0/msteams_client.py

# Send notification (Phase 1)
python scripts/phase1/send_notification.py --channel alerts --message "Test" --card alert
```

### Test Coverage

Current coverage: **83%** (174 tests passing)

| Module | Coverage |
|--------|----------|
| `src/teams/receiver/` | 99% |
| `src/agent/` | 83-100% |
| `src/core/` | 100% |
| `src/notifier/` | 61-100% |

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
TEAMS_WORKFLOW_ALERTS=http://localhost:3000/webhook
TEAMS_WORKFLOW_REPORTS=http://localhost:3000/webhook
TEAMS_WORKFLOW_GENERAL=http://localhost:3000/webhook
NOTIFIER_API_KEY=dev-api-key
NOTIFIER_PORT=8001

# Phase 2: Webhook Receiver
TEAMS_HMAC_SECRET=your-base64-secret
RECEIVER_PORT=3001
AGENT_BASE_URL=http://localhost:8000
AGENT_TIMEOUT=4.5
AGENT_MAX_RETRIES=1
```

> **Note:** Legacy Incoming Webhooks (Office 365 Connectors) were deprecated by Microsoft in 2025. This project uses Power Automate Workflows for Teams integration.

## Servers

| Server | Port | Phase | Description |
|--------|------|-------|-------------|
| Mock Agent | 8080 | 0 | Simulates AI Agent |
| Mock Webhook | 3000 | 0 | Simulates Teams webhook receiver |
| Notifier API | 8001 | 1 | Sends notifications to Teams |
| Webhook Receiver | 3001 | 2 | Receives messages from Teams |

## Docker

### Local Development with Docker

```bash
# Build and run both services
docker-compose up -d

# Check health
curl http://localhost:3001/health  # Receiver
curl http://localhost:8001/health  # Notifier

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Build Individual Images

```bash
# Build Receiver
docker build --target receiver -t teams-receiver:local .

# Build Notifier
docker build --target notifier -t teams-notifier:local .
```

## CI/CD

### Continuous Integration

GitHub Actions workflow runs on push/PR to main:

1. **Lint & Format** - Ruff check and format
2. **Type Check** - MyPy strict mode
3. **Security Scan** - Bandit SAST
4. **Tests & Coverage** - Pytest with 70% minimum coverage

### Continuous Deployment (AWS)

On merge to `main`, the release workflow:

1. Runs all tests
2. Builds Docker images for both services
3. Pushes to AWS ECR
4. Deploys to ECS Fargate with rolling update

See [AWS Deployment Guide](docs/aws-deployment.md) for full setup instructions.

## Documentation

- **[USAGE.md](USAGE.md)** - Setup and usage guide
- **[ROUTING.md](ROUTING.md)** - Phase navigation guide
- **[API Reference](docs/api-reference.md)** - Endpoints, request/response formats
- **[AWS Deployment](docs/aws-deployment.md)** - AWS ECS deployment guide
- **Swagger UI**:
  - Agent: http://localhost:8080/docs
  - Webhook: http://localhost:3000/docs
  - Notifier: http://localhost:8001/docs
  - Receiver: http://localhost:3001/docs
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
- **FastAPI** - Web framework
- **Pydantic** - Configuration and validation
- **Structlog** - Structured logging
- **HTTPX** - Async HTTP client
- **Pytest** - Testing framework
- **Ruff** - Linting and formatting
- **MyPy** - Static type checking
- **Bandit** - Security analysis
- **Pre-commit** - Git hooks

## License

Private - All rights reserved.
