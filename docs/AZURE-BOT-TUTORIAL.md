# Tutorial: Configurar Azure Bot para MS Teams

Este tutorial documenta los pasos exactos para configurar un Azure Bot que funcione con Microsoft Teams.

---

## Requisitos Previos

- Cuenta de Azure con suscripción activa
- Acceso a Microsoft Teams
- Aplicación desplegada con endpoint público (ej: Railway)

---

## Paso 1: Crear el Azure Bot

1. Ve a [Azure Portal](https://portal.azure.com)
2. Click en **"Create a resource"**
3. Busca **"Azure Bot"**
4. Click en **"Create"**

### Configurar el Bot:

| Campo | Valor |
|-------|-------|
| **Bot handle** | `nombre-unico-de-tu-bot` |
| **Subscription** | Selecciona tu suscripción |
| **Resource group** | Click "Create new" → `tu-bot-rg` |
| **Data residency** | Global |
| **Pricing tier** | F0 (Free) |
| **Type of App** | Single Tenant |
| **Creation type** | Create new Microsoft App ID |

5. Click **"Review + create"**
6. Click **"Create"**
7. Espera a que se complete el deployment

---

## Paso 2: Obtener el App ID

1. Ve a tu Azure Bot recién creado
2. Click en **"Configuration"** en el menú izquierdo
3. Copia el **Microsoft App ID** (formato: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

**Guarda este valor** - lo necesitarás después.

---

## Paso 3: Crear el Client Secret (Password)

> **IMPORTANTE**: Debes copiar el **VALUE**, no el **Secret ID**

1. En la página de Configuration, click en **"Manage Password"** (al lado del App ID)
2. Se abre **Azure AD → App registrations**
3. Click en **"Certificates & secrets"** en el menú izquierdo
4. Click en **"New client secret"**
5. Configura:
   - **Description**: `Bot Password`
   - **Expires**: 24 months (recomendado)
6. Click **"Add"**
7. **INMEDIATAMENTE** copia el **VALUE** (columna "Value", NO "Secret ID")

> **ADVERTENCIA**: El Value solo se muestra una vez. Si no lo copiaste, debes crear uno nuevo.

**Diferencia importante**:
- ❌ **Secret ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (GUID - NO usar)
- ✅ **Value**: `_yC8Q~gzM23...` (string alfanumérico - ESTE es el password)

---

## Paso 4: Cambiar a Multi-Tenant

Para que el bot funcione con usuarios de diferentes organizaciones:

1. En **App registrations**, selecciona tu app
2. Click en **"Authentication"** en el menú izquierdo
3. En **"Supported account types"**, selecciona:
   - **"Accounts in any organizational directory (Any Azure AD directory - Multitenant)"**
4. Click **"Save"**

---

## Paso 5: Configurar API Permissions

1. En **App registrations** → tu app
2. Click en **"API permissions"** en el menú izquierdo
3. Click **"Add a permission"**
4. Selecciona **"Microsoft Graph"**
5. Selecciona **"Delegated permissions"**
6. Busca y selecciona: **`User.Read`**
7. Click **"Add permissions"**
8. Click **"Grant admin consent for [tu tenant]"** (botón azul)
9. Verifica que aparezca ✅ verde al lado del permiso

---

## Paso 6: Configurar el Messaging Endpoint

1. Regresa a tu **Azure Bot** (no App Registration)
2. Click en **"Configuration"**
3. En **"Messaging endpoint"**, ingresa:
   ```
   https://tu-dominio.com/api/messages
   ```

   Ejemplo para Railway:
   ```
   https://tu-app-production.up.railway.app/api/messages
   ```

4. Click **"Apply"**

---

## Paso 7: Habilitar Canal de Microsoft Teams

1. En tu Azure Bot, click en **"Channels"** en el menú izquierdo
2. Click en el ícono de **Microsoft Teams**
3. Lee y acepta los términos de servicio
4. Click **"Apply"**

---

## Paso 8: Configurar Variables de Entorno

En tu plataforma de hosting (Railway, Heroku, etc.), configura estas variables:

```env
TEAMS_INTEGRATION_MODE=dual
MICROSOFT_APP_ID=tu-app-id-aqui
MICROSOFT_APP_PASSWORD=tu-secret-value-aqui
```

> **IMPORTANTE**:
> - NO incluyas espacios en blanco al inicio o final de los valores
> - Para Multi-Tenant, NO necesitas `MICROSOFT_APP_TENANT_ID`
> - Si usas Single-Tenant, agrega: `MICROSOFT_APP_TENANT_ID=tu-tenant-id`

---

## Paso 9: Verificar la Configuración

### Health Check del Bot

```bash
curl https://tu-dominio.com/api/messages/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "bot_framework": true,
  "adapter_initialized": true,
  "bot_initialized": true
}
```

### Health Check General

```bash
curl https://tu-dominio.com/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "integration_mode": "dual",
  "webhook_enabled": true,
  "bot_framework_enabled": true
}
```

---

## Paso 10: Probar el Bot

### Opción A: Test in Web Chat (Azure Portal)

1. En tu Azure Bot, click en **"Test in Web Chat"**
2. Escribe un mensaje
3. El bot debería responder

### Opcion B: Abrir en Teams

1. En tu Azure Bot → **Channels**
2. Click en **"Open in Teams"** (en el canal de Microsoft Teams)
3. Teams se abrirá con el bot
4. Click **"Add"** para agregarlo
5. Envía un mensaje para probar

---

## Troubleshooting

### Error: "Processing failed"

**Causa**: Error interno en el procesamiento del mensaje.

**Solución**: Revisa los logs de tu aplicación para ver el error específico.

---

### Error: "Required Authorization token was not supplied"

**Causa**: Las credenciales no coinciden o están mal configuradas.

**Solución**:
1. Verifica que `MICROSOFT_APP_ID` coincida con Azure Bot
2. Verifica que `MICROSOFT_APP_PASSWORD` sea el **Value** (no el Secret ID)
3. Asegúrate de que no hay espacios en blanco en las variables

---

### Error: "Tenant 'xxx' not found"

**Causa**:
1. El Tenant ID es incorrecto
2. Hay espacios en blanco o caracteres extra en el Tenant ID
3. La app es Single-Tenant pero el tenant no existe

**Solución**:
1. Verifica el Tenant ID en Azure AD → Overview
2. Elimina cualquier espacio en blanco
3. Considera cambiar a Multi-Tenant (Paso 4)

---

### Error: "OIDC Discovery failed"

**Causa**: No se puede conectar al servidor de autenticación de Microsoft.

**Solución**:
1. Verifica que el Tenant ID sea correcto
2. Asegúrate de que no hay caracteres extra en las variables de entorno
3. Si usas Multi-Tenant, elimina `MICROSOFT_APP_TENANT_ID`

---

### El bot no responde en Teams

**Causa**: El canal de Teams no está habilitado.

**Solución**:
1. Ve a Azure Bot → Channels
2. Verifica que Microsoft Teams esté listado
3. Si no está, agrégalo (Paso 7)

---

### Error 401 Unauthorized

**Causa**: El App Password expiró o es incorrecto.

**Solución**:
1. Ve a App registrations → Certificates & secrets
2. Crea un nuevo Client Secret
3. Copia el **Value** (no el ID)
4. Actualiza `MICROSOFT_APP_PASSWORD` en tu hosting

---

### Error: "You do not have permission to use this app here"

**Causa**: El administrador de Teams ha restringido la instalación de apps/bots personalizados.

**Solución**:
1. Contacta al administrador de IT para que permita la app
2. Pide que habiliten "sideloading" de apps
3. O usa el Microsoft 365 Developer Program (ver abajo)

---

### Teams Free no permite instalar bots

**Causa**: Teams Free tiene restricciones y no permite instalar bots personalizados.

**Solución**: Usa el Microsoft 365 Developer Program:
1. Ve a [developer.microsoft.com/microsoft-365/dev-program](https://developer.microsoft.com/en-us/microsoft-365/dev-program)
2. Regístrate (es gratis)
3. Obtienes un tenant con Teams completo (E5) por 90 días renovables
4. Tienes control total como administrador

---

## Resumen de Credenciales

| Credencial | Dónde encontrarla | Formato |
|------------|-------------------|---------|
| **App ID** | Azure Bot → Configuration | GUID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| **App Password** | App registrations → Certificates & secrets → **Value** | String: `_yC8Q~abc123...` |
| **Tenant ID** (opcional) | Azure AD → Overview | GUID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |

---

## Referencias

- [Azure Bot Service Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Teams Bot Development](https://docs.microsoft.com/en-us/microsoftteams/platform/bots/what-are-bots)
- [Bot Framework SDK for Python](https://github.com/microsoft/botbuilder-python)
- [App Registration](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
