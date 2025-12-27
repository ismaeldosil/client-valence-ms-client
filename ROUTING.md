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

| Phase | Name | Description | Prerequisite | Status |
|-------|------|-------------|--------------|--------|
| 0 | Testing & Mocks | Mock servers, tests, Postman | None | Complete |
| 1 | Notifications | Agent sends to Teams | Phase 0 | Complete |
| 2 | Queries (Stateless) | Users query Agent | Phase 0 | Complete |
| 3 | Queries (Stateful) | Queries with memory | Phase 0 + 2 | Pending |

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
AGENT_TIMEOUT=4.5
AGENT_MAX_RETRIES=1
```

### Phase 3 (Add)
```bash
SESSION_STORE=redis
REDIS_URL=redis://localhost:6379/0
SESSION_TTL_HOURS=24
SESSION_MAX_MESSAGES=50
```

## Quality Gates

Before transitioning phases, ensure quality checks pass:

### Development Workflow

```bash
# Install development dependencies
pip install -r requirements/dev.txt

# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type pre-push
```

### Quality Commands

| Command | Description | When to Use |
|---------|-------------|-------------|
| `make lint` | Ruff linting + formatting | Before commit |
| `make type-check` | MyPy static analysis | Before commit |
| `make security` | Bandit security scan | Before push |
| `make test` | Run tests with coverage | Before push |
| `make pre-push` | All of the above | Before git push |
| `make find-gaps` | Find untested code | When improving coverage |

### Coverage Requirements

| Phase | Minimum Coverage | Current |
|-------|------------------|---------|
| 0 | 70% | 100% |
| 1 | 70% | 61-100% |
| 2 | 70% | 83-100% |
| Overall | 70% | 83% |

### CI/CD Pipeline

GitHub Actions runs automatically on push/PR:

1. **Lint & Format** - Ruff
2. **Type Check** - MyPy
3. **Security Scan** - Bandit
4. **Tests & Coverage** - Pytest (70% threshold)

## Quick Start

```bash
# 1. Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/base.txt
pip install -r requirements/dev.txt
cp .env.example .env

# 2. Install hooks
pre-commit install
pre-commit install --hook-type pre-push

# 3. Start mocks
python scripts/phase0/start_mock_agent.py &
python scripts/phase0/start_mock_webhook.py &

# 4. Test
python scripts/phase0/msteams_client.py

# 5. Run tests
pytest tests/phase0/

# 6. Quality check
make pre-push

# 7. When ready, proceed to next phase
```

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── mocks/               # Mock servers
│   ├── mock_agent_server.py
│   ├── mock_webhook_receiver.py
│   └── mock_responses.py
├── phase0/              # Phase 0 tests (18 tests)
│   ├── test_mock_agent.py
│   ├── test_mock_responses.py
│   └── test_mock_webhook.py
├── phase1/              # Phase 1 tests (24 tests)
│   ├── test_cards.py
│   ├── test_notifier_api.py
│   ├── test_notifier_service.py
│   └── test_webhook_sender.py
├── phase2/              # Phase 2 tests (70 tests)
│   ├── test_agent_client.py
│   ├── test_agent_models.py
│   ├── test_handler.py
│   ├── test_hmac.py
│   ├── test_models.py
│   └── test_receiver_api.py
└── core/                # Core module tests (24 tests)
    ├── test_config.py
    └── test_exceptions.py
```

**Total: 174 tests**
