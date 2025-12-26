# API Reference

## Mock Agent Server (`:8080`)

Base URL: `http://localhost:8080`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/query` | Query the agent |

---

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "mock-agent"
}
```

---

### POST /query

Query the agent with a message.

**Request:**
```json
{
  "message": "What is the vacation policy?",
  "context": {
    "platform": "teams",
    "user_id": "user123"
  },
  "conversation_history": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User's question |
| `context` | object | No | Additional context |
| `context.platform` | string | No | Source platform |
| `context.user_id` | string | No | User identifier |
| `conversation_history` | array | No | Previous messages |

**Response:**
```json
{
  "text": "The vacation policy allows 15 business days per year...",
  "sources": ["hr-policies.pdf"],
  "confidence": 0.95,
  "processing_time_ms": 450
}
```

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Agent's response |
| `sources` | array | Source documents used |
| `confidence` | float | Confidence score (0-1) |
| `processing_time_ms` | int | Processing time in milliseconds |

---

## Mock Webhook Receiver (`:3000`)

Base URL: `http://localhost:3000`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/webhook` | Receive Teams messages |

---

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "mock-webhook"
}
```

---

### POST /webhook

Receive messages from Teams (Outgoing Webhook format).

**Request:**
```json
{
  "type": "message",
  "id": "msg-001",
  "text": "<at>Bot</at> Hello!",
  "from": {
    "id": "user-001",
    "name": "John Doe"
  },
  "conversation": {
    "id": "conv-001"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Message type |
| `id` | string | No | Message ID |
| `text` | string | Yes | Message content (may include @mentions) |
| `from` | object | No | Sender information |
| `from.id` | string | No | Sender ID |
| `from.name` | string | No | Sender name |
| `conversation` | object | No | Conversation info |
| `conversation.id` | string | No | Conversation ID |

**Response:**
```json
{
  "type": "message",
  "text": "Response text here"
}
```

---

## Supported Commands

The webhook receiver supports the following commands:

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/history` | Show conversation history |

---

## Notifier API (`:8001`) - Phase 1

Base URL: `http://localhost:8001`

### Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Health check |
| GET | `/api/v1/channels` | X-API-Key | List registered channels |
| POST | `/api/v1/notify` | X-API-Key | Send notification |

---

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "notifier"
}
```

---

### GET /api/v1/channels

List all registered notification channels.

**Headers:**
| Header | Required | Description |
|--------|----------|-------------|
| `X-API-Key` | Yes | API key (default: `dev-api-key`) |

**Response:**
```json
{
  "channels": [
    {"name": "alerts", "enabled": true, "description": "Alert notifications"},
    {"name": "reports", "enabled": true, "description": "Report notifications"},
    {"name": "general", "enabled": true, "description": "General notifications"}
  ]
}
```

---

### POST /api/v1/notify

Send a notification to a Teams channel.

**Headers:**
| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes | `application/json` |
| `X-API-Key` | Yes | API key (default: `dev-api-key`) |

**Request:**
```json
{
  "channel": "alerts",
  "message": "CPU usage exceeded 90%",
  "title": "High CPU Alert",
  "card_type": "alert",
  "priority": "critical",
  "metadata": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channel` | string | Yes | Channel name (alerts, reports, general) |
| `message` | string | Yes | Notification message |
| `title` | string | No | Notification title |
| `card_type` | string | No | Card type: `alert`, `info`, `report` |
| `priority` | string | No | Priority: `low`, `medium`, `high`, `critical` |
| `metadata` | object | No | Additional metadata |

**Response (Success):**
```json
{
  "success": true,
  "notification_id": "uuid-here",
  "channel": "alerts",
  "status": "sent",
  "error": null
}
```

**Response (Error - Channel not found):**
```json
{
  "detail": "Channel 'invalid' not found or disabled"
}
```

**Response (Error - Unauthorized):**
```json
{
  "detail": [{"type": "missing", "loc": ["header", "X-API-Key"], "msg": "Field required"}]
}
```

---

## Card Types

### Alert Card
Used for critical alerts and warnings.
```json
{"card_type": "alert", "priority": "critical"}
```

### Info Card
Used for informational messages.
```json
{"card_type": "info", "priority": "low"}
```

### Report Card
Used for reports and summaries.
```json
{"card_type": "report", "priority": "medium"}
```

---

## Interactive Documentation

When servers are running:

- **Agent Swagger UI**: http://localhost:8080/docs
- **Webhook Swagger UI**: http://localhost:3000/docs
- **Notifier Swagger UI**: http://localhost:8001/docs
