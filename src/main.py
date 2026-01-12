"""Main entry point for Valerie MS Teams Client.

Runs the Teams webhook receiver and the Dashboard/API server on a single port.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from src.agent import AgentClient
from src.core.config import settings
from src.dashboard.api import (
    DashboardStatus,
    ServiceStatus,
    TestResult,
    check_agent_health,
    get_teams_dashboard_html,
)
from src.teams.receiver import (
    HMACVerificationError,
    HMACVerifier,
    TeamsMessage,
    TeamsMessageHandler,
    create_verifier,
)

logger = structlog.get_logger(__name__)

# Global instances
_agent_client: AgentClient | None = None
_message_handler: TeamsMessageHandler | None = None
_hmac_verifier: HMACVerifier | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global _agent_client, _message_handler, _hmac_verifier

    logger.info(
        "app_starting",
        environment=settings.environment,
        agent_url=settings.agent_base_url,
        hmac_configured=bool(settings.teams_hmac_secret),
    )

    # Initialize agent client
    _agent_client = AgentClient(
        base_url=settings.agent_base_url,
        api_key=settings.agent_api_key,
        timeout=settings.agent_timeout,
        max_retries=settings.agent_max_retries,
    )

    # Initialize message handler
    _message_handler = TeamsMessageHandler(
        agent_client=_agent_client,
        timeout_message="The request is taking longer than expected. Teams has a 5-second limit for responses. Please try a simpler question.",
        error_message="I'm having trouble connecting to my knowledge base. Please try again in a moment.",
    )

    # Initialize HMAC verifier (optional)
    _hmac_verifier = create_verifier(settings.teams_hmac_secret)
    if not _hmac_verifier:
        logger.warning(
            "hmac_verification_disabled",
            reason="TEAMS_HMAC_SECRET not configured",
        )

    yield

    # Cleanup
    if _agent_client:
        await _agent_client.close()
    logger.info("app_stopped")


# Create main FastAPI app
app = FastAPI(
    title="Valerie MS Teams Client",
    description="MS Teams integration for Valerie AI Agent",
    version="1.0.0",
    lifespan=lifespan,
)


# ===========================================
# Health & Root Endpoints
# ===========================================


@app.get("/")
async def root():
    """Root endpoint - redirect to dashboard."""
    return RedirectResponse(url="/dashboard")


@app.get("/health")
async def health():
    """Health check endpoint for Railway."""
    agent_status = "unknown"
    agent_version = "unknown"

    if _agent_client:
        try:
            health_data = await _agent_client.health_check()
            agent_status = health_data.get("status", "unknown")
            agent_version = health_data.get("version", "unknown")
        except Exception as e:
            agent_status = f"error: {str(e)[:50]}"

    return {
        "status": "healthy",
        "service": "valerie-teams-client",
        "version": "1.0.0",
        "environment": settings.environment,
        "hmac_enabled": _hmac_verifier is not None,
        "agent": {
            "url": settings.agent_base_url,
            "status": agent_status,
            "version": agent_version,
        },
    }


# ===========================================
# Teams Webhook Endpoints
# ===========================================


@app.get("/webhook")
async def webhook_get():
    """GET endpoint for Teams URL validation."""
    return {"status": "ok", "message": "Webhook ready"}


@app.post("/webhook")
async def webhook_handler(request: Request) -> JSONResponse:
    """Handle incoming Teams Outgoing Webhook messages.

    This endpoint receives messages when users @mention the bot in Teams.
    """
    # Get raw body for HMAC verification
    body = await request.body()

    # Verify HMAC signature if configured
    if _hmac_verifier:
        auth_header = request.headers.get("Authorization")
        try:
            _hmac_verifier.verify(auth_header, body)
        except HMACVerificationError as e:
            logger.warning("hmac_verification_failed", error=str(e))
            raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse the message
    try:
        data = await request.json()
        message = TeamsMessage.from_dict(data)
    except Exception as e:
        logger.error("message_parse_error", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid message format")

    log = logger.bind(
        message_id=message.id,
        user_name=message.from_user.name,
        conversation_id=message.conversation.id,
        clean_text=message.get_clean_text()[:50],
    )

    log.info("webhook_received")

    # Process the message
    if not _message_handler:
        log.error("handler_not_initialized")
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        response = await _message_handler.handle(message)
        log.info("webhook_response_sent")
        return JSONResponse(content=response.to_dict())

    except Exception as e:
        log.error("handler_error", error=str(e))
        return JSONResponse(
            content={
                "type": "message",
                "text": "An unexpected error occurred. Please try again.",
            }
        )


# ===========================================
# Dashboard Endpoints
# ===========================================


@app.get("/dashboard", response_class=type(RedirectResponse))
async def dashboard_redirect():
    """Redirect /dashboard to /dashboard/."""
    return RedirectResponse(url="/dashboard/")


@app.get("/dashboard/")
async def dashboard_home():
    """Serve the dashboard HTML page."""
    return HTMLResponse(content=get_teams_dashboard_html())


@app.get("/dashboard/api/status", response_model=DashboardStatus)
async def dashboard_status():
    """Get complete status of Teams client and agent."""
    agent_status = await check_agent_health()

    client_status = ServiceStatus(
        name="MS Teams Client",
        status="healthy",
        url=f"localhost:{os.environ.get('PORT', settings.receiver_port)}",
        last_check=datetime.now(UTC).isoformat(),
        details={
            "environment": settings.environment,
            "hmac_secret_configured": bool(settings.teams_hmac_secret),
            "workflow_alerts_configured": bool(settings.teams_workflow_alerts),
            "workflow_reports_configured": bool(settings.teams_workflow_reports),
        },
    )

    return DashboardStatus(
        timestamp=datetime.now(UTC).isoformat(),
        client=client_status,
        agent=agent_status,
    )


@app.get("/dashboard/api/health")
async def dashboard_health():
    """Dashboard health check."""
    return {"status": "healthy", "service": "teams-client-dashboard"}


@app.post("/dashboard/api/test/agent", response_model=TestResult)
async def dashboard_test_agent(message: str = "Hello, test from Teams dashboard"):
    """Test the Valerie Agent with a message."""
    import httpx

    start = datetime.now(UTC)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.agent_base_url}/api/v1/chat",
                json={
                    "message": message,
                    "session_id": "teams-dashboard-test",
                    "user_id": "dashboard",
                    "platform": "teams",
                },
            )
            elapsed = (datetime.now(UTC) - start).total_seconds() * 1000

            if response.status_code == 200:
                data = response.json()
                return TestResult(
                    success=True,
                    message=data.get("message", "Response received"),
                    response_time_ms=round(elapsed, 2),
                    details=data,
                )
            else:
                return TestResult(
                    success=False,
                    message=f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time_ms=round(elapsed, 2),
                )
    except Exception as e:
        return TestResult(
            success=False,
            message=str(e),
        )


@app.get("/dashboard/api/config")
async def dashboard_config():
    """Get current configuration (non-sensitive)."""
    return {
        "environment": settings.environment,
        "agent_url": settings.agent_base_url,
        "hmac_configured": bool(settings.teams_hmac_secret),
        "workflow_alerts_configured": bool(settings.teams_workflow_alerts),
        "workflow_reports_configured": bool(settings.teams_workflow_reports),
    }


@app.post("/dashboard/api/test/webhook", response_model=TestResult)
async def dashboard_test_webhook(message: str = "Hello from dashboard webhook test"):
    """Test the webhook endpoint by simulating a Teams message."""
    import uuid

    start = datetime.now(UTC)

    # Create a simulated Teams message payload
    test_payload = {
        "type": "message",
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "localTimestamp": datetime.now(UTC).isoformat(),
        "serviceUrl": "https://smba.trafficmanager.net/amer/",
        "channelId": "msteams",
        "from": {
            "id": "dashboard-test-user",
            "name": "Dashboard Test User",
            "aadObjectId": str(uuid.uuid4()),
        },
        "conversation": {
            "id": f"test-conversation-{uuid.uuid4()}",
            "conversationType": "channel",
            "tenantId": str(uuid.uuid4()),
        },
        "recipient": {
            "id": "bot-id",
            "name": "Valerie Bot",
        },
        "text": f"<at>Valerie</at> {message}",
        "textFormat": "plain",
        "channelData": {
            "teamsChannelId": "test-channel",
            "teamsTeamId": "test-team",
        },
    }

    try:
        # Process through the message handler (bypassing HMAC)
        if not _message_handler:
            return TestResult(
                success=False,
                message="Message handler not initialized",
            )

        teams_message = TeamsMessage.from_dict(test_payload)
        response = await _message_handler.handle(teams_message)
        elapsed = (datetime.now(UTC) - start).total_seconds() * 1000

        return TestResult(
            success=True,
            message=response.text if hasattr(response, 'text') else str(response.to_dict()),
            response_time_ms=round(elapsed, 2),
            details=response.to_dict(),
        )

    except Exception as e:
        elapsed = (datetime.now(UTC) - start).total_seconds() * 1000
        return TestResult(
            success=False,
            message=str(e),
            response_time_ms=round(elapsed, 2),
        )


@app.post("/dashboard/api/test/workflow/{workflow_type}", response_model=TestResult)
async def dashboard_test_workflow(
    workflow_type: str,
    message: str = "Test message from dashboard",
    title: str = "Dashboard Test",
):
    """Test sending a message through a workflow (alerts, reports, general)."""
    import httpx

    start = datetime.now(UTC)

    # Get the workflow URL based on type
    workflow_urls = {
        "alerts": settings.teams_workflow_alerts,
        "reports": settings.teams_workflow_reports,
        "general": settings.teams_workflow_general,
    }

    workflow_url = workflow_urls.get(workflow_type)
    if not workflow_url:
        return TestResult(
            success=False,
            message=f"Workflow '{workflow_type}' not configured. Available: {list(workflow_urls.keys())}",
        )

    # Build the payload for Power Automate
    payload = {
        "title": title,
        "message": message,
        "timestamp": datetime.now(UTC).isoformat(),
        "source": "dashboard-test",
        "priority": "medium",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                workflow_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            elapsed = (datetime.now(UTC) - start).total_seconds() * 1000

            if response.status_code in (200, 202):
                return TestResult(
                    success=True,
                    message=f"Message sent to {workflow_type} workflow",
                    response_time_ms=round(elapsed, 2),
                    details={
                        "workflow": workflow_type,
                        "status_code": response.status_code,
                        "response": response.text[:200] if response.text else "OK",
                    },
                )
            else:
                return TestResult(
                    success=False,
                    message=f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time_ms=round(elapsed, 2),
                )

    except Exception as e:
        elapsed = (datetime.now(UTC) - start).total_seconds() * 1000
        return TestResult(
            success=False,
            message=str(e),
            response_time_ms=round(elapsed, 2),
        )


# ===========================================
# Main Entry Point
# ===========================================


def main():
    """Run the application."""
    # Railway injects PORT env var - use it if available
    port = int(os.environ.get("PORT", settings.receiver_port))

    print()
    print("=" * 60)
    print("  Valerie MS Teams Client")
    print("=" * 60)
    print(f"  Environment: {settings.environment}")
    print(f"  Agent URL:   {settings.agent_base_url}")
    print(f"  Port:        {port}")
    print(f"  Webhook:     http://0.0.0.0:{port}/webhook")
    print(f"  Dashboard:   http://0.0.0.0:{port}/dashboard")
    print(f"  Health:      http://0.0.0.0:{port}/health")
    print("=" * 60)
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
