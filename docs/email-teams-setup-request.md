# MS Teams Integration - Setup Request Email

---

**Subject:** MS Teams Integration Setup - Incoming Webhooks Configuration

---

Hi [Name],

Hope you're doing well! We're ready to connect the AI Agent to Microsoft Teams for sending notifications. Could you help us set up the required webhooks?

## What We Need

We need **Incoming Webhooks** created in the Teams channels where the agent will send notifications:

| Channel | Purpose |
|---------|---------|
| Alerts | Critical alerts and system warnings |
| Reports | Daily/weekly reports and summaries |
| General | General notifications and updates |

## Setup Steps

1. Open Microsoft Teams
2. Go to the channel → Click "..." (More options) → **Connectors**
3. Search for "Incoming Webhook" → Click **Configure**
4. Enter a name (e.g., "Agent Notifications") and upload an icon (optional)
5. Click **Create** → **Copy the webhook URL**
6. Repeat for each channel

> **Note:** The webhook URL is only shown once during setup. Please copy it before closing.

## What to Send Back

Once configured, please send us:

| Item | Example |
|------|---------|
| Alerts Webhook URL | `https://outlook.office.com/webhook/...` |
| Reports Webhook URL | `https://outlook.office.com/webhook/...` |
| General Webhook URL | `https://outlook.office.com/webhook/...` |

## Attachments

- **teams_webhook_setup_guide.pdf** - Step-by-step guide with screenshots
- **postman_collection.json** - Postman collection to test the integration
- **postman_environment.json** - Environment variables template

## Testing

Once we receive the webhook URLs, we'll:
1. Configure the notification service
2. Send a test message to each channel
3. Confirm everything is working

Let me know if you have any questions - happy to jump on a call if needed!

Thanks,
[Your Name]

---

# Alternative - Shorter Version

---

**Subject:** MS Teams Setup Request - Webhook URLs Needed

---

Hi [Name],

Quick request for the MS Teams integration.

**What we need:** Incoming Webhook URLs for 3 channels (Alerts, Reports, General)

**How to create them:**
1. Teams channel → "..." → Connectors → Incoming Webhook → Configure
2. Name it "Agent Notifications" → Create → Copy URL
3. Repeat for each channel

**Send us back:**
- Alerts webhook URL
- Reports webhook URL
- General webhook URL

I've attached a setup guide with screenshots. The webhook URL is only shown once, so please copy it before closing.

Let me know if you need help!

Thanks,
[Your Name]
