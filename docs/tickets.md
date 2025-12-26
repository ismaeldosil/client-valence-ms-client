# Tickets - Teams Agent Integration

## Nomenclatura

- `[F0]-XXX` - Fase 0: Testing & Mocks
- `[F1]-XXX` - Fase 1: Notificaciones (Agent → Teams)
- `[F2]-XXX` - Fase 2: Consultas Stateless (Teams → Agent)
- `[F3]-XXX` - Fase 3: Consultas Stateful (con memoria)

---

# Fase 0: Testing & Mocks

## [F0]-001: Project Setup & Base Structure
**Estado:** ✅ Completado
**Descripción:** Estructura inicial del proyecto, pyproject.toml, requirements, .env

## [F0]-002: Core Module - Configuration
**Estado:** ✅ Completado
**Descripción:** Módulo de configuración con pydantic-settings

## [F0]-003: Core Module - Exceptions
**Estado:** ✅ Completado
**Descripción:** Jerarquía de excepciones personalizadas

## [F0]-004: Core Module - Logging
**Estado:** ✅ Completado
**Descripción:** Configuración de structlog

## [F0]-005: Mock Responses Data
**Estado:** ✅ Completado
**Descripción:** Base de conocimiento para respuestas mock

## [F0]-006: Mock Agent Server
**Estado:** ✅ Completado
**Descripción:** FastAPI server simulando agente AI en puerto 8080

## [F0]-007: Mock Webhook Receiver
**Estado:** ✅ Completado
**Descripción:** FastAPI server simulando webhook receiver en puerto 3000

## [F0]-008: Start Scripts
**Estado:** ✅ Completado
**Descripción:** Scripts para iniciar mock servers

## [F0]-009: MS Teams Client
**Estado:** ✅ Completado
**Descripción:** Cliente Python para testing interactivo

## [F0]-010: Run All Endpoints Script
**Estado:** ✅ Completado
**Descripción:** Script que prueba todos los endpoints

## [F0]-011: Pytest Configuration & Fixtures
**Estado:** ✅ Completado
**Descripción:** Configuración de pytest y fixtures

## [F0]-012: Unit Tests
**Estado:** ✅ Completado
**Descripción:** 28 tests unitarios para fase 0

## [F0]-013: Postman Collection
**Estado:** ✅ Completado
**Descripción:** Colección Postman con todos los endpoints

## [F0]-014: Documentation
**Estado:** ✅ Completado
**Descripción:** README, API Reference, API Design Explanation

---

# Fase 1: Notificaciones (Agent → Teams)

## [F1]-001: Teams Sender Protocol
**Estado:** Pendiente
**Prioridad:** Critical
**Descripción:** Definir Protocol/Interface para envío a Teams

**Archivos a crear:**
- `src/teams/sender/__init__.py`
- `src/teams/sender/base.py`

**Modelo:**
```python
from typing import Protocol

class TeamsSender(Protocol):
    async def send_text(self, webhook_url: str, text: str) -> bool: ...
    async def send_card(self, webhook_url: str, card: dict) -> bool: ...
```

**Criterios de Aceptación:**
- [ ] Protocol definido con type hints
- [ ] Documentación de métodos

---

## [F1]-002: Webhook Sender Implementation
**Estado:** Pendiente
**Prioridad:** Critical
**Dependencias:** [F1]-001

**Descripción:** Implementar sender via Incoming Webhook

**Archivos a crear:**
- `src/teams/sender/webhook_sender.py`

**Criterios de Aceptación:**
- [ ] POST a webhook URL
- [ ] Envío de texto simple
- [ ] Envío de Adaptive Cards
- [ ] Logging estructurado

---

## [F1]-003: Retry Logic & Error Handling
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F1]-002

**Descripción:** Retry con backoff exponencial y manejo de errores HTTP

**Criterios de Aceptación:**
- [ ] Retry configurable (default 3)
- [ ] Backoff exponencial
- [ ] Manejo de errores HTTP 4xx/5xx
- [ ] Timeout handling

---

## [F1]-004: Adaptive Card Builder
**Estado:** Pendiente
**Prioridad:** Critical

**Descripción:** Builder para crear Adaptive Cards

**Archivos a crear:**
- `src/teams/sender/cards.py`
- `src/teams/sender/templates/`

**Nota Técnica:** Solo `openURL` action está soportado en Teams Outgoing Webhooks. Otros actions no funcionarán.

**Criterios de Aceptación:**
- [ ] Build alert card
- [ ] Build info card
- [ ] Build report card
- [ ] Colores por prioridad
- [ ] Schema version 1.4

---

## [F1]-005: Card Templates JSON
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F1]-004

