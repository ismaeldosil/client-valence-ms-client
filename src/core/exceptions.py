"""
Custom exceptions for the project.

Exception hierarchy:
    TeamsAgentError (base)
    ├── AgentError
    │   ├── AgentTimeoutError
    │   └── AgentConnectionError
    └── TeamsError
        └── WebhookVerificationError
"""


class TeamsAgentError(Exception):
    """Base exception for all project errors."""

    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


class AgentError(TeamsAgentError):
    """Error related to AI Agent."""

    pass


class AgentTimeoutError(AgentError):
    """Agent did not respond in time."""

    def __init__(self, message: str = "Agent request timed out"):
        super().__init__(message)


class AgentConnectionError(AgentError):
    """Cannot connect to agent."""

    def __init__(self, message: str = "Cannot connect to agent"):
        super().__init__(message)


class TeamsError(TeamsAgentError):
    """Error related to Microsoft Teams."""

    pass


class WebhookVerificationError(TeamsError):
    """HMAC verification failed for webhook."""

    def __init__(self, message: str = "Webhook signature verification failed"):
        super().__init__(message)
