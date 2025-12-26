# MS Teams Agent Integration Client - Python Implementation

## Summary

Python client for integration between Microsoft Teams and AI Agent, enabling bidirectional communication: notifications from the agent to Teams and user queries from Teams to the agent.

---

## Description

### Objective

Develop a Python client that acts as middleware between Microsoft Teams and an AI Agent, enabling:
- **Notifications (Agent → Teams):** The agent can send alerts, reports, and information to Teams channels
- **Queries (Teams → Agent):** Users can query the agent from Teams via @mentions

---

### Implemented Components

**Phase 0 - Testing & Mocks** ✅
- Mock Agent Server (FastAPI, port 8080)
- Mock Webhook Receiver (FastAPI, port 3000)
- Knowledge Base with test responses
- Interactive client for testing
- Postman collection with 40 endpoints
- 28 unit tests

**Phase 1 - Notifications (Agent → Teams)** ✅
- Webhook Sender with retry logic (exponential backoff)
- Adaptive Cards Builder (alert, info, report)
- Notification Service with channel registry
- Notifier API (FastAPI, port 8001) with X-API-Key authentication
- 37 unit tests

---

### Tech Stack

| Technology | Usage |
|------------|-------|
| Python 3.11+ | Runtime |
| FastAPI | REST APIs |
| Pydantic | Validation and configuration |
| HTTPX | Async HTTP client |
| Structlog | Structured logging |
| Pytest | Testing framework |

---

### Available Endpoints

**Notifier API (`:8001`)**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/channels` | List registered channels |
| POST | `/api/v1/notify` | Send notification to Teams |

---

### Required Configuration

```bash
# Phase 1: Notifications
TEAMS_WEBHOOK_ALERTS=https://outlook.office.com/webhook/...
TEAMS_WEBHOOK_REPORTS=https://outlook.office.com/webhook/...
TEAMS_WEBHOOK_GENERAL=https://outlook.office.com/webhook/...
NOTIFIER_API_KEY=<api-key>
NOTIFIER_PORT=8001
```

---

### Usage Examples

```bash
# Start server
python scripts/phase1/start_notifier_api.py

# Send notification via CLI
python scripts/phase1/send_notification.py \
  --channel alerts \
  --message "CPU usage exceeded 90%" \
  --title "High CPU Alert" \
  --card alert \
  --priority critical

# Send via API
curl -X POST http://localhost:8001/api/v1/notify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key" \
  -d '{"channel":"alerts","message":"Test","priority":"high"}'
```

---

### Repository

`https://github.com/REEA-Global-LLC/client-valence-ms-client`

### Branches

- `main` - Stable code
- `develop` - Active development
- `feature/phase-1` - Phase 1 feature branch

---

### Tests

```bash
pytest tests/ -v  # 65 tests passing
```

---

### Pending (Future Phases)

- **Phase 2:** Stateless Queries (Teams → Agent) with HMAC verification and 5s timeout
- **Phase 3:** Queries with conversation memory (sessions)

---

## Acceptance Criteria

- [x] Mock servers working for local development
- [x] Notifier API with authentication
- [x] Adaptive Cards support (alert, info, report)
- [x] Retry logic with exponential backoff
- [x] Complete documentation (README, API Reference)
- [x] Updated Postman collection
- [x] Unit tests (>80% coverage)
- [x] Configuration via environment variables

---

## Labels

`python` `teams` `integration` `fastapi` `notifications`

## Story Points

13
