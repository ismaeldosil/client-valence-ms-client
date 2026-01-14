"""Main entry point for Valerie MS Teams Client.

Runs the Teams webhook receiver and the Dashboard/API server on a single port.
Supports dual mode: Outgoing Webhooks and/or Bot Framework.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from src.agent import AgentClient
from src.core.config import IntegrationMode, settings
from src.dashboard.api import (
    DashboardStatus,
    ServiceStatus,
    TestResult,
    check_agent_health,
    get_teams_dashboard_html,
)
from src.session import SessionStore, create_session_store
from src.teams.receiver import (
    HMACVerificationError,
    HMACVerifier,
    TeamsMessage,
    TeamsMessageHandler,
    create_verifier,
)
from src.teams.common import UnifiedMessageProcessor

if TYPE_CHECKING:
    from botbuilder.core import BotFrameworkAdapter
    from src.teams.bot_framework import ValerieBot, ProactiveMessenger

logger = structlog.get_logger(__name__)

# Global instances - Shared
_agent_client: AgentClient | None = None
_session_store: SessionStore | None = None
_unified_processor: UnifiedMessageProcessor | None = None

# Global instances - Webhook mode
_message_handler: TeamsMessageHandler | None = None
_hmac_verifier: HMACVerifier | None = None

# Global instances - Bot Framework mode
_bot_adapter: "BotFrameworkAdapter | None" = None
_bot_instance: "ValerieBot | None" = None
_proactive_messenger: "ProactiveMessenger | None" = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global _agent_client, _message_handler, _hmac_verifier, _session_store
    global _unified_processor, _bot_adapter, _bot_instance, _proactive_messenger

    integration_mode = settings.teams_integration_mode

    logger.info(
        "app_starting",
        environment=settings.environment,
        agent_url=settings.agent_base_url,
        integration_mode=integration_mode.value,
        hmac_configured=bool(settings.teams_hmac_secret),
        bot_credentials_configured=bool(settings.microsoft_app_id),
        session_store=settings.session_store,
    )

    # Initialize shared components
    _session_store = create_session_store(
        store_type=settings.session_store,
        redis_url=settings.redis_url,
        ttl_hours=settings.session_ttl_hours,
    )

    _agent_client = AgentClient(
        base_url=settings.agent_base_url,
        api_key=settings.agent_api_key,
        timeout=settings.agent_timeout,
        max_retries=settings.agent_max_retries,
    )

    _unified_processor = UnifiedMessageProcessor(
        agent_client=_agent_client,
        session_store=_session_store,
        timeout_message="The request is taking longer than expected. Please try a simpler question.",
        error_message="I'm having trouble connecting to my knowledge base. Please try again in a moment.",
    )

    # Initialize Webhook mode components
    if integration_mode in (IntegrationMode.WEBHOOK, IntegrationMode.DUAL):
        logger.info("initializing_webhook_mode")

        _message_handler = TeamsMessageHandler(
            agent_client=_agent_client,
            session_store=_session_store,
            timeout_message="The request is taking longer than expected. Teams has a 5-second limit for responses. Please try a simpler question.",
            error_message="I'm having trouble connecting to my knowledge base. Please try again in a moment.",
        )

        _hmac_verifier = create_verifier(settings.teams_hmac_secret)
        if not _hmac_verifier:
            logger.warning(
                "hmac_verification_disabled",
                reason="TEAMS_HMAC_SECRET not configured",
            )

    # Initialize Bot Framework mode components
    if integration_mode in (IntegrationMode.BOT, IntegrationMode.DUAL):
        logger.info("initializing_bot_framework_mode")

        try:
            from src.teams.bot_framework import (
                ValerieBot,
                ProactiveMessenger,
                create_bot_adapter,
            )
            from src.api.bot_api import set_bot_components

            _bot_adapter = create_bot_adapter(
                app_id=settings.microsoft_app_id,
                app_password=settings.microsoft_app_password,
                tenant_id=settings.microsoft_app_tenant_id,
            )

            _proactive_messenger = ProactiveMessenger(_bot_adapter)

            _bot_instance = ValerieBot(
                processor=_unified_processor,
                proactive_messenger=_proactive_messenger,
            )

            # Inject bot components into API module
            set_bot_components(_bot_adapter, _bot_instance)

            logger.info(
                "bot_framework_initialized",
                has_credentials=bool(settings.microsoft_app_id),
            )

        except ImportError as e:
            logger.error(
                "bot_framework_import_error",
                error=str(e),
                hint="Install botbuilder packages: pip install botbuilder-core botbuilder-schema",
            )
        except Exception as e:
            logger.error("bot_framework_init_error", error=str(e))

    yield

    # Cleanup
    if _session_store and hasattr(_session_store, 'close'):
        await _session_store.close()
    if _agent_client:
        await _agent_client.close()
    logger.info("app_stopped")


# Create main FastAPI app
app = FastAPI(
    title="Valerie MS Teams Client",
    description="MS Teams integration for Valerie AI Agent - Webhook and Bot Framework",
    version="1.0.0",
    lifespan=lifespan,
)

# Include Bot Framework router if enabled
if settings.teams_integration_mode in (IntegrationMode.BOT, IntegrationMode.DUAL):
    try:
        from src.api.bot_api import router as bot_router
        app.include_router(bot_router)
        logger.info("bot_api_router_included")
    except ImportError:
        logger.warning("bot_api_router_not_available")


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
        "integration_mode": settings.teams_integration_mode.value,
        "webhook_enabled": _message_handler is not None,
        "bot_framework_enabled": _bot_instance is not None,
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

    HMAC Verification Logic:
    - No Authorization header: Accept (validation request from Teams during webhook creation)
    - Authorization header + HMAC configured: Validate signature, reject if invalid
    - Authorization header + HMAC NOT configured: Accept with warning (setup not complete)
    """
    # Get raw body for HMAC verification
    body = await request.body()
    auth_header = request.headers.get("Authorization")

    # HMAC Verification
    if auth_header:
        # Request has Authorization header - validate if we have HMAC configured
        if _hmac_verifier:
            try:
                _hmac_verifier.verify(auth_header, body)
                logger.debug("hmac_verification_success")
            except HMACVerificationError as e:
                logger.warning("hmac_verification_failed", error=str(e))
                raise HTTPException(status_code=401, detail="Invalid signature")
        else:
            # HMAC not configured but request has auth header
            logger.warning(
                "hmac_not_configured_but_auth_header_present",
                hint="Configure TEAMS_HMAC_SECRET to validate signatures",
            )
    else:
        # No Authorization header - this is likely a validation request from Teams
        # during webhook creation, or HMAC is not being used
        logger.info(
            "webhook_request_without_auth",
            hint="Validation request or HMAC not configured on Teams side",
            body_preview=body[:100].decode("utf-8", errors="ignore") if body else "empty",
        )

    # Handle empty body (validation request)
    if not body or body == b"":
        logger.info("webhook_validation_request", message="Empty body - responding with OK")
        return JSONResponse(
            content={
                "type": "message",
                "text": "Webhook endpoint is ready.",
            }
        )

    # Parse the message
    try:
        data = await request.json()
    except Exception as e:
        # Could be a validation request with non-JSON body
        logger.warning("json_parse_error", error=str(e), body_preview=body[:200].decode("utf-8", errors="ignore"))
        return JSONResponse(
            content={
                "type": "message",
                "text": "Webhook received.",
            }
        )

    # Check if this is a minimal validation payload (Teams sometimes sends minimal data)
    if not data.get("text") and not data.get("type"):
        logger.info("webhook_minimal_payload", data=data)
        return JSONResponse(
            content={
                "type": "message",
                "text": "Webhook validated successfully.",
            }
        )

    try:
        message = TeamsMessage.from_dict(data)
    except Exception as e:
        logger.error("message_parse_error", error=str(e), data_keys=list(data.keys()) if isinstance(data, dict) else "not_dict")
        # Return a valid response instead of 400 to not break validation
        return JSONResponse(
            content={
                "type": "message",
                "text": "Message received but could not be fully processed.",
            }
        )

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

    # Get session store stats
    session_stats = {}
    if _session_store:
        try:
            session_stats = await _session_store.get_stats()
        except Exception:
            session_stats = {"type": settings.session_store, "error": "Failed to get stats"}

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
            "session_store": settings.session_store,
            "session_ttl_hours": settings.session_ttl_hours,
            "session_stats": session_stats,
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
        "session_store": settings.session_store,
        "session_ttl_hours": settings.session_ttl_hours,
    }


