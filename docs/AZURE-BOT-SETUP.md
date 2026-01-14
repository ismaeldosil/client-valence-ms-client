# Azure Bot Setup Guide for Valerie MS Teams Client

This guide walks through setting up an Azure Bot to enable Bot Framework integration with the Valerie MS Teams client.

---

## Prerequisites

- Azure subscription with permissions to create resources
- MS Teams client deployed (Railway URL or your domain)
- Admin access to Microsoft Teams tenant

---

## Step 1: Create Azure Bot Resource

### 1.1 Navigate to Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Sign in with your Azure account

### 1.2 Create a New Bot

1. Click **"Create a resource"**
2. Search for **"Azure Bot"**
3. Click **"Create"**

### 1.3 Configure Bot Settings

Fill in the following:

| Field | Value |
|-------|-------|
| **Bot handle** | `valerie-teams-bot` (unique name) |
| **Subscription** | Select your subscription |
| **Resource group** | Create new or use existing |
| **Data residency** | Global (or your preferred region) |
| **Pricing tier** | F0 (Free) for testing, S1 for production |
| **Type of App** | Multi Tenant |
| **Creation type** | Create new Microsoft App ID |

4. Click **"Review + create"**
5. Click **"Create"**

---

## Step 2: Get Bot Credentials

### 2.1 Get Microsoft App ID

