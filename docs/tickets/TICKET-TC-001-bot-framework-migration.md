# TICKET-TC-001: Migrate from Outgoing Webhooks to Bot Framework

**Status:** Todo | **Priority:** P3 | **Effort:** XL | **Agent:** @backend

## Description

The current MS Teams integration uses **Outgoing Webhooks**, which have significant limitations compared to the Bot Framework. This ticket tracks the migration to Bot Framework for full conversational capabilities.

## Current Architecture Limitations

### Outgoing Webhooks
- Only triggered by explicit @mentions
- Cannot receive thread replies automatically (user must @mention bot each time)
- Cannot send proactive messages
- Cannot access message history
- Limited to simple request/response pattern
- No support for cards with interactive buttons

### Bot Framework Benefits
- Receives all messages in conversations where bot is a member
- Full thread reply handling (similar to Slack)
- Proactive messaging capabilities
- Rich interactive Adaptive Cards with buttons
- Access to Microsoft Graph API for extended functionality
- Better session management with Activity IDs

## Implementation Plan

### 1. Register Bot in Azure
```
- Create Azure Bot resource
- Configure messaging endpoint
- Set up authentication (App ID and Secret)
```

### 2. Update Client Architecture
```python
# New architecture using Bot Framework SDK
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity

class ValerieBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        # Access full conversation context
        conversation_id = turn_context.activity.conversation.id
        reply_to_id = turn_context.activity.reply_to_id
        thread_ts = turn_context.activity.conversation.thread_ts

        # Handle both direct messages and thread replies
        ...
```

### 3. Enable Proactive Messaging
```python
# Store conversation references for proactive messaging
async def send_proactive_message(conversation_reference, message):
    await adapter.continue_conversation(
        conversation_reference,
        lambda ctx: ctx.send_activity(message)
    )
```

### 4. Deploy to Azure App Service
- Configure App Service for Bot Framework
- Update environment variables
- Set up health checks

## Acceptance Criteria

- [ ] Bot registered in Azure
- [ ] Bot Framework SDK integrated
- [ ] Thread replies handled without @mentions
- [ ] Proactive messaging working
- [ ] Interactive Adaptive Cards with buttons
- [ ] Session management with thread awareness
- [ ] All existing functionality preserved

## Workaround (Current)

The following improvements have been made to work within Outgoing Webhook limitations:

1. **Thread-aware session keys** (implemented)
   - Parse `replyToId` from webhook payload
   - Include in session key for thread context
   - File: `src/teams/receiver/models.py`

2. **User guidance**
   - Users must @mention the bot in every message
   - Thread context is maintained when users reply in the same thread and @mention

## Dependencies

- Azure subscription with Bot Service capability
- Bot Framework SDK (`botbuilder-core`, `botbuilder-integration-aiohttp`)

## Estimated Effort

| Task | Hours |
|------|-------|
| Azure Bot registration | 2 |
| Bot Framework SDK integration | 8 |
| Proactive messaging | 4 |
| Interactive cards | 6 |
| Testing and deployment | 4 |
| Documentation | 2 |
| **Total** | **26** |

## References

- [Bot Framework Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Teams Bot Development](https://docs.microsoft.com/en-us/microsoftteams/platform/bots/what-are-bots)
- [Outgoing Webhooks vs Bots](https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-outgoing-webhook)
