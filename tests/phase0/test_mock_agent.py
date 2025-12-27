"""
Tests for Mock Agent Server.
"""

from fastapi.testclient import TestClient


class TestMockAgentHealth:
    """Tests for /health endpoint."""

    def test_health_returns_ok(self, agent_test_client: TestClient) -> None:
        """Health check returns healthy status."""
        response = agent_test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestMockAgentQuery:
    """Tests for /query endpoint."""

    def test_query_vacaciones(self, agent_test_client: TestClient) -> None:
        """Query with 'vacaciones' returns vacation policy."""
        response = agent_test_client.post(
            "/query",
            json={
                "message": "Cual es la politica de vacaciones?",
                "context": {"platform": "test"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "15 dias" in data["text"].lower() or "15 días" in data["text"].lower()
        assert data["confidence"] > 0.9
        assert len(data["sources"]) > 0
        assert data["processing_time_ms"] > 0

    def test_query_horario(self, agent_test_client: TestClient) -> None:
        """Query with 'horario' returns schedule info."""
        response = agent_test_client.post(
            "/query",
            json={
                "message": "Cual es el horario de trabajo?",
                "context": {"platform": "test"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "9:00" in data["text"] or "18:00" in data["text"]
        assert data["confidence"] > 0.9

    def test_query_remoto(self, agent_test_client: TestClient) -> None:
        """Query with 'remoto' returns remote work policy."""
        response = agent_test_client.post(
            "/query",
            json={
                "message": "Puedo trabajar remoto?",
                "context": {"platform": "test"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "remoto" in data["text"].lower() or "casa" in data["text"].lower()
        assert data["confidence"] > 0.8

    def test_query_unknown(self, agent_test_client: TestClient) -> None:
        """Unknown query returns default response."""
        response = agent_test_client.post(
            "/query",
            json={
                "message": "Cual es el sentido de la vida?",
                "context": {"platform": "test"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["confidence"] < 0.5
        assert len(data["sources"]) == 0

    def test_query_with_history(
        self,
        agent_test_client: TestClient,
        sample_query_with_history: dict,
    ) -> None:
        """Query with conversation history is accepted."""
        response = agent_test_client.post("/query", json=sample_query_with_history)

        assert response.status_code == 200
        data = response.json()
        assert "text" in data

    def test_response_format(
        self,
        agent_test_client: TestClient,
        sample_query_request: dict,
    ) -> None:
        """Response has correct format."""
        response = agent_test_client.post("/query", json=sample_query_request)

        assert response.status_code == 200
        data = response.json()

        # Check all required fields
        assert "text" in data
        assert "sources" in data
        assert "confidence" in data
        assert "processing_time_ms" in data

        # Check types
        assert isinstance(data["text"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["confidence"], float)
        assert isinstance(data["processing_time_ms"], int)
