# Microsoft Teams Workflow Setup Guide

**AI Agent Integration - Configuration Steps**

---

## Overview

This guide covers the setup of Microsoft Teams Workflows for AI Agent integration using **Power Automate Workflows** (the modern replacement for legacy Incoming Webhooks).

| Integration Type | Direction | Purpose |
|------------------|-----------|---------|
| **Workflow Webhook** | Agent → Teams | Send notifications to Teams channels |
| **Outgoing Webhook** | Teams → Agent | Receive messages from Teams users |

> **Note:** Microsoft retired legacy Incoming Webhooks (Office 365 Connectors) in 2025. This guide uses the recommended Power Automate Workflows approach.

---

# Part 1: Workflow Webhook Setup

**Purpose:** Allow the AI Agent to send notifications to Teams channels.

---

## Prerequisites

Before starting, verify you have:

| Requirement | Description |
|-------------|-------------|
| **Microsoft 365 Account** | With access to Power Automate |
| **Teams Access** | Member of the target team and channels |
| **Workflows App** | Installed in Teams (or access to Power Automate portal) |

---

## Step 1: Access Workflows in Teams

### Option A: From the Channel (Recommended)

1. Open **Microsoft Teams**
2. Navigate to the target channel (e.g., "Alerts")
3. Click the **"+"** (Add a tab) or **"..."** (More options) button
4. Search for **"Workflows"**
5. Select the Workflows app

### Option B: From Power Automate Portal

1. Go to [make.powerautomate.com](https://make.powerautomate.com)
2. Sign in with your Microsoft 365 account
3. Click **"Create"** → **"Instant cloud flow"**

---

## Step 2: Create a New Workflow

1. In the Workflows app or Power Automate, search for templates:
   - **"Post to a channel when a webhook request is received"**
   - Or **"When a Teams webhook request is received"**

2. Select the template and click **"Continue"**

3. Verify your connection shows a green checkmark with your username

---

## Step 3: Configure the Workflow

### 3.1 Set the Trigger

The trigger **"When a Teams webhook request is received"** will be pre-configured.

### 3.2 Add Parse JSON Action (Optional but Recommended)

1. Click **"+ New step"**
2. Search for **"Parse JSON"**
3. In the **Content** field, select **"Body"** from dynamic content
4. Click **"Use sample payload to generate schema"**
5. Paste this sample:

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
          {
            "type": "TextBlock",
            "text": "Sample notification"
          }
        ]
      }
    }
  ]
}
```

### 3.3 Configure Post to Channel

1. Click **"+ New step"**
2. Search for **"Post card in a chat or channel"**
3. Configure:
   - **Post as**: Flow bot
   - **Post in**: Channel
   - **Team**: Select your team
   - **Channel**: Select the target channel
   - **Adaptive Card**: Select the parsed content or use dynamic content

---

## Step 4: Save and Get the Webhook URL

1. Click **"Save"** to save the workflow
2. Go back to the trigger step **"When a Teams webhook request is received"**
3. Click on the trigger to expand it
4. Copy the **HTTP POST URL**

> **IMPORTANT:** Save this URL securely - you will need to send it to the development team.

**Example URL format:**
```
https://prod-XX.westus.logic.azure.com:443/workflows/XXXXXXXX/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=XXXXXXXX
```

---

## Step 5: Configure Workflow Security (Recommended)

1. In the workflow, click on the trigger step
2. Under **"Who can trigger the flow?"**, select one of:
   - **Anyone** (less secure, easier setup)
   - **Any user in my tenant** (recommended)
   - **Specific users in my tenant** (most secure)

3. Optionally, add a **Trigger condition** with a secret header

---

## Step 6: Repeat for Each Channel

Repeat Steps 1-5 for each channel:

| Channel | Workflow Name | Status |
|---------|---------------|--------|
| Alerts | Agent Notifications - Alerts | ☐ Pending |
| Reports | Agent Notifications - Reports | ☐ Pending |
| General | Agent Notifications - General | ☐ Pending |

---

## Verification

To verify the workflow is working, send a test message using curl:

```bash
curl -X POST "YOUR_WORKFLOW_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "message",
    "attachments": [{
      "contentType": "application/vnd.microsoft.card.adaptive",
      "contentUrl": null,
      "content": {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [{
          "type": "TextBlock",
          "text": "Hello from the AI Agent!",
          "weight": "Bolder",
          "size": "Medium"
        }]
      }
    }]
  }'
```

If successful, you should see the message appear in the Teams channel.

---

# Part 2: Outgoing Webhook Setup

**Purpose:** Allow Teams users to send messages to the AI Agent using @mentions.

---

## Prerequisites

| Requirement | Description |
|-------------|-------------|
| **Team Owner Access** | Only team owners can create outgoing webhooks |
| **Public Channel** | Outgoing webhooks only work in public channels |
| **HTTPS Endpoint** | A publicly accessible HTTPS URL for your agent |

---

## Step 1: Navigate to Team Settings

1. Select **Teams** from the left sidebar
2. Find your team and click **"..."** (More options)
3. Select **"Manage team"**

---

## Step 2: Access Apps Configuration

1. Select the **"Apps"** tab on the channel page
2. Scroll to **"Create an outgoing webhook"**
3. Click on it to open the configuration dialog

---

## Step 3: Configure the Outgoing Webhook

Fill in the following details:

| Field | Value | Example |
|-------|-------|---------|
| **Name** | Bot display name | `AI Agent` |
| **Callback URL** | Your agent's HTTPS endpoint | `https://your-agent.example.com/webhook` |
| **Description** | Brief description | `AI Agent for HR queries` |
| **Profile Picture** | (Optional) Upload an icon | - |

---

## Step 4: Save the Security Token

1. Click **"Create"**
2. A dialog will appear with the **HMAC security token**

> **CRITICAL:** Copy and save this token securely. This token is used to verify messages are from Teams.

---

# Technical Specifications

## Workflow Webhook Limits

| Specification | Limit |
|---------------|-------|
| Message Format | Adaptive Cards only (JSON) |
| Card Version | Adaptive Cards v1.4 |
| Supported Actions | All card actions |
| Rate Limit | Depends on Power Automate plan |

## Outgoing Webhook Limits

| Specification | Limit |
|---------------|-------|
| Response Timeout | **5 seconds** |
| Channel Type | Public channels only |
| Trigger | Requires @mention |
| Supported Actions | Only `openURL` action |

---

# Important Notes

## Workflow Ownership

> **Important:** Workflows are linked to specific users (owners). If the owner leaves the organization, the workflow may stop working. **Add co-owners** to ensure continuity.

## Security Considerations

1. **Keep workflow URLs private**
2. **Use trigger conditions** with secret headers for additional security
3. **HMAC verification** is required for outgoing webhooks

---

# Checklist

Before sending the configuration back, verify:

- [ ] Workflow created for **Alerts** channel
- [ ] Workflow created for **Reports** channel
- [ ] Workflow created for **General** channel
- [ ] All workflow URLs copied and saved
- [ ] Co-owners added to each workflow
- [ ] Test message sent successfully to each channel
- [ ] (Optional) Outgoing Webhook created with HMAC token saved

---

# Support

If you encounter any issues during setup, please contact us.
