# ROUTING.md - Phase Navigation Guide

## Phase Map

```
                    ┌─────────────────┐
                    │    FASE 0       │
                    │  Testing/Mocks  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              │              ▼
    ┌─────────────────┐      │    ┌─────────────────┐
    │    FASE 1       │      │    │    FASE 2       │
    │ Notificaciones  │      │    │  Consultas      │
    │ (Agent→Teams)   │      │    │  (Sin memoria)  │
    └────────┬────────┘      │    └────────┬────────┘
             │               │             │
             │               │             ▼
             │               │    ┌─────────────────┐
             │               │    │    FASE 3       │
             │               │    │  Consultas      │
             │               │    │  (Con memoria)  │
             │               │    └─────────────────┘
             │               │             │
             └───────────────┴─────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   COMPLETADO    │
                    └─────────────────┘
```

## Phase Descriptions

| Phase | Name | Description | Prerequisite |
|-------|------|-------------|--------------|
| 0 | Testing & Mocks | Mock servers, tests, Postman | None |
| 1 | Notifications | Agent sends to Teams | Phase 0 |
| 2 | Queries (Stateless) | Users query Agent | Phase 0 |
| 3 | Queries (Stateful) | Queries with memory | Phase 0 + 2 |

## How to Use

### Sequential Path (Full Features)
```
Phase 0 → Phase 1 → Phase 2 → Phase 3
```

### Notifications Only
```
Phase 0 → Phase 1 → Done
```

### Queries Only (No Memory)
```
Phase 0 → Phase 2 → Done
```

### Queries with Memory
```
Phase 0 → Phase 2 → Phase 3 → Done
```

## Phase Prompts

| Phase | Prompt File |
|-------|-------------|
| 0 | `prompts/prompt-fase-0-testing.md` |
| 1 | `prompts/prompt-fase-1-notificaciones.md` |
| 2 | `prompts/prompt-fase-2-consultas-stateless.md` |
| 3 | `prompts/prompt-fase-3-consultas-stateful.md` |

## Transition Checklist

### Phase 0 → Phase 1/2
- [ ] All Phase 0 tests pass: `pytest tests/phase0/`
- [ ] Mock servers run without errors
- [ ] Postman collection works
- [ ] .env configured

### Phase 1 → Phase 2
- [ ] Notifications work
- [ ] At least one Power Automate Workflow configured
- [ ] Tests pass: `pytest tests/phase1/`

### Phase 2 → Phase 3
- [ ] Queries work without memory
- [ ] Agent client configured
- [ ] Tests pass: `pytest tests/phase2/`
- [ ] Redis available (for Phase 3)

## Environment Variables by Phase

### Phase 0 (Required)
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### Phase 1 (Add)
```bash
# Power Automate Workflow URLs
TEAMS_WORKFLOW_ALERTS=https://prod-XX.westus.logic.azure.com:443/workflows/...
TEAMS_WORKFLOW_REPORTS=https://prod-XX.westus.logic.azure.com:443/workflows/...
TEAMS_WORKFLOW_GENERAL=https://prod-XX.westus.logic.azure.com:443/workflows/...
NOTIFIER_API_KEY=your-key
NOTIFIER_PORT=8001
```

> **Note:** Legacy Incoming Webhooks (Office 365 Connectors) were deprecated by Microsoft in 2025.

### Phase 2 (Add)
```bash
TEAMS_HMAC_SECRET=your-hmac-secret
AGENT_BASE_URL=https://your-agent.com
AGENT_API_KEY=your-key
```

### Phase 3 (Add)
```bash
SESSION_STORE=redis
REDIS_URL=redis://localhost:6379/0
```

## Quick Start

```bash
# 1. Setup
./scripts/setup.sh

# 2. Start mocks
python scripts/phase0/start_mock_agent.py &
python scripts/phase0/start_mock_webhook.py &

# 3. Test
python scripts/phase0/msteams_client.py

# 4. Run tests
pytest tests/phase0/

# 5. When ready, proceed to next phase
# Read: prompts/prompt-fase-X-....md
```
