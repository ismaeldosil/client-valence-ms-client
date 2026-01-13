"""Dashboard API for MS Teams Client status and testing.

Provides a web interface to check health, status, and test the MS Teams client functionality.
"""

from datetime import UTC, datetime

import httpx
import structlog
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.core.config import settings

logger = structlog.get_logger(__name__)


# ===========================================
# Models
# ===========================================


class ServiceStatus(BaseModel):
    """Status of a service."""

    name: str
    status: str  # "healthy", "degraded", "offline"
    url: str
    response_time_ms: float | None = None
    last_check: str
    details: dict | None = None
    error: str | None = None


class DashboardStatus(BaseModel):
    """Complete dashboard status response."""

    timestamp: str
    client: ServiceStatus
    agent: ServiceStatus


class TestResult(BaseModel):
    """Result of a test execution."""

    success: bool
    message: str
    response_time_ms: float | None = None
    details: dict | None = None


# ===========================================
# Health Check Functions
# ===========================================


async def check_agent_health() -> ServiceStatus:
    """Check Valerie Agent health."""
    start = datetime.now(UTC)
    agent_url = settings.agent_base_url

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{agent_url}/health")
            elapsed = (datetime.now(UTC) - start).total_seconds() * 1000

            if response.status_code == 200:
                data = response.json()
                return ServiceStatus(
                    name="Valerie Agent",
                    status="healthy",
                    url=agent_url,
                    response_time_ms=round(elapsed, 2),
                    last_check=start.isoformat(),
                    details=data,
                )
            else:
                return ServiceStatus(
                    name="Valerie Agent",
                    status="degraded",
                    url=agent_url,
                    response_time_ms=round(elapsed, 2),
                    last_check=start.isoformat(),
                    error=f"HTTP {response.status_code}",
                )
    except Exception as e:
        return ServiceStatus(
            name="Valerie Agent",
            status="offline",
            url=agent_url,
            last_check=start.isoformat(),
            error=str(e),
        )


def get_client_status() -> ServiceStatus:
    """Get current MS Teams client status."""
    return ServiceStatus(
        name="MS Teams Client",
        status="healthy",
        url=f"localhost:{settings.receiver_port}",
        last_check=datetime.now(UTC).isoformat(),
        details={
            "environment": settings.environment,
            "receiver_port": settings.receiver_port,
            "notifier_port": settings.notifier_port,
            "hmac_secret_configured": bool(settings.teams_hmac_secret),
            "workflow_alerts_configured": bool(settings.teams_workflow_alerts),
            "workflow_reports_configured": bool(settings.teams_workflow_reports),
        },
    )


# ===========================================
# Test Functions
# ===========================================


async def test_agent_chat(message: str) -> TestResult:
    """Test sending a chat message to the agent."""
    start = datetime.now(UTC)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.agent_base_url}/chat",
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


# ===========================================
# Dashboard App Factory
# ===========================================


def create_dashboard_app() -> FastAPI:
    """Create the dashboard FastAPI application."""
    app = FastAPI(
        title="Valerie MS Teams Client Dashboard",
        description="Monitor and test the MS Teams client for Valerie AI Agent",
        version="1.0.0",
    )

    # ===========================================
    # API Endpoints
    # ===========================================

    @app.get("/", response_class=HTMLResponse)
    async def dashboard_home():
        """Serve the dashboard HTML page."""
        return HTMLResponse(content=get_teams_dashboard_html())

    @app.get("/api/status", response_model=DashboardStatus)
    async def get_status():
        """Get complete status of MS Teams client and agent."""
        agent_status = await check_agent_health()
        client_status = get_client_status()

        return DashboardStatus(
            timestamp=datetime.now(UTC).isoformat(),
            client=client_status,
            agent=agent_status,
        )

    @app.get("/api/health")
    async def health():
        """Simple health check for the dashboard itself."""
        return {"status": "healthy", "service": "teams-client-dashboard"}

    @app.post("/api/test/agent", response_model=TestResult)
    async def test_agent(message: str = "Hello, test from Teams dashboard"):
        """Test the Valerie Agent with a message."""
        return await test_agent_chat(message)

    @app.get("/api/config")
    async def get_config():
        """Get current configuration (non-sensitive)."""
        return {
            "environment": settings.environment,
            "agent_url": settings.agent_base_url,
            "receiver_port": settings.receiver_port,
            "notifier_port": settings.notifier_port,
            "hmac_configured": bool(settings.teams_hmac_secret),
        }

    return app


