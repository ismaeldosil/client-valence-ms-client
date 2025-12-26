# Microsoft Teams Webhook Setup Guide

**AI Agent Integration - Configuration Steps**

---

## Overview

This guide covers the setup of Microsoft Teams webhooks for AI Agent integration:

| Webhook Type | Direction | Purpose |
|--------------|-----------|---------|
| **Incoming Webhook** | Agent → Teams | Send notifications to Teams channels |
| **Outgoing Webhook** | Teams → Agent | Receive messages from Teams users |

---

# Part 1: Incoming Webhook Setup

**Purpose:** Allow the AI Agent to send notifications to Teams channels.

---

## Prerequisites

Before starting, verify you have:

| Requirement | Description |
|-------------|-------------|
| **Teams Admin Access** | Or member permissions to add connectors |
| **Channel Access** | Access to the target channels (Alerts, Reports, General) |
| **Member Permissions** | Teams Settings → Member permissions → "Allow members to create, update, and remove connectors" must be enabled |

---

## Step 1: Navigate to the Channel

1. Open **Microsoft Teams**
2. Select **Teams** from the left sidebar
3. Navigate to the team containing your target channel
4. Select the channel where notifications will be sent (e.g., "Alerts")

---

## Step 2: Access Channel Settings

### For New Teams Client:

1. Click the **"..."** (More options) button to the right of the channel name
2. Select **"Manage channel"**
3. Select **"Edit"**

### For Classic Teams Client:

1. Click the **"..."** (More options) button in the upper-right corner
2. Select **"Connectors"** from the dropdown menu

---

## Step 3: Add Incoming Webhook

1. In the connectors list, search for **"Incoming Webhook"**
2. Click **"Add"** next to Incoming Webhook
3. Click **"Add"** again in the confirmation dialog

---

## Step 4: Configure the Webhook

1. **Name:** Enter a descriptive name (e.g., "Agent Notifications - Alerts")
2. **Image:** (Optional) Upload an icon for the webhook
3. Click **"Create"**

---

## Step 5: Copy the Webhook URL

> **⚠️ IMPORTANT:** The webhook URL is only shown once. Copy it immediately before closing the dialog.

1. After clicking "Create", a unique webhook URL will be displayed
2. Click **"Copy"** to copy the URL to your clipboard
3. **Save this URL securely** - you will need to send it to the development team
4. Click **"Done"**

**Example URL format:**
```
https://outlook.office.com/webhook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/IncomingWebhook/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## Step 6: Repeat for Each Channel

Repeat Steps 1-5 for each channel:

| Channel | Webhook Name | Status |
|---------|--------------|--------|
| Alerts | Agent Notifications - Alerts | ☐ Pending |
| Reports | Agent Notifications - Reports | ☐ Pending |
| General | Agent Notifications - General | ☐ Pending |

---

## Verification

To verify the webhook is working, you can send a test message using curl:

```bash
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from the AI Agent! Webhook configured successfully."}'
```

If successful, you should see the message appear in the Teams channel.

---

# Part 2: Outgoing Webhook Setup (Optional - Phase 2)

**Purpose:** Allow Teams users to send messages to the AI Agent using @mentions.

> **Note:** This is only required for Phase 2 (Teams → Agent communication).

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
2. Scroll to **"Create an outgoing webhook"** (under "Upload an app" section)
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
3. **⚠️ CRITICAL:** Copy and save this token securely
4. This token is used to verify messages are from Teams

> **Note:** The HMAC token does not expire and is unique to this webhook configuration.

---

## Information to Send Back

After completing the setup, please provide the following:

### For Incoming Webhooks (Required):

| Channel | Webhook URL |
|---------|-------------|
| Alerts | `https://outlook.office.com/webhook/...` |
| Reports | `https://outlook.office.com/webhook/...` |
| General | `https://outlook.office.com/webhook/...` |

### For Outgoing Webhook (Phase 2 - Optional):

| Item | Value |
|------|-------|
| HMAC Security Token | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| Bot Name | The name you configured |

---

# Technical Specifications

## Incoming Webhook Limits

| Specification | Limit |
|---------------|-------|
| Message Size | 28 KB maximum |
| Rate Limit | 4 requests per second |
| Card Version | Adaptive Cards v1.4 |
| Supported Actions | All card actions |

## Outgoing Webhook Limits

| Specification | Limit |
|---------------|-------|
| Response Timeout | **5 seconds** (connection terminates after) |
| Channel Type | Public channels only |
| Trigger | Requires @mention |
| Supported Actions | Only `openURL` action |

---

# Important Notes

## Deprecation Notice

> **⚠️ Microsoft Notice:** Microsoft 365 Connectors (including Incoming Webhooks) are scheduled for deprecation. While existing webhooks continue to work, consider migrating to **Power Automate Workflows** for new implementations.

## Security Considerations

1. **Keep webhook URLs private** - Anyone with the URL can send messages to your channel
2. **Rotate webhooks** if URLs are compromised
3. **HMAC verification** is required for outgoing webhooks to prevent spoofing

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't find "Connectors" option | Check member permissions in Team Settings |
| Webhook URL not shown | You may have closed the dialog - delete and recreate |
| Messages not appearing | Verify the URL is correct and channel is accessible |
| 429 Too Many Requests | You're exceeding 4 requests/second rate limit |

---

# Checklist

Before sending the configuration back, verify:

- [ ] Incoming Webhook created for **Alerts** channel
- [ ] Incoming Webhook created for **Reports** channel
- [ ] Incoming Webhook created for **General** channel
- [ ] All webhook URLs copied and saved
- [ ] Test message sent successfully to each channel
- [ ] (Optional) Outgoing Webhook created with HMAC token saved

---

# Support

If you encounter any issues during setup, please contact:

- **Email:** [your-email@company.com]
- **Teams:** [Your Name]

We're happy to schedule a call to walk through the setup together.