@app.get("/dashboard/api/sessions")
async def dashboard_sessions():
    """Get session store statistics."""
    if _session_store:
        try:
            stats = await _session_store.get_stats()
            return {
                "enabled": True,
                **stats,
            }
        except Exception as e:
            return {
                "enabled": True,
                "error": str(e),
            }
    return {
        "enabled": False,
        "type": "none",
        "active_sessions": 0,
    }


@app.get("/dashboard/api/sessions/list")
async def list_sessions():
    """List all active sessions."""
    if _session_store:
        try:
            sessions = await _session_store.list_sessions()
            return {
                "sessions": [
                    {
                        "session_id": s.session_id,
                        "user_id": s.user_id,
                        "conversation_id": s.conversation_id,
                        "created_at": s.created_at,
                        "last_activity": s.last_activity,
                        "message_count": s.message_count,
                    }
                    for s in sessions
                ],
                "total": len(sessions),
            }
        except Exception as e:
            return {"sessions": [], "total": 0, "error": str(e)}
    else:
        return {"sessions": [], "total": 0}


@app.delete("/dashboard/api/sessions")
async def clear_all_sessions():
    """Clear all sessions."""
    if _session_store:
        try:
            count = await _session_store.clear_all()
            return {"message": f"Cleared {count} sessions", "count": count}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Session store not configured"}