def get_teams_dashboard_html() -> str:
    """Return embedded HTML for the MS Teams client dashboard."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Valerie MS Teams Client - Dashboard</title>
    <style>
        :root {
            --bg-primary: #1b1a19;
            --bg-secondary: #252423;
            --bg-card: #323130;
            --text-primary: #f3f2f1;
            --text-secondary: #a19f9d;
            --teams-purple: #6264a7;
            --teams-green: #6bb700;
            --teams-yellow: #ffb900;
            --teams-red: #c50f1f;
            --teams-blue: #0078d4;
            --border-color: #484644;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, var(--teams-purple) 0%, #464775 100%);
            border-radius: 12px;
        }

        .logo {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin-bottom: 10px;
        }

        .logo svg {
            width: 40px;
            height: 40px;
        }

        h1 {
            font-size: 1.8rem;
            font-weight: 600;
        }

        .subtitle {
            color: rgba(255,255,255,0.85);
            font-size: 0.95rem;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }

        .card {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 20px;
            border: 1px solid var(--border-color);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border-color);
        }

        .card-title {
            font-size: 1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .card-icon {
            width: 20px;
            height: 20px;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
        }

        .status-healthy { background: var(--teams-green); box-shadow: 0 0 8px var(--teams-green); }
        .status-degraded { background: var(--teams-yellow); box-shadow: 0 0 8px var(--teams-yellow); }
        .status-offline { background: var(--teams-red); box-shadow: 0 0 8px var(--teams-red); }
        .status-checking { background: var(--teams-blue); animation: pulse 1s infinite; }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .status-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 4px;
            background: var(--bg-card);
        }

        .metric {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            font-size: 0.9rem;
        }

        .metric-label { color: var(--text-secondary); }
        .metric-value { font-weight: 500; }

        .config-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 0;
            font-size: 0.85rem;
        }

        .config-check { color: var(--teams-green); }
        .config-x { color: var(--teams-red); }

        .section {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 20px;
            border: 1px solid var(--border-color);
            margin-bottom: 20px;
        }

        .section h2 {
            margin-bottom: 15px;
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .controls {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }

        .input-field {
            flex: 1;
            min-width: 200px;
            padding: 10px 12px;
            border-radius: 4px;
            border: 1px solid var(--border-color);
            background: var(--bg-card);
            color: var(--text-primary);
            font-size: 0.9rem;
        }

        .input-field:focus {
            outline: none;
            border-color: var(--teams-blue);
        }

        textarea.input-field {
            resize: vertical;
            min-height: 60px;
        }

        .tabs {
            display: flex;
            gap: 5px;
            margin-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
        }

        .tab {
            padding: 8px 16px;
            border-radius: 4px 4px 0 0;
            border: none;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
            background: transparent;
            color: var(--text-secondary);
            transition: all 0.2s;
        }

        .tab:hover {
            color: var(--text-primary);
            background: var(--bg-card);
        }

        .tab.active {
            background: var(--teams-purple);
            color: white;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .events-container {
            background: var(--bg-card);
            border-radius: 4px;
            overflow: hidden;
            max-height: 400px;
            overflow-y: auto;
        }

        .events-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .events-count {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .event-item {
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
            transition: background 0.2s;
        }

        .event-item:hover {
            background: rgba(255,255,255,0.03);
        }

        .event-item:last-child {
            border-bottom: none;
        }

        .event-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }

        .event-type {
            font-size: 0.7rem;
            text-transform: uppercase;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 3px;
            background: var(--teams-purple);
        }

        .event-type.webhook { background: var(--teams-blue); }
        .event-type.workflow { background: var(--teams-green); }
        .event-type.session { background: #0078d4; }

        .event-time {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        .event-user {
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 4px;
        }

        .event-text {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }

        .event-meta {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        .no-events {
            text-align: center;
            padding: 30px;
            color: var(--text-secondary);
        }

        .btn-sm {
            padding: 6px 12px;
            font-size: 0.8rem;
        }

        .btn-danger {
            background: var(--teams-red);
            color: white;
        }

        .btn-danger:hover { background: #a50d1a; }

        .btn {
            padding: 10px 18px;
            border-radius: 4px;
            border: none;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.2s;
        }

        .btn-primary {
            background: var(--teams-purple);
            color: white;
        }

        .btn-primary:hover { background: #5558a0; }

        .btn-secondary {
            background: var(--bg-card);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover { background: var(--border-color); }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .log {
            background: var(--bg-card);
            border-radius: 4px;
            padding: 12px;
            max-height: 250px;
            overflow-y: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.8rem;
        }

        .log-entry {
            padding: 4px 0;
            border-bottom: 1px solid var(--border-color);
        }

        .log-entry:last-child { border-bottom: none; }

        .log-time {
            color: var(--text-secondary);
            margin-right: 8px;
        }

        .log-success { color: var(--teams-green); }
        .log-error { color: var(--teams-red); }
        .log-info { color: var(--teams-blue); }

        .refresh-float {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px;
            border-radius: 50%;
            background: var(--teams-purple);
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            transition: transform 0.2s;
        }

        .refresh-float:hover { transform: scale(1.1); }

        .refresh-float svg {
            width: 22px;
            height: 22px;
            fill: white;
        }

        .spinning { animation: spin 1s linear infinite; }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        footer {
            text-align: center;
            margin-top: 25px;
            padding-top: 15px;
            border-top: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-size: 0.85rem;
        }

        footer a {
            color: var(--teams-blue);
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">
                <svg viewBox="0 0 24 24" fill="white">
                    <path d="M19.2 6.4H16V3.2c0-.88-.72-1.6-1.6-1.6h-4.8c-.88 0-1.6.72-1.6 1.6v3.2H4.8c-.88 0-1.6.72-1.6 1.6v12.8c0 .88.72 1.6 1.6 1.6h14.4c.88 0 1.6-.72 1.6-1.6V8c0-.88-.72-1.6-1.6-1.6zM9.6 3.2h4.8v3.2H9.6V3.2zm9.6 17.6H4.8V8h14.4v12.8z"/>
                    <circle cx="12" cy="12" r="2.5"/>
                    <path d="M12 16.5c-2.33 0-4.5 1.17-4.5 2.5h9c0-1.33-2.17-2.5-4.5-2.5z"/>
                </svg>
                <h1>Valerie MS Teams Client</h1>
            </div>
            <p class="subtitle">Monitor and test your Microsoft Teams integration</p>
        </header>

        <div class="grid">
            <!-- Client Status -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">
                        <svg class="card-icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                        </svg>
                        Teams Client
                    </span>
                    <span class="status-label">
                        <span class="status-dot status-checking" id="client-dot"></span>
                        <span id="client-status">Checking</span>
                    </span>
                </div>
                <div class="config-item">
                    <span id="hmac-check" class="config-x">&#10007;</span>
                    HMAC Secret (Webhooks)
                </div>
                <div class="config-item">
                    <span id="alerts-check" class="config-x">&#10007;</span>
                    Alerts Workflow
                </div>
                <div class="config-item">
                    <span id="reports-check" class="config-x">&#10007;</span>
                    Reports Workflow
                </div>
                <div class="metric">
                    <span class="metric-label">Receiver Port</span>
                    <span class="metric-value" id="client-receiver">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Environment</span>
                    <span class="metric-value" id="client-env">-</span>
                </div>
            </div>

            <!-- Sessions Status -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">
                        <svg class="card-icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                        </svg>
                        Sessions
                    </span>
                    <span class="status-label">
                        <span class="status-dot" id="session-dot"></span>
                        <span id="session-status">-</span>
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-label">Store Type</span>
                    <span class="metric-value" id="session-type">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Active Sessions</span>
                    <span class="metric-value" id="session-count">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">TTL</span>
                    <span class="metric-value" id="session-ttl">-</span>
                </div>
            </div>

            <!-- Agent Status -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">
                        <svg class="card-icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M21 10.12h-6.78l2.74-2.82c-2.73-2.7-7.15-2.8-9.88-.1-2.73 2.71-2.73 7.08 0 9.79s7.15 2.71 9.88 0C18.32 15.65 19 14.08 19 12.1h2c0 1.98-.88 4.55-2.64 6.29-3.51 3.48-9.21 3.48-12.72 0-3.5-3.47-3.53-9.11-.02-12.58s9.14-3.47 12.65 0L21 3v7.12z"/>
                        </svg>
                        Valerie Agent
                    </span>
                    <span class="status-label">
                        <span class="status-dot status-checking" id="agent-dot"></span>
                        <span id="agent-status">Checking</span>
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-label">URL</span>
                    <span class="metric-value" id="agent-url">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Response Time</span>
                    <span class="metric-value" id="agent-response">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Version</span>
                    <span class="metric-value" id="agent-version">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Check</span>
                    <span class="metric-value" id="agent-lastcheck">-</span>
                </div>
            </div>
        </div>

        <!-- Tabs Section -->
        <div class="section">
            <div class="tabs">
                <button class="tab active" onclick="switchTab('sessions')">Sessions</button>
                <button class="tab" onclick="switchTab('test')">Test Agent</button>
                <button class="tab" onclick="switchTab('workflows')">Workflows</button>
                <button class="tab" onclick="switchTab('endpoints')">Endpoints</button>
            </div>

            <!-- Sessions Tab -->
            <div id="tab-sessions" class="tab-content active">
                <div class="events-header">
                    <span class="events-count"><span id="sessions-total">0</span> active sessions</span>
                    <div>
                        <button class="btn btn-sm btn-secondary" onclick="refreshSessions()">Refresh</button>
                        <button class="btn btn-sm btn-danger" onclick="clearAllSessions()">Clear All</button>
                    </div>
                </div>
                <div class="events-container" id="sessions-list">
                    <div class="no-events">No active sessions. Sessions will appear here when users interact with the bot.</div>
                </div>
            </div>

            <!-- Test Agent Tab -->
            <div id="tab-test" class="tab-content">
                <div class="controls">
                    <input type="text" class="input-field" id="test-message"
                           placeholder="Enter test message..."
                           value="Hello, this is a test from Teams dashboard">
                </div>
                <div class="controls">
                    <button class="btn btn-primary" onclick="testAgent()">Test Agent (Direct)</button>
                    <button class="btn btn-primary" onclick="testWebhook()" style="background: #0078d4;">Test Webhook</button>
                    <button class="btn btn-secondary" onclick="refreshStatus()">Refresh Status</button>
                </div>
                <div class="log" id="log">
                    <div class="log-entry log-info">
                        <span class="log-time">[--:--:--]</span>
                        Dashboard initialized. Click "Refresh Status" to check connections.
                    </div>
                </div>
            </div>

            <!-- Workflows Tab -->
            <div id="tab-workflows" class="tab-content">
                <div class="controls">
                    <input type="text" class="input-field" id="workflow-title"
                           placeholder="Message title..."
                           value="Dashboard Test">
                </div>
                <div class="controls">
                    <textarea class="input-field" id="workflow-message" placeholder="Enter message to send..." rows="3">Hello, this is a test message from the Teams dashboard.</textarea>
                </div>
                <div class="controls">
                    <button class="btn btn-danger" onclick="testWorkflow('alerts')">Send to Alerts</button>
                    <button class="btn btn-primary" onclick="testWorkflow('reports')" style="background: #0078d4;">Send to Reports</button>
                    <button class="btn btn-primary" onclick="testWorkflow('general')">Send to General</button>
                </div>
                <div class="log" id="workflow-log">
                    <div class="log-entry log-info">
                        <span class="log-time">[--:--:--]</span>
                        Select a workflow and enter a message to send.
                    </div>
                </div>
            </div>

            <!-- Endpoints Tab -->
            <div id="tab-endpoints" class="tab-content">
                <h3 style="margin-bottom: 15px; font-size: 1rem;">Test API Endpoints</h3>
                <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                    <button class="btn btn-secondary" onclick="testEndpoint('/health')">GET /health</button>
                    <button class="btn btn-secondary" onclick="testEndpoint('/dashboard/api/status')">GET /api/status</button>
                    <button class="btn btn-secondary" onclick="testEndpoint('/dashboard/api/config')">GET /api/config</button>
                    <button class="btn btn-secondary" onclick="testEndpoint('/dashboard/api/sessions')">GET /api/sessions</button>
                    <button class="btn btn-secondary" onclick="testEndpoint('/dashboard/api/sessions/list')">GET /api/sessions/list</button>
                </div>
                <div class="log" id="endpoint-log" style="margin-top: 15px;">
                    <div class="log-entry log-info">
                        <span class="log-time">[--:--:--]</span>
                        Click an endpoint button to test it.
                    </div>
                </div>
            </div>
        </div>

        <footer>
            <p>Valerie AI Agent - MS Teams Integration | <a href="https://github.com/REEA-Global-LLC">REEA Global</a></p>
        </footer>
    </div>

    <button class="refresh-float" onclick="refreshStatus()" title="Refresh Status">
        <svg id="refresh-icon" viewBox="0 0 24 24">
            <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
        </svg>
    </button>

    <script>
        // Tab switching
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.add('active');

            if (tabName === 'sessions') refreshSessions();
        }

        function log(message, type = 'info', logId = 'log') {
            const logEl = document.getElementById(logId);
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = `log-entry log-${type}`;
            entry.innerHTML = `<span class="log-time">[${time}]</span> ${message}`;
            logEl.insertBefore(entry, logEl.firstChild);

            while (logEl.children.length > 50) {
                logEl.removeChild(logEl.lastChild);
            }
        }

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function updateStatusDot(dotId, statusId, status) {
            const dot = document.getElementById(dotId);
            const label = document.getElementById(statusId);

            dot.className = 'status-dot status-' + status;
            label.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        }

        function updateCheck(elementId, configured) {
            const el = document.getElementById(elementId);
            if (configured) {
                el.textContent = '\\u2713';
                el.className = 'config-check';
            } else {
                el.textContent = '\\u2717';
                el.className = 'config-x';
            }
        }

        async function refreshStatus() {
            const icon = document.getElementById('refresh-icon');
            icon.classList.add('spinning');
            log('Refreshing status...', 'info');

            try {
                const response = await fetch('api/status');
                const data = await response.json();

                // Update Client
                updateStatusDot('client-dot', 'client-status', data.client.status);
                document.getElementById('client-receiver').textContent = data.client.details?.receiver_port || '-';
                document.getElementById('client-env').textContent = data.client.details?.environment || '-';
                updateCheck('hmac-check', data.client.details?.hmac_secret_configured);
                updateCheck('alerts-check', data.client.details?.workflow_alerts_configured);
                updateCheck('reports-check', data.client.details?.workflow_reports_configured);

                // Update Agent
                updateStatusDot('agent-dot', 'agent-status', data.agent.status);
                document.getElementById('agent-url').textContent = data.agent.url || '-';
                document.getElementById('agent-response').textContent =
                    data.agent.response_time_ms ? `${data.agent.response_time_ms}ms` : '-';
                document.getElementById('agent-version').textContent =
                    data.agent.details?.version || '-';
                document.getElementById('agent-lastcheck').textContent =
                    new Date(data.agent.last_check).toLocaleTimeString();

                // Update Sessions
                const sessionStats = data.client.details?.session_stats || {};
                const sessionType = data.client.details?.session_store || 'memory';
                const sessionDot = document.getElementById('session-dot');
                const sessionStatus = document.getElementById('session-status');

                if (sessionStats.connected === true || sessionType === 'memory') {
                    sessionDot.className = 'status-dot status-healthy';
                    sessionStatus.textContent = 'Active';
                } else if (sessionStats.connected === false) {
                    sessionDot.className = 'status-dot status-error';
                    sessionStatus.textContent = 'Disconnected';
                } else {
                    sessionDot.className = 'status-dot status-checking';
                    sessionStatus.textContent = 'Unknown';
                }

                document.getElementById('session-type').textContent = sessionType;
                document.getElementById('session-count').textContent = sessionStats.active_sessions ?? '-';
                document.getElementById('session-ttl').textContent =
                    data.client.details?.session_ttl_hours ? `${data.client.details.session_ttl_hours}h` : '-';

                log('Status updated successfully', 'success');
            } catch (error) {
                log(`Error: ${error.message}`, 'error');
            }

            icon.classList.remove('spinning');
        }

        async function testAgent() {
            const message = document.getElementById('test-message').value;
            if (!message.trim()) {
                log('Please enter a message', 'error');
                return;
            }

            log(`Sending to agent: "${message.substring(0, 50)}${message.length > 50 ? '...' : ''}"`, 'info');

            try {
                const response = await fetch(`api/test/agent?message=${encodeURIComponent(message)}`, {
                    method: 'POST'
                });
                const data = await response.json();

                if (data.success) {
                    log(`Agent response: ${data.message.substring(0, 100)}${data.message.length > 100 ? '...' : ''}`, 'success');
                    if (data.response_time_ms) {
                        log(`Response time: ${data.response_time_ms}ms`, 'info');
                    }
                } else {
                    log(`Test failed: ${data.message}`, 'error');
                }
            } catch (error) {
                log(`Error: ${error.message}`, 'error');
            }
        }

        async function testWebhook() {
            const message = document.getElementById('test-message').value;
            if (!message.trim()) {
                log('Please enter a message', 'error');
                return;
            }

            log(`Testing webhook with: "${message.substring(0, 50)}${message.length > 50 ? '...' : ''}"`, 'info');

            try {
                const response = await fetch(`api/test/webhook?message=${encodeURIComponent(message)}`, {
                    method: 'POST'
                });
                const data = await response.json();

                if (data.success) {
                    log(`Webhook response: ${data.message.substring(0, 100)}${data.message.length > 100 ? '...' : ''}`, 'success');
                    if (data.response_time_ms) {
                        log(`Response time: ${data.response_time_ms}ms`, 'info');
                    }
                } else {
                    log(`Webhook test failed: ${data.message}`, 'error');
                }
            } catch (error) {
                log(`Error: ${error.message}`, 'error');
            }
        }

        async function testWorkflow(workflowType) {
            const message = document.getElementById('workflow-message').value;
            const title = document.getElementById('workflow-title').value;
            if (!message.trim()) {
                log('Please enter a message', 'error', 'workflow-log');
                return;
            }

            log(`Sending to ${workflowType} workflow: "${message.substring(0, 40)}..."`, 'info', 'workflow-log');

            try {
                const response = await fetch(`api/test/workflow/${workflowType}?message=${encodeURIComponent(message)}&title=${encodeURIComponent(title)}`, {
                    method: 'POST'
                });
                const data = await response.json();

                if (data.success) {
                    log(`${workflowType} workflow: ${data.message}`, 'success', 'workflow-log');
                    if (data.response_time_ms) {
                        log(`Response time: ${data.response_time_ms}ms`, 'info', 'workflow-log');
                    }
                } else {
                    log(`${workflowType} workflow failed: ${data.message}`, 'error', 'workflow-log');
                }
            } catch (error) {
                log(`Error: ${error.message}`, 'error', 'workflow-log');
            }
        }

        // Sessions functions
        async function refreshSessions() {
            try {
                const response = await fetch('api/sessions/list');
                const data = await response.json();

                document.getElementById('sessions-total').textContent = data.total;

                const container = document.getElementById('sessions-list');
                if (data.sessions.length === 0) {
                    container.innerHTML = '<div class="no-events">No active sessions. Sessions will appear here when users interact with the bot.</div>';
                    return;
                }

                container.innerHTML = data.sessions.map(session => `
                    <div class="event-item">
                        <div class="event-header">
                            <span class="event-type session">Session</span>
                            <span class="event-time">${new Date(session.last_activity).toLocaleString()}</span>
                        </div>
                        <div class="event-user">User: ${escapeHtml(session.user_id)}</div>
                        <div class="event-text">Conversation: ${escapeHtml(session.conversation_id.substring(0, 50))}...</div>
                        <div class="event-meta">
                            Messages: ${session.message_count} |
                            Session ID: ${escapeHtml(session.session_id.substring(0, 20))}...
                        </div>
                        <div style="margin-top: 8px;">
                            <button class="btn btn-sm btn-danger" onclick="deleteSession('${escapeHtml(session.user_id)}', '${escapeHtml(session.conversation_id)}')">Delete</button>
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error refreshing sessions:', error);
            }
        }

        async function clearAllSessions() {
            if (!confirm('Clear ALL sessions? This will end all active conversations.')) return;
            try {
                const response = await fetch('api/sessions', { method: 'DELETE' });
                const data = await response.json();
                alert(data.message || data.error);
                refreshSessions();
            } catch (error) {
                console.error('Error clearing sessions:', error);
            }
        }

        async function deleteSession(userId, conversationId) {
            if (!confirm('Delete this session?')) return;
            try {
                const response = await fetch(`api/sessions/${encodeURIComponent(userId)}/${encodeURIComponent(conversationId)}`, {
                    method: 'DELETE'
                });
                const data = await response.json();
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    refreshSessions();
                }
            } catch (error) {
                console.error('Error deleting session:', error);
            }
        }

        // Endpoint testing
        async function testEndpoint(endpoint) {
            const logId = 'endpoint-log';
            log(`Testing ${endpoint}...`, 'info', logId);

            try {
                const start = Date.now();
                const response = await fetch(endpoint);
                const elapsed = Date.now() - start;
                const data = await response.json();

                log(`${endpoint} - ${response.status} (${elapsed}ms)`, response.ok ? 'success' : 'error', logId);
                log(`Response: ${JSON.stringify(data).substring(0, 200)}${JSON.stringify(data).length > 200 ? '...' : ''}`, 'info', logId);
            } catch (error) {
                log(`${endpoint} - Error: ${error.message}`, 'error', logId);
            }
        }

        // Initial load
        refreshStatus();
        refreshSessions();

        // Auto-refresh every 60 seconds
        setInterval(refreshStatus, 60000);
    </script>
</body>
</html>
"""