**Archivos a crear:**
- `src/teams/sender/templates/alert.json`
- `src/teams/sender/templates/info.json`
- `src/teams/sender/templates/report.json`

**Criterios de Aceptación:**
- [ ] Templates válidos según Adaptive Cards schema
- [ ] Variables con placeholders {{variable}}

---

## [F1]-006: Notification Models
**Estado:** Pendiente
**Prioridad:** High

**Archivos a crear:**
- `src/notifier/__init__.py`
- `src/notifier/models.py`

**Modelo:**
```python
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Notification:
    id: str
    channel: str
    message: str
    title: Optional[str]
    card_type: Optional[str]
    priority: Priority
    status: NotificationStatus
    created_at: datetime
    sent_at: Optional[datetime]
```

---

## [F1]-007: Channel Registry
**Estado:** Pendiente
**Prioridad:** High

**Archivos a crear:**
- `src/notifier/channels.py`

**Descripción:** Registro de canales con sus webhook URLs

**Criterios de Aceptación:**
- [ ] Cargar canales desde settings
- [ ] Get channel by name
- [ ] List all channels
- [ ] Validate webhook URL format

---

## [F1]-008: Notification Service
**Estado:** Pendiente
**Prioridad:** Critical
**Dependencias:** [F1]-002, [F1]-004, [F1]-006, [F1]-007

**Archivos a crear:**
- `src/notifier/service.py`

**Criterios de Aceptación:**
- [ ] notify() method
- [ ] Selección automática de formato (text vs card)
- [ ] Logging de envíos
- [ ] Tracking de status

---

## [F1]-009: Notifier API
**Estado:** Pendiente
**Prioridad:** Critical
**Dependencias:** [F1]-008

**Archivos a crear:**
- `src/api/__init__.py`
- `src/api/notifier_api.py`

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/v1/notify | Enviar notificación |
| GET | /api/v1/channels | Listar canales |

**Criterios de Aceptación:**
- [ ] FastAPI app
- [ ] Swagger docs
- [ ] Input validation

---

## [F1]-010: API Key Authentication
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F1]-009

**Descripción:** Autenticación con X-API-Key header

**Criterios de Aceptación:**
- [ ] Header X-API-Key requerido
- [ ] 401 si key inválida
- [ ] Key configurable via env

---

## [F1]-011: Phase 1 Configuration
**Estado:** Pendiente
**Prioridad:** High

**Archivos a modificar:**
- `src/core/config.py`

**Variables a agregar:**
```python
# Fase 1
teams_webhook_alerts: Optional[str] = None
teams_webhook_reports: Optional[str] = None
teams_webhook_general: Optional[str] = None
notifier_api_key: str = "dev-api-key"
notifier_port: int = 8000
```

---

## [F1]-012: Unit Tests - Sender
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F1]-002, [F1]-003

**Archivos a crear:**
- `tests/phase1/__init__.py`
- `tests/phase1/test_webhook_sender.py`

---

## [F1]-013: Unit Tests - Cards
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F1]-004

**Archivos a crear:**
- `tests/phase1/test_cards.py`

---

## [F1]-014: Unit Tests - Service
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F1]-008

**Archivos a crear:**
- `tests/phase1/test_notifier_service.py`

---

## [F1]-015: Integration Test
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F1]-009

**Archivos a crear:**
- `tests/phase1/test_integration.py`

---

## [F1]-016: Phase 1 Requirements
**Estado:** Pendiente
**Prioridad:** Medium

**Archivos a crear:**
- `requirements/phase1.txt`

---

## [F1]-017: Send Notification Script
**Estado:** Pendiente
**Prioridad:** Medium
**Dependencias:** [F1]-008

**Archivos a crear:**
- `scripts/phase1/send_notification.py`

---

## [F1]-018: Documentation Updates
**Estado:** Pendiente
**Prioridad:** Medium

**Archivos a modificar:**
- `README.md`
- `docs/api-reference.md`

---

# Fase 2: Consultas Stateless (Teams → Agent)

## [F2]-001: HMAC Security Module
**Estado:** Pendiente
**Prioridad:** Critical

**Descripción:** Verificación HMAC-SHA256 para mensajes de Teams

**Archivos a crear:**
- `src/teams/receiver/__init__.py`
- `src/teams/receiver/security.py`

**Implementación (de Microsoft Docs):**
```python
import hmac
import hashlib
import base64

def verify_hmac(body: bytes, auth_header: str, secret: str) -> bool:
    """
    Verifica HMAC-SHA256 del mensaje de Teams.

    Teams envía header: "HMAC <base64-signature>"
    Secret viene en Base64 desde Teams.
    """
    if not auth_header.startswith("HMAC "):
        return False

    provided_signature = auth_header[5:]  # Remove "HMAC "

    # Secret from Teams is Base64 encoded
    key_bytes = base64.b64decode(secret)

    # Compute HMAC-SHA256
    computed = hmac.new(key_bytes, body, hashlib.sha256)
    expected_signature = base64.b64encode(computed.digest()).decode()

    return hmac.compare_digest(provided_signature, expected_signature)
```

