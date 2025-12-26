# API Design Explanation

This document explains the design decisions and sources for the APIs implemented in this project.

## Overview

The project implements two mock servers that simulate the components needed for Teams-Agent integration:

1. **Mock Agent Server** - Simulates an AI Agent that responds to queries
2. **Mock Webhook Receiver** - Simulates our webhook endpoint that receives messages from Teams

---

## 1. Mock Agent Server API

### Source of Design

The Mock Agent API was designed based on common patterns from:

- **OpenAI Chat Completions API** - Response structure with text and metadata
- **LangChain Agent patterns** - Context and conversation history handling
- **RAG (Retrieval Augmented Generation) systems** - Sources and confidence scores

### Endpoints

#### GET /health

Standard health check endpoint following cloud-native application patterns.

```json
{
  "status": "ok",
  "service": "mock-agent"
}
```

**Design rationale:**
- Simple status check for load balancers and monitoring
- Service identification for multi-service environments

#### POST /query

Main endpoint for querying the agent.

**Request Format:**
```json
{
  "message": "User's question",
  "context": {
    "platform": "teams",
    "user_id": "user123",
    "conversation_id": "conv456"
  },
  "conversation_history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"}
  ]
}
```

**Response Format:**
```json
{
  "text": "Agent's response text",
  "sources": ["document1.pdf", "policy.md"],
  "confidence": 0.95,
  "processing_time_ms": 450
}
```

**Design rationale:**

| Field | Source/Inspiration | Purpose |
|-------|-------------------|---------|
| `message` | Standard chat APIs | The user's input query |
| `context` | LangChain, custom agents | Metadata about the request origin |
| `context.platform` | Multi-channel bots | Identify source (teams, slack, web) |
| `conversation_history` | OpenAI Chat API | Enable multi-turn conversations |
| `text` | All chat APIs | The agent's response |
| `sources` | RAG systems (LlamaIndex, LangChain) | Document attribution for responses |
| `confidence` | ML classification patterns | Indicate response reliability (0-1) |
| `processing_time_ms` | Observability best practices | Performance monitoring |

---

## 2. Mock Webhook Receiver API

### Source of Design

The Webhook Receiver API was designed based on:

- **Microsoft Teams Outgoing Webhooks** - Official Teams message format
- **Microsoft Bot Framework** - Activity schema for messages
- **Teams Adaptive Cards** - Response format for rich messages

### Reference Documentation

