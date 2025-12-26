# Best Practices and Technical Decisions

This document captures all technical decisions, best practices, and conventions defined during development.

---

## 1. Microsoft Teams Integration

### Power Automate Workflows (Required)

> **IMPORTANT:** Legacy Incoming Webhooks (Office 365 Connectors) were deprecated by Microsoft in 2025. All integrations MUST use Power Automate Workflows.

#### Workflow URL Format
```
https://prod-XX.westus.logic.azure.com:443/workflows/XXXXXXXX/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=XXXXXXXX
```

#### Adaptive Card Payload Format

All notifications must use this structure:

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "contentUrl": null,
      "content": {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
          {
            "type": "TextBlock",
            "text": "Title",
            "weight": "Bolder",
            "size": "Medium"
          },
          {
            "type": "TextBlock",
            "text": "Message content",
            "wrap": true
          }
        ]
      }
    }
  ]
}
```

#### Workflow Technical Limits

| Specification | Limit |
|---------------|-------|
| Message Format | Adaptive Cards only (JSON) |
| Card Version | Adaptive Cards v1.4 |
| Rate Limit | Depends on Power Automate plan |
| Security | Tenant-level, user-level, or custom headers |

#### Workflow Ownership (Critical)

Workflows are linked to specific users (owners). If the owner leaves:
- The workflow may stop working
- **Always add co-owners** to ensure continuity

To add co-owners:
1. Open workflow in Power Automate
2. Go to "..." → "Share"
3. Add additional owners

### Outgoing Webhooks (Teams → Agent)

| Specification | Limit |
|---------------|-------|
| Response Timeout | **5 seconds** |
| Channel Type | Public channels only |
| Trigger | Requires @mention |
| Verification | HMAC-SHA256 required |
| Supported Actions | Only `openURL` |

---

## 2. Port Configuration

| Service | Port | Notes |
|---------|------|-------|
| Mock Agent Server | 8080 | - |
| Mock Webhook Receiver | 3000 | Simulates Teams webhook |
| Notifier API | 8001 | **Not 8000** (conflicts with LangGraph) |

---

## 3. Environment Variables

### Phase 0 (Base)
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
MOCK_AGENT_PORT=8080
MOCK_WEBHOOK_PORT=3000
```

### Phase 1 (Notifications)
```bash
# Power Automate Workflow URLs (one per channel)
TEAMS_WORKFLOW_ALERTS=https://prod-XX.westus.logic.azure.com:443/workflows/...
TEAMS_WORKFLOW_REPORTS=https://prod-XX.westus.logic.azure.com:443/workflows/...
TEAMS_WORKFLOW_GENERAL=https://prod-XX.westus.logic.azure.com:443/workflows/...
NOTIFIER_API_KEY=your-secure-key
NOTIFIER_PORT=8001

# For local testing (mock)
TEAMS_WORKFLOW_ALERTS=http://localhost:3000/webhook
TEAMS_WORKFLOW_REPORTS=http://localhost:3000/webhook
TEAMS_WORKFLOW_GENERAL=http://localhost:3000/webhook
```

### Phase 2 (Queries)
```bash
TEAMS_HMAC_SECRET=your-hmac-secret
AGENT_BASE_URL=https://your-agent.com
AGENT_API_KEY=your-key
AGENT_TIMEOUT=4.0
```

### Phase 3 (Sessions)
```bash
SESSION_STORE=redis
REDIS_URL=redis://localhost:6379/0
SESSION_TTL_MINUTES=30
```

---

## 4. Postman Conventions

| Item | Value |
|------|-------|
| Collection Name | `MS Teams Agent Integration APIs` |
| Environment Name | `Microsoft Client - Environment` |

### Environment Variables

```json
{
  "mock_agent_url": "http://localhost:8080",
  "mock_webhook_url": "http://localhost:3000",
  "notifier_api_url": "http://localhost:8001",
  "notifier_api_key": "dev-api-key",
  "teams_workflow_url": "",
  "receiver_url": "http://localhost:3000",
  "teams_hmac_secret": "",
  "agent_base_url": "http://localhost:8080",
  "agent_api_key": "",
  "agent_timeout": "4.0",
  "session_ttl_minutes": "30"
}
```