**Criterios de Aceptación:**
- [ ] Verificación HMAC-SHA256
- [ ] Secret en Base64
- [ ] Comparación timing-safe
- [ ] Tests con vectors conocidos

---

## [F2]-002: Teams Message Models (Completo)
**Estado:** Pendiente
**Prioridad:** Critical

**Descripción:** Modelos completos según Azure Bot Service schema

**Archivos a crear:**
- `src/teams/receiver/models.py`

**Modelo Completo (basado en Microsoft Docs):**
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TeamsUser(BaseModel):
    id: str
    name: str
    aadObjectId: Optional[str] = None

class TeamsRecipient(BaseModel):
    id: str
    name: str

class TeamsConversation(BaseModel):
    id: str
    conversationType: Optional[str] = None  # "channel", "personal", "groupChat"
    tenantId: Optional[str] = None
    name: Optional[str] = None

class TeamsMention(BaseModel):
    type: str = "mention"
    mentioned: TeamsUser
    text: str  # e.g., "<at>BotName</at>"

class TeamsMessage(BaseModel):
    type: str = "message"
    id: str
    timestamp: Optional[datetime] = None
    serviceUrl: Optional[str] = None
    channelId: str = "msteams"
    from_: Optional[TeamsUser] = Field(None, alias="from")
    conversation: Optional[TeamsConversation] = None
    recipient: Optional[TeamsRecipient] = None
    text: str
    entities: List[TeamsMention] = []

    class Config:
        populate_by_name = True

class WebhookResponse(BaseModel):
    type: str = "message"
    text: str
```

**Nota:** Teams solo funciona en canales PÚBLICOS, no en privados ni personales.

---

## [F2]-003: Message Text Extractor
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F2]-002

**Descripción:** Extraer texto limpio removiendo @mentions usando entities

**Implementación:**
```python
def extract_clean_text(message: TeamsMessage) -> str:
    """
    Extrae texto sin @mentions usando el array entities.

    Más robusto que split por </at>.
    """
    text = message.text

    for entity in message.entities:
        if entity.type == "mention":
            text = text.replace(entity.text, "").strip()

    return text
```

---

## [F2]-004: Teams Message Handler (Stateless)
**Estado:** Pendiente
**Prioridad:** Critical
**Dependencias:** [F2]-002, [F2]-003

**Archivos a crear:**
- `src/teams/receiver/handler.py`

**⚠️ CRÍTICO - Timeout:**
```python
# Microsoft Docs: "5 seconds before connection timeout"
# NO 10 segundos como decía el prompt original
TEAMS_TIMEOUT = 5.0
SAFE_TIMEOUT = 4.0  # Dejar margen
```

**Criterios de Aceptación:**
- [ ] Handler stateless (sin historial)
- [ ] Timeout < 5 segundos
- [ ] Manejo de errores graceful
- [ ] Respuesta en formato Teams

---

## [F2]-005: Webhook Receiver App
**Estado:** Pendiente
**Prioridad:** Critical
**Dependencias:** [F2]-001, [F2]-004

**Archivos a crear:**
- `src/teams/receiver/app.py`

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /webhook | Recibir mensajes de Teams |

**Flow:**
1. Recibir POST de Teams
2. Verificar HMAC
3. Parsear mensaje
4. Extraer texto limpio
5. Query al agent
6. Responder en < 5s

---

## [F2]-006: Agent Client Protocol
**Estado:** Pendiente
**Prioridad:** Critical

**Archivos a crear:**
- `src/agent/__init__.py`
- `src/agent/base.py`
- `src/agent/models/__init__.py`
- `src/agent/models/request.py`
- `src/agent/models/response.py`

**Modelo:**
```python
from typing import Protocol, Optional
from dataclasses import dataclass, field

@dataclass
class RequestContext:
    platform: str = "teams"
    user_id: str = ""
    user_name: str = ""
    conversation_id: str = ""
    tenant_id: str = ""

@dataclass
class AgentResponse:
    text: str
    sources: list[str] = field(default_factory=list)
    confidence: Optional[float] = None

class AgentClient(Protocol):
    async def query(
        self,
        message: str,
        context: RequestContext,
        timeout: Optional[float] = None
    ) -> AgentResponse: ...

    async def health_check(self) -> bool: ...