- [Teams Outgoing Webhooks](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-outgoing-webhook)
- [Bot Framework Activity Schema](https://learn.microsoft.com/en-us/azure/bot-service/rest-api/bot-framework-rest-connector-api-reference)

### Endpoints

#### GET /health

Standard health check endpoint.

```json
{
  "status": "ok",
  "service": "mock-webhook"
}
```

#### POST /webhook

Receives messages from Teams in the Outgoing Webhook format.

**Request Format (from Teams):**
```json
{
  "type": "message",
  "id": "1234567890",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "localTimestamp": "2024-01-15T10:30:00.000Z",
  "serviceUrl": "https://smba.trafficmanager.net/amer/",
  "channelId": "msteams",
  "from": {
    "id": "29:1abc...",
    "name": "John Doe",
    "aadObjectId": "guid-here"
  },
  "conversation": {
    "id": "19:abc...@thread.tacv2",
    "conversationType": "channel",
    "tenantId": "tenant-guid",
    "name": "General"
  },
  "recipient": {
    "id": "28:bot-id",
    "name": "Bot Name"
  },
  "text": "<at>BotName</at> Hello, how are you?",
  "entities": [
    {
      "type": "mention",
      "mentioned": {
        "id": "28:bot-id",
        "name": "BotName"
      },
      "text": "<at>BotName</at>"
    }
  ]
}
```

**Response Format (to Teams):**
```json
{
  "type": "message",
  "text": "Response text here"
}
```

**Design rationale:**

| Field | Source | Purpose |
|-------|--------|---------|
| `type` | Bot Framework | Message type identifier |
| `id` | Bot Framework | Unique message identifier |
| `from` | Bot Framework | Sender information |
| `from.id` | Teams | Teams user ID (29: prefix) |
| `from.name` | Teams | Display name |
| `conversation` | Bot Framework | Conversation context |
| `conversation.id` | Teams | Teams conversation/channel ID |
| `text` | Bot Framework | Message content with @mentions |
| `entities` | Bot Framework | Structured data (mentions, etc.) |

### @Mention Handling

When a user mentions the bot in Teams, the message includes HTML-like tags:

```
<at>BotName</at> What is the vacation policy?
```

The webhook receiver strips these tags to get the clean message:

```python
if "</at>" in text:
    text = text.split("</at>", 1)[1].strip()
```

### Commands

The following commands are implemented based on common bot patterns:

| Command | Purpose | Source |
|---------|---------|--------|
| `/help` | Show available commands | Standard bot convention |
| `/clear` | Clear conversation history | Chat applications |
| `/history` | Show conversation history | Chat applications |

---

## 3. Teams Incoming Webhook (for Notifications)

### Source of Design

Based on Microsoft's official documentation:

- [Create Incoming Webhooks](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook)
- [Send messages using Incoming Webhook](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/connectors-using)

### Request Format

**Simple Text Message:**
```json
{
  "text": "Hello from the agent!"
}
```

**Adaptive Card Message:**
```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
          {
            "type": "TextBlock",
            "text": "Notification Title",
            "weight": "Bolder",
            "size": "Medium"
          },
          {
            "type": "TextBlock",
            "text": "Notification content here",
            "wrap": true
          }
        ]
      }
    }
  ]
}
```

### Reference Documentation

- [Adaptive Cards Schema](https://adaptivecards.io/explorer/)
- [Adaptive Cards Designer](https://adaptivecards.io/designer/)

---

## 4. Postman Collection Structure

The Postman collection is organized into folders matching the API structure:

```
Teams Agent Integration/
├── Health Checks/
│   ├── Mock Agent Health
│   └── Mock Webhook Health
├── Mock Agent/
│   ├── Query - Simple
│   ├── Query - Vacaciones
│   ├── Query - Horario
│   └── Query - With History
├── Mock Webhook/
│   ├── Simple Message
│   ├── Command - Clear
│   ├── Command - History
│   └── Command - Help
└── Teams Real (Optional)/
    ├── Send Text Message
    └── Send Adaptive Card
```

### Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `mock_agent_url` | `http://localhost:8080` | Mock agent base URL |
| `mock_webhook_url` | `http://localhost:3000` | Mock webhook base URL |
| `teams_webhook_url` | *(empty)* | Real Teams Incoming Webhook URL |

---

## 5. Summary of Sources

| Component | Primary Source |
|-----------|---------------|
| Agent Query API | OpenAI API patterns + RAG systems |
| Webhook Receiver | Microsoft Teams Outgoing Webhooks |
| Message Format | Microsoft Bot Framework Activity Schema |
| @Mention Handling | Teams Outgoing Webhook documentation |
| Incoming Webhook | Microsoft Teams Incoming Webhooks |
| Adaptive Cards | Microsoft Adaptive Cards specification |
| Health Endpoints | Cloud-native application patterns |
| Commands | Common chatbot conventions |

---

## 6. Official Microsoft Documentation Links

1. **Outgoing Webhooks:**
   https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-outgoing-webhook

2. **Incoming Webhooks:**
   https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook

3. **Bot Framework REST API:**
   https://learn.microsoft.com/en-us/azure/bot-service/rest-api/bot-framework-rest-connector-api-reference

4. **Adaptive Cards:**
   https://adaptivecards.io/

5. **Teams Message Format:**
   https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/connectors-using