**Decision:** Include endpoints for ALL phases in the collection from the start, organized by folders.

---

## 5. Documentation for Clients

### Rules

1. **Do NOT mark phase differences** in external documents
2. **Include note about additional costs** for advanced features
3. **Do NOT include "What We Need From You"** sections with fill-in forms
4. **Always mention co-owners** requirement for workflows

### Document Generation

1. Create in **HTML** first with:
   - Professional styles (Teams color: `#5B5FC7`)
   - Tables for specifications
   - Alert boxes (warning, info, critical)
   - Checklists

2. Convert to **PDF** with weasyprint:
   ```bash
   weasyprint guide.html guide.pdf
   ```

---

## 6. Git/GitHub Rules

### Commit Messages

- Use conventional commits: `feat:`, `fix:`, `test:`, `docs:`
- NO references to Claude, AI assistant, or generation tools
- NO "Co-Authored-By" headers

### If References Leak

Clean with git filter-branch:
```bash
git filter-branch --force --msg-filter '
grep -v "Claude" | grep -v "Generated with" | grep -v "Co-Authored-By"
' --prune-empty -- --all

git push origin --force --all
```

---

## 7. Project Structure

### Required Directories

```
docs/
├── api-reference.md
├── tickets.md
├── email-teams-setup-request.md
├── teams_webhook_setup_guide.md
├── teams_webhook_setup_guide.html
└── teams_webhook_setup_guide.pdf

postman/
├── teams-agent-integration.postman_collection.json
└── environments/
    └── local.postman_environment.json

prompts/
├── best-practices.md (this file)
├── prompt-fase-0-testing.md
├── prompt-fase-1-notificaciones.md
├── prompt-fase-2-consultas-stateless.md
└── prompt-fase-3-consultas-stateful.md
```

### Do NOT Create

- JIRA ticket files in repository
- Unnecessary README files
- Redundant documentation

---

## 8. Phase Definitions

### Phase 0: Testing & Mocks
- Mock servers for development
- Postman collection
- Unit tests

### Phase 1: Notifications (Agent → Teams)
- **Unidirectional** communication only
- Power Automate Workflows (NOT legacy webhooks)
- Three default channels: Alerts, Reports, General
- X-API-Key authentication

### Phase 2: Queries Stateless (Teams → Agent)
- Bidirectional communication
- Outgoing Webhooks from Teams
- HMAC-SHA256 verification
- 5-second response timeout

### Phase 3: Queries with Memory
- Session management
- Redis for state storage
- Conversation history

---

## 9. Code Standards

1. **Type hints**: All code must have complete type hints
2. **Tests**: Maintain >80% coverage
3. **Logging**: Use structured logging (structlog)
4. **No AI mentions**: Never mention Claude/AI in code or docs

---

## 10. Client Communication

### Email Templates

Must include:
1. What workflows we need (by channel)
2. Why Power Automate (deprecation notice)
3. Step-by-step summary
4. What to send back
5. Note about additional costs
6. Attachments: PDF guide, Postman collection

### Cost Warning (Required)

> Some advanced configurations (such as bidirectional communication where users can chat with the agent) may require additional Microsoft services that incur monthly costs. We'll discuss these options and their associated costs before implementing any features that require them.

---

## References

- [Microsoft: Retirement of Office 365 Connectors](https://devblogs.microsoft.com/microsoft365dev/retirement-of-office-365-connectors-within-microsoft-teams/)
- [Microsoft: Create flows that post adaptive cards](https://learn.microsoft.com/en-us/power-automate/create-adaptive-cards)
- [Adaptive Cards Documentation](https://adaptivecards.io/)
- [Power Automate Workflow Migration Guide](https://heusser.pro/p/migrate-teams-office-365-connectors-to-workflows-8p40yq7jfebm/)
