# Epic: MS Teams Client for Valerie AI Agent

**Epic ID:** TC-000
**Status:** In Progress
**Started:** December 2025

---

## Vision

Enable seamless conversational access to the Valerie AI Agent through Microsoft Teams, supporting both enterprise notification workflows and interactive user queries within the Teams collaboration environment.

---

## Problem Statement

Organizations using Microsoft Teams as their primary collaboration platform need a native way to interact with Valerie AI. Unlike Slack's rich bot ecosystem, Teams presents unique integration challenges:

- Multiple integration patterns with different trade-offs (Webhooks, Connectors, Bot Framework)
- Enterprise security requirements (Azure AD, tenant isolation)
- Microsoft's evolving platform APIs and deprecation cycles
- 5-second timeout constraints on synchronous responses

---

## Solution Overview

A unified MS Teams client that abstracts the complexity of Microsoft's integration landscape, providing:

1. **Outbound notifications** to Teams channels via Power Automate Workflows
2. **Inbound queries** from users via Outgoing Webhooks and Bot Framework
3. **Conversational context** through session management
4. **Operational visibility** through a built-in dashboard

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MS Teams Client                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Notifier   │  │   Receiver   │  │    Bot Framework     │   │
│  │   (Outbound) │  │   (Inbound)  │  │    (Bidirectional)   │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         │                 │                      │               │
│         ▼                 ▼                      ▼               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Unified Message Processor                   │    │
│  │         (commands, sessions, agent routing)              │    │
│  └─────────────────────────┬───────────────────────────────┘    │
│                            │                                     │
├────────────────────────────┼─────────────────────────────────────┤
│                            ▼                                     │
│                    Valerie AI Agent                              │
│                    (external service)                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Completed Work

### Phase 1: Notifications (Outbound)

**Objective:** Enable Valerie to push alerts and reports to Teams channels.

**Approach:** Power Automate Workflows as the delivery mechanism, replacing deprecated Office 365 Connectors.

**Capabilities delivered:**
- Alert notifications to dedicated channels
- Scheduled report delivery
- Adaptive Card formatting for rich content
- API endpoint for programmatic triggering

---

### Phase 2: Queries via Webhooks (Inbound)

**Objective:** Allow users to ask questions to Valerie by @mentioning a bot in Teams.

**Approach:** Outgoing Webhooks—a lightweight integration requiring no Azure Bot registration.

**Capabilities delivered:**
- HMAC signature verification for security
- Message parsing and @mention stripping
- Timeout-aware processing (sub-5-second responses)
- Error handling with user-friendly messages

**Known limitations:**
- Requires @mention for every message
- No thread continuation without re-mentioning
- Cannot initiate conversations

---

### Phase 3: Session Management

**Objective:** Maintain conversational context across multiple interactions.

**Approach:** Pluggable session store supporting both in-memory (development) and Redis (production) backends.

**Capabilities delivered:**
- Session persistence keyed by user and conversation
- Thread-aware sessions (separate context per thread)
- Configurable TTL for automatic cleanup
- Session listing and management via dashboard

---

### Phase 4: Bot Framework Integration

**Objective:** Overcome Outgoing Webhooks limitations for true conversational experience.

**Approach:** Dual-mode architecture supporting both Webhooks and Bot Framework simultaneously.

**Capabilities delivered:**
- Automatic thread participation (no @mention required after initial contact)
- Proactive messaging foundation
- Azure AD authentication (Single and Multi-Tenant)
- Unified processor shared between integration modes

---

### Operational Tooling

**Dashboard:** Web-based interface for monitoring and testing
- Real-time health status of client and agent
- Session inspection and management
- Endpoint testing tools
- Configuration visibility

**Documentation:** Comprehensive guides for setup and troubleshooting
- Azure Bot configuration tutorial
- Deployment guides (Railway, AWS)
- API reference

---

## Integration Modes

| Mode | Mechanism | @Mention Required | Proactive Messages | Complexity |
|------|-----------|-------------------|-------------------|------------|
| `webhook` | Outgoing Webhooks | Yes, always | No | Low |
| `bot` | Bot Framework | Only first message | Yes | Medium |
| `dual` | Both active | Depends on entry point | Partial | Medium |

---

## Technical Decisions

### Why Power Automate over Connectors?
Office 365 Connectors are deprecated (retirement 2025). Power Automate Workflows provide a supported, flexible alternative with better enterprise integration.

### Why support both Webhooks and Bot Framework?
Different deployment scenarios have different requirements. Webhooks require no Azure resources—ideal for quick pilots. Bot Framework enables richer experiences for production deployments.

### Why thread-aware sessions?
Users expect conversational continuity within a thread. A question asked in a thread should reference prior context from that thread, not from unrelated conversations.

---

## Configuration

```env
# Integration mode
TEAMS_INTEGRATION_MODE=dual|webhook|bot

# Agent connection
AGENT_BASE_URL=https://...

# Webhook security
TEAMS_HMAC_SECRET=...

# Bot Framework (when mode=bot or dual)
MICROSOFT_APP_ID=...
MICROSOFT_APP_PASSWORD=...

# Session management
SESSION_STORE=memory|redis
SESSION_TTL_HOURS=24
```

---

## Open Items

- [ ] Production testing in enterprise Teams environment
- [ ] Adaptive Cards with interactive actions
- [ ] Proactive messaging for long-running queries
- [ ] File attachment handling

---

## References

- [Power Automate Workflows](https://learn.microsoft.com/en-us/power-automate/)
- [Teams Outgoing Webhooks](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-outgoing-webhook)
- [Bot Framework SDK](https://github.com/microsoft/botbuilder-python)
- [Azure Bot Service](https://docs.microsoft.com/en-us/azure/bot-service/)
