# Discovery: Bot Framework Integration for MS Teams

**Ticket:** TC-002
**Type:** Discovery
**Status:** Complete
**Date:** 2026-01-14

---

## Summary

This discovery explored the feasibility of integrating Microsoft Bot Framework as an alternative communication channel for the MS Teams client, addressing limitations inherent to the Outgoing Webhooks approach.

---

## Background

The existing MS Teams integration relies on **Outgoing Webhooks**, a lightweight mechanism that forwards messages to an external endpoint when the bot is @mentioned. While simple to set up, this approach has fundamental constraints rooted in its design as a one-way notification system rather than a conversational interface.

---

## Key Findings

### Outgoing Webhooks Limitations

| Constraint | Impact |
|------------|--------|
| **@mention required** | Users must explicitly mention the bot in every message, even within ongoing threads |
| **5-second timeout** | Complex queries risk timeout failures; no async processing possible |
| **No proactive messaging** | Bot cannot initiate conversations or send follow-up messages |
| **Limited card support** | Adaptive Cards support only `OpenURL` actions, no form submissions |

### Bot Framework Capabilities

The Bot Framework operates on a fundamentally different model—it establishes a **bidirectional channel** between Teams and the bot service, enabling:

- **Automatic thread participation**: Once in a conversation, the bot receives all messages without requiring @mention
- **Proactive messaging**: Ability to send messages initiated by the bot (alerts, reminders, notifications)
- **Rich interactions**: Full Adaptive Card support including form submissions and button actions
- **No timeout constraints**: Long-running operations can complete without risk of connection termination

---

## Architecture Decision

Rather than replacing the existing webhook integration, a **dual-mode architecture** was designed:

```
┌─────────────────────────────────────────────────┐
│              Integration Mode                    │
│    "webhook"  |  "bot"  |  "dual"               │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   [Webhooks]    [Bot Framework]  [Both]
        │             │             │
        └─────────────┴─────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  Unified Processor     │
         │  (shared logic)        │
         └────────────────────────┘
```

This approach allows:
- Gradual migration without disrupting existing deployments
- Flexibility to choose the appropriate mode per environment
- Code reuse through a unified message processing layer

---

## Azure Configuration Insights

### Authentication Model

Azure Bot Service supports three authentication modes:

| Mode | Use Case |
|------|----------|
| **Single Tenant** | Bot restricted to one Azure AD tenant |
| **Multi-Tenant** | Bot accessible from any Azure AD tenant |
| **Managed Identity** | Azure-managed credentials (advanced scenarios) |

**Finding:** Multi-Tenant is required when the Azure subscription and Teams tenant are in different organizations.

### Critical Configuration Points

1. **Client Secret vs Secret ID**: Azure displays both; only the **Value** (not the GUID identifier) works as the password
2. **Whitespace sensitivity**: Environment variables with trailing spaces cause authentication failures
3. **API Permissions**: `User.Read` delegated permission required for basic bot functionality

---

## Deployment Considerations

The Bot Framework requires:
- HTTPS endpoint with valid SSL certificate
- Public accessibility (no localhost/internal URLs)
- Proper CORS headers for browser-based testing

Cloud platforms like Railway provide these out-of-the-box, making deployment straightforward.

---

## Teams Admin Constraints

**Discovery finding:** Installing custom bots in Microsoft Teams requires either:
- Admin consent in the target tenant
- Sideloading permissions enabled
- Microsoft 365 Developer Program tenant (for testing)

Teams Free accounts cannot install custom bots due to platform restrictions.

---

## Conclusion

Bot Framework integration is viable and provides significant advantages over Outgoing Webhooks for conversational scenarios. The dual-mode architecture enables incremental adoption while maintaining backward compatibility.

---

## References

- [Bot Framework Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Teams Platform: Bots](https://docs.microsoft.com/en-us/microsoftteams/platform/bots/)
- [Azure AD App Registration](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
