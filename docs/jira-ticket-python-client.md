# MS Teams Notification Client - Phase 1

## Summary

Python client for sending notifications from an AI Agent to Microsoft Teams channels via Incoming Webhooks.

---

## Description

### Objective

Develop a Python client that enables an AI Agent to send notifications to Microsoft Teams channels. This is a **one-way communication** (Agent → Teams) for alerts, reports, and informational messages.

---

### Implemented Components

**Notification System** ✅
- Webhook Sender with retry logic (exponential backoff)
- Adaptive Cards Builder (alert, info, report templates)
- Notification Service with channel registry
- Notifier REST API with X-API-Key authentication

**Testing Infrastructure** ✅
- Mock Agent Server (port 8080)
- Mock Webhook Receiver (port 3000)
- Postman collection with all endpoints
- 65 unit tests

---

### Tech Stack

| Technology | Usage |
|------------|-------|
| Python 3.11+ | Runtime |
| FastAPI | REST API |
| Pydantic | Validation and configuration |
| HTTPX | Async HTTP client |
| Structlog | Structured logging |
| Pytest | Testing framework |

---

### API Endpoints

**Notifier API (`:8001`)**

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Health check |
| GET | `/api/v1/channels` | X-API-Key | List registered channels |
| POST | `/api/v1/notify` | X-API-Key | Send notification to Teams |

---

### Notification Types

| Type | Card | Use Case |
|------|------|----------|
| Alert | `alert` | Critical errors, warnings, system alerts |
| Info | `info` | Informational messages, deployments, updates |
| Report | `report` | Daily reports, summaries, metrics |

### Priority Levels

`low` | `medium` | `high` | `critical`

---

### Required Configuration

```bash
# Teams Incoming Webhook URLs (one per channel)
TEAMS_WEBHOOK_ALERTS=https://outlook.office.com/webhook/...
TEAMS_WEBHOOK_REPORTS=https://outlook.office.com/webhook/...
TEAMS_WEBHOOK_GENERAL=https://outlook.office.com/webhook/...

# API Security
NOTIFIER_API_KEY=<secure-api-key>
NOTIFIER_PORT=8001
```

---

### Usage Examples

**CLI:**
```bash
python scripts/phase1/send_notification.py \
  --channel alerts \
  --message "CPU usage exceeded 90%" \
  --title "High CPU Alert" \
  --card alert \
  --priority critical
```

**API:**
```bash
curl -X POST http://localhost:8001/api/v1/notify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <api-key>" \
  -d '{
    "channel": "alerts",
    "message": "Database connection failed",
    "title": "Critical Error",
    "card_type": "alert",
    "priority": "critical"
  }'
```

**Response:**
```json
{
  "success": true,
  "notification_id": "uuid",
  "channel": "alerts",
  "status": "sent"
}
```

---

### Features

- **Retry Logic:** Automatic retries with exponential backoff on failure
- **Multiple Channels:** Support for alerts, reports, and general channels
- **Adaptive Cards:** Rich formatting with colors, icons, and actions
- **Authentication:** X-API-Key header required for all endpoints
- **Async:** Non-blocking HTTP requests with HTTPX

---

### Repository

`https://github.com/REEA-Global-LLC/client-valence-ms-client`

### Branches

- `main` - Stable code
- `develop` - Active development

---

### Tests

```bash
pytest tests/ -v  # 65 tests passing
```

---

## Acceptance Criteria

- [x] Send text notifications to Teams channels
- [x] Send Adaptive Cards (alert, info, report)
- [x] Retry logic with exponential backoff
- [x] Channel registry with multiple webhooks
- [x] REST API with authentication
- [x] Configuration via environment variables
- [x] Unit tests with >80% coverage
- [x] Documentation and Postman collection

---

## Labels

`python` `teams` `notifications` `fastapi` `webhooks`

## Story Points

8