1. Go to your newly created Bot resource
2. Click **"Configuration"** in the left menu
3. Copy the **Microsoft App ID** (looks like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

### 2.2 Create Client Secret (App Password)

1. In the Configuration page, click **"Manage Password"** (next to Microsoft App ID)
2. This opens the Azure AD App Registration
3. Go to **"Certificates & secrets"**
4. Click **"New client secret"**
5. Description: `Valerie Bot Secret`
6. Expiration: Choose appropriate duration (recommended: 24 months)
7. Click **"Add"**
8. **IMPORTANT**: Copy the **Value** immediately (you won't see it again!)

---

## Step 3: Configure Messaging Endpoint

### 3.1 Set the Endpoint URL

1. Go back to your Bot resource
2. Click **"Configuration"**
3. Set **Messaging endpoint** to:

```
https://YOUR-RAILWAY-DOMAIN/api/messages
```

**Example for Railway deployment:**
```
https://teams-client-production.up.railway.app/api/messages
```

4. Click **"Apply"**

---

## Step 4: Enable Microsoft Teams Channel

### 4.1 Add Teams Channel

1. In your Bot resource, click **"Channels"** in the left menu
2. Click **"Microsoft Teams"** icon
3. Accept the Terms of Service
4. Click **"Apply"**

### 4.2 Configure Teams Channel (Optional)

1. Click on the Teams channel to configure
2. **Messaging** tab:
   - Enable **"Enable messaging"**
3. Click **"Apply"**

---

## Step 5: Configure Environment Variables

Add these to your Railway deployment (or `.env` file):

```env
# Integration Mode
TEAMS_INTEGRATION_MODE=dual

# Azure Bot Credentials (from Step 2)
MICROSOFT_APP_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MICROSOFT_APP_PASSWORD=your-client-secret-value

# Optional: Bot Service URL (default is fine for most cases)
BOT_SERVICE_URL=https://smba.trafficmanager.net/amer/
```

### Railway Configuration

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Select your MS Teams client project
3. Go to **Variables**
4. Add the variables above
5. Deploy will restart automatically

---

## Step 6: Install Bot in Teams

### Option A: Add for Testing (Development)

1. In Azure Bot resource, go to **"Channels"**
2. Click **"Open in Teams"** button
3. Teams will open with the bot
4. Click **"Add"** to add to your personal chat

### Option B: Add to Teams App Catalog (Production)

1. Go to [Teams Admin Center](https://admin.teams.microsoft.com)
2. Navigate to **Teams apps > Manage apps**
3. Click **"Upload new app"**
4. Create a Teams app manifest (see below)

---

## Step 7: Create Teams App Manifest (Production)

For production deployment, create a Teams app package:

### 7.1 Create manifest.json

```json
{
  "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "1.0.0",
  "id": "YOUR-MICROSOFT-APP-ID",
  "packageName": "com.reea.valerie",
  "developer": {
    "name": "REEA Global",
    "websiteUrl": "https://reea.global",
    "privacyUrl": "https://reea.global/privacy",
    "termsOfUseUrl": "https://reea.global/terms"
  },
  "name": {
    "short": "Valerie",
    "full": "Valerie AI Assistant"
  },
  "description": {
    "short": "AI-powered assistant for your organization",
    "full": "Valerie is an AI assistant that helps you find information and answers questions about company policies, procedures, and more."
  },
  "icons": {
    "outline": "outline.png",
    "color": "color.png"
  },
  "accentColor": "#5558AF",
  "bots": [
    {
      "botId": "YOUR-MICROSOFT-APP-ID",
      "scopes": ["personal", "team", "groupchat"],
      "supportsFiles": false,
      "isNotificationOnly": false,
      "commandLists": [
        {
          "scopes": ["personal", "team", "groupchat"],
          "commands": [
            {
              "title": "help",
              "description": "Show available commands"
            },
            {
              "title": "status",
              "description": "Check bot status"
            },
            {
              "title": "clear",
              "description": "Clear conversation history"
            }
          ]
        }
      ]
    }
  ],
  "permissions": ["identity", "messageTeamMembers"],
  "validDomains": [
    "teams-client-production.up.railway.app"
  ]
}
```

### 7.2 Create App Package

1. Create icons (32x32 outline.png, 192x192 color.png)
2. Put manifest.json and icons in a folder
3. Zip the contents (not the folder itself)
4. Upload to Teams Admin Center

---

## Step 8: Verify Setup

### 8.1 Check Health Endpoint

```bash
curl https://YOUR-RAILWAY-DOMAIN/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "valerie-teams-client",
  "integration_mode": "dual",
  "webhook_enabled": true,
  "bot_framework_enabled": true
}
```

### 8.2 Check Bot Framework Endpoint

```bash
curl https://YOUR-RAILWAY-DOMAIN/api/messages/health
```

Expected response:
```json
{
  "status": "healthy",
  "bot_framework": true,
  "adapter_initialized": true,
  "bot_initialized": true
}
```

### 8.3 Test in Teams

1. Open Microsoft Teams
2. Find Valerie bot in chat
3. Send a message: `Hello`
4. Bot should respond

**Thread Reply Test (Bot Framework advantage):**
1. Bot responds to your message
2. Reply to the bot's message in the thread
3. Bot should respond WITHOUT needing @mention

---

## Troubleshooting

### Bot Not Responding

1. **Check logs in Railway:**
   ```bash
   railway logs
   ```

2. **Verify credentials:**
   - Ensure `MICROSOFT_APP_ID` matches Azure Bot
   - Ensure `MICROSOFT_APP_PASSWORD` is the secret Value (not ID)

3. **Check endpoint:**
   - URL must be HTTPS
   - URL must be publicly accessible
   - URL must end with `/api/messages`

### 401 Unauthorized Errors

- App Password may have expired
- Create a new client secret in Azure AD

### Bot Added But No Messages

- Check Teams channel is enabled in Azure Bot
- Verify `TEAMS_INTEGRATION_MODE=dual` or `bot`

### Thread Replies Not Working

- Ensure Bot Framework mode is enabled
- Check `bot_framework_enabled: true` in health response

---

## Security Considerations

1. **Rotate secrets regularly** - Create new App Password every 6-12 months
2. **Use Key Vault** (optional) - Store secrets in Azure Key Vault for production
3. **Monitor activity** - Check Azure Bot analytics for unusual activity
4. **Limit permissions** - Only grant necessary permissions in manifest

---

## Quick Reference

| Item | Value |
|------|-------|
| Messaging Endpoint | `https://YOUR-DOMAIN/api/messages` |
| Health Check | `https://YOUR-DOMAIN/health` |
| Bot API Health | `https://YOUR-DOMAIN/api/messages/health` |
| Integration Mode | `TEAMS_INTEGRATION_MODE=dual` |

---

## Support

- [Azure Bot Service Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Teams Bot Development](https://docs.microsoft.com/en-us/microsoftteams/platform/bots/what-are-bots)
- [Bot Framework SDK](https://github.com/microsoft/botbuilder-python)