```

---

## [F2]-007: REST Agent Client
**Estado:** Pendiente
**Prioridad:** Critical
**Dependencias:** [F2]-006

**Archivos a crear:**
- `src/agent/clients/__init__.py`
- `src/agent/clients/rest_client.py`

**Criterios de Aceptación:**
- [ ] Implementar AgentClient protocol
- [ ] Usar httpx async
- [ ] Timeout configurable
- [ ] Bearer token auth
- [ ] Retry logic

---

## [F2]-008: Agent Client Factory
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F2]-007

**Archivos a crear:**
- `src/agent/factory.py`

---

## [F2]-009: Timeout & Error Handling
**Estado:** Pendiente
**Prioridad:** Critical
**Dependencias:** [F2]-004, [F2]-007

**Descripción:** Manejo especial de timeout para cumplir con límite de 5s de Teams

**Criterios de Aceptación:**
- [ ] Timeout total < 5s
- [ ] Respuesta fallback si timeout
- [ ] Logging de timeouts
- [ ] Métricas de latencia

---

## [F2]-010: Phase 2 Configuration
**Estado:** Pendiente
**Prioridad:** High

**Archivos a modificar:**
- `src/core/config.py`

**Variables a agregar:**
```python
# Fase 2
teams_webhook_secret: str = ""  # HMAC secret from Teams
receiver_port: int = 3000
agent_protocol: str = "rest"
agent_base_url: str = "http://localhost:8080"
agent_api_key: Optional[str] = None
agent_timeout: float = 4.0  # < 5s Teams limit
```

---

## [F2]-011: Unit Tests - Security
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F2]-001

**Archivos a crear:**
- `tests/phase2/__init__.py`
- `tests/phase2/test_security.py`

---

## [F2]-012: Unit Tests - Models
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F2]-002

**Archivos a crear:**
- `tests/phase2/test_models.py`

---

## [F2]-013: Unit Tests - Handler
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F2]-004

**Archivos a crear:**
- `tests/phase2/test_handler.py`

---

## [F2]-014: Unit Tests - Agent Client
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F2]-007

**Archivos a crear:**
- `tests/phase2/test_agent_client.py`

---

## [F2]-015: Integration Test
**Estado:** Pendiente
**Prioridad:** High
**Dependencias:** [F2]-005

**Archivos a crear:**
- `tests/phase2/test_integration.py`

---

## [F2]-016: Phase 2 Requirements
**Estado:** Pendiente
**Prioridad:** Medium

**Archivos a crear:**
- `requirements/phase2.txt`

---

## [F2]-017: Simulate Teams Message Script
**Estado:** Pendiente
**Prioridad:** Medium
**Dependencias:** [F2]-005

**Archivos a crear:**
- `scripts/phase2/simulate_teams_message.py`

---

## [F2]-018: Documentation - Limitations
**Estado:** Pendiente
**Prioridad:** Medium

**Descripción:** Documentar limitaciones de Outgoing Webhooks

**Limitaciones a documentar:**
- Solo canales públicos (no privados/personales)
- Timeout de 5 segundos
- Solo action openURL en cards
- No puede acceder roster/channels API
- Requiere @mention para activar
- HMAC token no expira

---

## [F2]-019: Documentation Updates
**Estado:** Pendiente
**Prioridad:** Medium

**Archivos a modificar:**
- `README.md`
- `docs/api-reference.md`

---

# Resumen por Fase

| Fase | Total Tickets | Completados | Pendientes |
|------|---------------|-------------|------------|
| F0 | 14 | 14 | 0 |
| F1 | 18 | 0 | 18 |
| F2 | 19 | 0 | 19 |
| **Total** | **51** | **14** | **37** |

---

# Orden de Ejecución Recomendado

## Fase 1 - Sprints
```
Sprint 1: [F1]-001 → [F1]-002 → [F1]-003 → [F1]-011
Sprint 2: [F1]-004 → [F1]-005
Sprint 3: [F1]-006 → [F1]-007 → [F1]-008
Sprint 4: [F1]-009 → [F1]-010
Sprint 5: [F1]-012 → [F1]-013 → [F1]-014 → [F1]-015
Sprint 6: [F1]-016 → [F1]-017 → [F1]-018
```

## Fase 2 - Sprints
```
Sprint 1: [F2]-001 → [F2]-002 → [F2]-003 → [F2]-010
Sprint 2: [F2]-006 → [F2]-007 → [F2]-008
Sprint 3: [F2]-004 → [F2]-009
Sprint 4: [F2]-005
Sprint 5: [F2]-011 → [F2]-012 → [F2]-013 → [F2]-014 → [F2]-015
Sprint 6: [F2]-016 → [F2]-017 → [F2]-018 → [F2]-019
```