@app.delete("/dashboard/api/sessions/{user_id}/{conversation_id:path}")
async def delete_session(user_id: str, conversation_id: str):
    """Delete a specific session."""
    if _session_store:
        try:
            deleted = await _session_store.delete(user_id, conversation_id)
            if deleted:
                return {"message": "Session deleted"}
            else:
                return {"error": "Session not found"}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Session store not configured"}


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
# Documentation Endpoints
# ===========================================


@app.get("/docs", response_class=type(RedirectResponse))
async def docs_redirect():
    """Redirect /docs to /docs/."""
    return RedirectResponse(url="/docs/")


@app.get("/docs/")
async def docs_home():
    """Serve the documentation HTML page."""
    from pathlib import Path

    docs_path = Path(__file__).parent.parent / "docs" / "index.html"
    if docs_path.exists():
        return HTMLResponse(content=docs_path.read_text())
    else:
        return HTMLResponse(
            content="<h1>Documentation not found</h1><p>docs/index.html is missing.</p>",
            status_code=404,
        )


@app.get("/docs/common/styles.css")
async def docs_css():
    """Serve the documentation CSS."""
    from pathlib import Path
    from fastapi.responses import Response

    css_path = Path(__file__).parent.parent / "docs" / "common" / "styles.css"
    if css_path.exists():
        return Response(content=css_path.read_text(), media_type="text/css")
    else:
        return Response(content="", status_code=404)


@app.get("/docs/webhook-status")
async def docs_webhook_status():
    """Serve the webhook status report."""
    from pathlib import Path

    docs_path = Path(__file__).parent.parent / "docs" / "webhook-status-report.html"
    if docs_path.exists():
        return HTMLResponse(content=docs_path.read_text())
    else:
        return HTMLResponse(
            content="<h1>Report not found</h1><p>docs/webhook-status-report.html is missing.</p>",
            status_code=404,
        )


# ===========================================
# Main Entry Point
# ===========================================


def main():
    """Run the application."""
    # Railway injects PORT env var - use it if available
    port = int(os.environ.get("PORT", settings.receiver_port))
    mode = settings.teams_integration_mode.value

    print()
    print("=" * 60)
    print("  Valerie MS Teams Client")
    print("=" * 60)
    print(f"  Environment:      {settings.environment}")
    print(f"  Integration Mode: {mode}")
    print(f"  Agent URL:        {settings.agent_base_url}")
    print(f"  Port:             {port}")
    print()
    print("  Endpoints:")
    if mode in ("webhook", "dual"):
        print(f"    Webhook:    http://0.0.0.0:{port}/webhook")
    if mode in ("bot", "dual"):
        print(f"    Bot API:    http://0.0.0.0:{port}/api/messages")
    print(f"    Dashboard:  http://0.0.0.0:{port}/dashboard")
    print(f"    Health:     http://0.0.0.0:{port}/health")
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
