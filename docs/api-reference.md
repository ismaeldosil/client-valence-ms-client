# API Reference

## Mock Agent Server (`:8080`)

Base URL: `http://localhost:8080`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness check |
| GET | `/live` | Liveness check |
| POST | `/api/v1/chat` | Chat with agent (v2) |
| GET | `/api/v1/sessions/{id}` | Get session details |
| DELETE | `/api/v1/sessions/{id}` | Delete session |
| POST | `/query` | Legacy query endpoint (deprecated) |

---

### GET /health

Health check endpoint with service status.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.2.0-mock",
  "timestamp": "2025-12-27T10:30:00Z",
  "services": [
    {"name": "knowledge_base", "status": "healthy", "latency_ms": 5.2},
    {"name": "agent_pipeline", "status": "healthy", "latency_ms": 12.1}
  ]
}
```

---

### POST /api/v1/chat

Send a message to the chatbot (v2 API).

**Request:**
```json
{
  "message": "Find suppliers with Nadcap certification",
  "session_id": "existing-session-id",
  "user_id": "user-123"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User's message (1-5000 chars) |
| `session_id` | string | No | Existing session ID for conversation continuity |
| `user_id` | string | No | User identifier for tracking |

**Response:**
```json
{
  "session_id": "sess-abc123",
  "message": "Here are the suppliers with Nadcap certification...",
  "agents_executed": [
    {
      "agent_name": "intent_classifier",
      "display_name": "Intent Classifier",
      "status": "completed",
      "duration_ms": 50,
      "output": {"intent": "supplier_search", "confidence": 0.95}
    },
    {
      "agent_name": "knowledge_retrieval",
      "display_name": "Knowledge Retrieval",
      "status": "completed",
      "duration_ms": 200,
      "output": {}
    }
  ],
  "intent": "supplier_search",
  "confidence": 0.95,
  "requires_approval": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Session identifier for conversation continuity |
| `message` | string | Agent's response message |
| `agents_executed` | array | List of agents that processed the request |
| `intent` | string | Detected user intent |
| `confidence` | float | Confidence score (0-1) |
| `requires_approval` | boolean | Whether action requires user approval |

---

### GET /api/v1/sessions/{session_id}

Get session details and message history.

**Response:**
```json
{
  "session_id": "sess-abc123",
  "status": "active",
  "created_at": "2025-12-27T10:00:00Z",
  "last_activity": "2025-12-27T10:30:00Z",
  "message_count": 5,
  "messages": [
    {"role": "user", "content": "Hello", "timestamp": "2025-12-27T10:00:00Z"},
    {"role": "assistant", "content": "Hi there!", "timestamp": "2025-12-27T10:00:01Z"}
  ]
}
```

---

### DELETE /api/v1/sessions/{session_id}

Delete a session.

**Response:**
```json
{
  "deleted": true,
  "session_id": "sess-abc123"
}
```

---

### POST /query (Deprecated)

Legacy query endpoint. Use `/api/v1/chat` instead.

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

**Response:**
```json
{
  "text": "The vacation policy allows 15 business days per year...",
  "sources": ["hr-policies.pdf"],
  "confidence": 0.95,
  "processing_time_ms": 450
}
```

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
  "status": "healthy",
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

**Response:**
```json
{
  "type": "message",
  "text": "Response text here"
}
```

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
  "status": "healthy",
  "service": "notifier",
  "version": "1.0.0"
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

## Webhook Receiver (`:3001`) - Phase 2

Base URL: `http://localhost:3001`

### Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Health check with agent status |
| POST | `/webhook` | HMAC | Receive Teams messages |
| POST | `/api/v1/test-message` | No | Test endpoint (dev only) |

---

### GET /health

Health check with agent connection status.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "phase": "2-stateless",
  "hmac_enabled": true,
  "agent": {
    "url": "http://localhost:8000",
    "status": "healthy",
    "version": "2.2.0"
  }
}
```

---

### POST /webhook

Receive messages from Teams Outgoing Webhook.

**Headers:**
| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | `HMAC <base64-signature>` |
| `Content-Type` | Yes | `application/json` |

**Request (Teams format):**
```json
{
  "type": "message",
  "id": "msg-001",
  "timestamp": "2025-12-27T18:41:34.000Z",
  "serviceUrl": "https://smba.trafficmanager.net/amer/",
  "channelId": "msteams",
  "from": {
    "id": "29:user-aad-id",
    "name": "John Doe",
    "aadObjectId": "user-aad-object-id"
  },
  "conversation": {
    "id": "19:channel-id@thread.tacv2",
    "conversationType": "channel",
    "tenantId": "tenant-id"
  },
  "recipient": {
    "id": "28:bot-id",
    "name": "Valerie"
  },
  "text": "<at>Valerie</at> What suppliers have Nadcap certification?",
  "entities": [
    {
      "type": "mention",
      "mentioned": {
        "id": "28:bot-id",
        "name": "Valerie"
      },
      "text": "<at>Valerie</at>"
    }
  ]
}
```

**Response (Teams format):**
```json
{
  "type": "message",
  "text": "Based on our database, the following suppliers have Nadcap certification..."
}
```

**Error Response (401 - Invalid HMAC):**
```json
{
  "detail": "Invalid signature"
}
```

**Error Response (400 - Invalid message):**
```json
{
  "detail": "Invalid message format"
}
```

---

### POST /api/v1/test-message

Test endpoint for development (no HMAC required).

> **Note:** Only available when `ENVIRONMENT=development`

**Request:**
```json
{
  "id": "test-1",
  "text": "<at>Bot</at> Hello, how are you?",
  "from": {"id": "user-1", "name": "Test User"},
  "conversation": {"id": "conv-1"}
}
```

**Response:**
```json
{
  "type": "message",
  "text": "Agent response here..."
}
```

---

## Webhook Receiver Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/status` | Check agent connection status |
| `/clear` | Clear conversation history (Phase 3) |

---

## Error Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 400 | Bad Request | Invalid JSON or message format |
| 401 | Unauthorized | Invalid or missing HMAC signature / API key |
| 403 | Forbidden | Feature not available (e.g., test endpoint in production) |
| 404 | Not Found | Session or resource not found |
| 422 | Validation Error | Request validation failed |
| 503 | Service Unavailable | Agent or service not ready |
| 504 | Gateway Timeout | Agent response took > 5 seconds |

---

## Interactive Documentation

When servers are running:

- **Agent Swagger UI**: http://localhost:8080/docs
- **Webhook Swagger UI**: http://localhost:3000/docs
- **Notifier Swagger UI**: http://localhost:8001/docs
- **Receiver Swagger UI**: http://localhost:3001/docs
