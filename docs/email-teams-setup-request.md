# MS Teams Integration - Setup Request Email

---

**Subject:** MS Teams Integration Setup - Power Automate Workflows Configuration

---

Hi [Name],

Hope you're doing well! We're ready to connect the AI Agent to Microsoft Teams for sending notifications. Could you help us set up the required workflows?

## What We Need

We need **Power Automate Workflows** configured for the Teams channels where the agent will send notifications:

| Channel | Purpose |
|---------|---------|
| Alerts | Critical alerts and system warnings |
| Reports | Daily/weekly reports and summaries |
| General | General notifications and updates |

## Why Power Automate Workflows?

Microsoft retired legacy Incoming Webhooks (Office 365 Connectors) in 2025. Power Automate Workflows is the recommended replacement, offering better security and more features.

## Setup Steps

1. Open Microsoft Teams
2. Navigate to the target channel → Click **"..."** → Select **"Workflows"**
3. Search for **"Post to a channel when a webhook request is received"**
4. Select the template → Configure the team and channel
5. Save the workflow → Copy the **HTTP POST URL**
6. **Important:** Add co-owners to ensure workflow continuity
7. Repeat for each channel

> **Note:** The workflow URL is shown after saving. Please copy it before navigating away.

## What to Send Back

Once configured, please send us:

| Item | Example |
|------|---------|
| Alerts Workflow URL | `https://prod-XX.westus.logic.azure.com:443/workflows/...` |
| Reports Workflow URL | `https://prod-XX.westus.logic.azure.com:443/workflows/...` |
| General Workflow URL | `https://prod-XX.westus.logic.azure.com:443/workflows/...` |

## Attachments

- **teams_webhook_setup_guide.pdf** - Step-by-step guide with detailed instructions
- **postman_collection.json** - Postman collection to test the integration
- **postman_environment.json** - Environment variables template

## Testing

Once we receive the workflow URLs, we'll:
1. Configure the notification service
2. Send a test message to each channel
3. Confirm everything is working

## Important Note

Some advanced configurations (such as bidirectional communication where users can chat with the agent) may require additional Microsoft services that incur monthly costs. We'll discuss these options and their associated costs before implementing any features that require them.

Let me know if you have any questions - happy to jump on a call if needed!

Thanks,
[Your Name]

---

# Alternative - Shorter Version

---

**Subject:** MS Teams Setup Request - Workflow URLs Needed

---

Hi [Name],

Quick request for the MS Teams integration.

**What we need:** Power Automate Workflow URLs for 3 channels (Alerts, Reports, General)

**How to create them:**
1. Teams channel → "..." → Workflows → "Post to a channel when a webhook request is received"
2. Configure team/channel → Save → Copy the HTTP POST URL
3. Add co-owners to each workflow
4. Repeat for each channel

**Send us back:**
- Alerts workflow URL
- Reports workflow URL
- General workflow URL

I've attached a setup guide with detailed instructions. Please add co-owners to each workflow to ensure they keep working if someone leaves the organization.

**Note:** Some advanced configurations (e.g., bidirectional chat with the agent) may require additional Microsoft services with monthly costs. We'll discuss options before implementing.

Let me know if you need help!

Thanks,
[Your Name]
