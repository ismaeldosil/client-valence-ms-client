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

## Interactive Documentation

When servers are running:

- **Agent Swagger UI**: http://localhost:8080/docs
- **Webhook Swagger UI**: http://localhost:3000/docs
