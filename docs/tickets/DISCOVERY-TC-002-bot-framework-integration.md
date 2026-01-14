# Discovery: Bot Framework Integration for MS Teams Client

**Ticket:** TC-002
**Type:** Discovery
**Status:** Complete
**Date:** 2026-01-14

---

## Objetivo

Investigar e implementar Microsoft Bot Framework como alternativa a Outgoing Webhooks para el cliente de MS Teams, habilitando respuestas automáticas en threads sin necesidad de @mention.

---

## Contexto

El cliente de MS Teams utilizaba Outgoing Webhooks, que tiene limitaciones:
- Requiere @mention en cada mensaje
- No soporta mensajes proactivos
- Timeout de 5 segundos
- Sin soporte para Adaptive Cards interactivas

---

## Solución Implementada

### Arquitectura Dual Mode

Se implementó soporte para ambos modos de integración:

```
TEAMS_INTEGRATION_MODE = "webhook" | "bot" | "dual"
```

| Modo | Descripción |
|------|-------------|
| `webhook` | Solo Outgoing Webhooks (comportamiento original) |
| `bot` | Solo Bot Framework |
| `dual` | Ambos activos simultáneamente |

### Componentes Creados

1. **UnifiedMessageProcessor** (`src/teams/common/processor.py`)
   - Procesamiento compartido de mensajes
   - Manejo de comandos (/help, /clear, /status)
   - Gestión de sesiones

2. **ValerieBot** (`src/teams/bot_framework/bot.py`)
   - ActivityHandler para Bot Framework
   - Recibe mensajes sin @mention en threads
   - Manejo de conversation updates

3. **Bot Adapter** (`src/teams/bot_framework/adapter.py`)
   - Configuración de autenticación
   - Soporte Single/Multi Tenant

4. **ProactiveMessenger** (`src/teams/bot_framework/proactive.py`)
   - Envío de mensajes no solicitados
   - Almacenamiento de ConversationReferences

5. **Bot API** (`src/api/bot_api.py`)
   - Endpoint `/api/messages` para Bot Framework
   - Health check `/api/messages/health`

---

## Configuración Azure

### Pasos Clave

1. Crear Azure Bot (Single Tenant → Multi-Tenant)
2. Obtener App ID y Client Secret (**Value**, no Secret ID)
3. Configurar App Registration como Multi-Tenant
4. Agregar permisos `User.Read` en API Permissions
5. Configurar Messaging Endpoint
6. Habilitar canal de Microsoft Teams

### Variables de Entorno

```env
TEAMS_INTEGRATION_MODE=dual
MICROSOFT_APP_ID=xxx
MICROSOFT_APP_PASSWORD=xxx
AGENT_BASE_URL=https://...
```

---

## Problemas Encontrados y Soluciones

| Problema | Causa | Solución |
|----------|-------|----------|
| Token not supplied | Credenciales incorrectas | Usar el **Value** del secret, no el ID |
| Tenant not found | Espacios en variables | Limpiar espacios en blanco |
| OIDC Discovery failed | Single Tenant mal configurado | Cambiar a Multi-Tenant |
| No permission in Teams | Restricciones de admin | Developer Program o pedir permisos |

---

## Documentación Creada

- `docs/AZURE-BOT-TUTORIAL.md` - Tutorial paso a paso
- `docs/AZURE-BOT-SETUP.md` - Guía de referencia rápida

---

## Testing

- 135 tests pasando
- Health checks funcionales
- Web Chat de Azure funcionando
- Pendiente: prueba en Teams (requiere permisos de admin)

---

## Próximos Pasos

1. Obtener acceso a Teams con permisos de admin
2. Probar thread replies sin @mention
3. Implementar Adaptive Cards interactivas
4. Configurar mensajes proactivos

---

## Referencias

- [Azure Bot Service Docs](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Bot Framework SDK Python](https://github.com/microsoft/botbuilder-python)
- [Teams Bot Development](https://docs.microsoft.com/en-us/microsoftteams/platform/bots/)
