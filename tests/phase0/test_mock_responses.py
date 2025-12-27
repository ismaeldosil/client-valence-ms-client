"""
Tests for Mock Responses data.
"""

from tests.mocks.mock_responses import (
    DEFAULT_RESPONSE,
    KNOWLEDGE_BASE,
    get_response_for_query,
)


class TestKnowledgeBase:
    """Tests for KNOWLEDGE_BASE data."""

    def test_has_minimum_entries(self) -> None:
        """Knowledge base has at least 5 entries."""
        assert len(KNOWLEDGE_BASE) >= 5

    def test_entries_have_required_fields(self) -> None:
        """Each entry has text, sources, confidence."""
        for keyword, data in KNOWLEDGE_BASE.items():
            assert "text" in data, f"Missing 'text' in {keyword}"
            assert "sources" in data, f"Missing 'sources' in {keyword}"
            assert "confidence" in data, f"Missing 'confidence' in {keyword}"

    def test_confidence_in_valid_range(self) -> None:
        """Confidence scores are between 0 and 1."""
        for keyword, data in KNOWLEDGE_BASE.items():
            assert 0 <= data["confidence"] <= 1, f"Invalid confidence for {keyword}"

    def test_text_is_not_empty(self) -> None:
        """Text responses are not empty."""
        for keyword, data in KNOWLEDGE_BASE.items():
            assert len(data["text"]) > 0, f"Empty text for {keyword}"

    def test_sources_is_list(self) -> None:
        """Sources is a list."""
        for keyword, data in KNOWLEDGE_BASE.items():
            assert isinstance(data["sources"], list), f"Sources not a list for {keyword}"


class TestDefaultResponse:
    """Tests for DEFAULT_RESPONSE."""

    def test_has_required_fields(self) -> None:
        """Default response has required fields."""
        assert "text" in DEFAULT_RESPONSE
        assert "sources" in DEFAULT_RESPONSE
        assert "confidence" in DEFAULT_RESPONSE

    def test_low_confidence(self) -> None:
        """Default response has low confidence."""
        assert DEFAULT_RESPONSE["confidence"] < 0.5

    def test_empty_sources(self) -> None:
        """Default response has no sources."""
        assert len(DEFAULT_RESPONSE["sources"]) == 0


class TestGetResponseForQuery:
    """Tests for get_response_for_query function."""

    def test_matches_vacaciones(self) -> None:
        """Matches query with 'vacaciones'."""
        response = get_response_for_query("Cual es la politica de vacaciones?")
        assert response["confidence"] > 0.9

    def test_matches_horario(self) -> None:
        """Matches query with 'horario'."""
        response = get_response_for_query("Cual es el horario?")
        assert response["confidence"] > 0.9

    def test_case_insensitive(self) -> None:
        """Matching is case insensitive."""
        response1 = get_response_for_query("VACACIONES")
        response2 = get_response_for_query("vacaciones")
        assert response1["confidence"] == response2["confidence"]

    def test_returns_default_for_unknown(self) -> None:
        """Returns default response for unknown queries."""
        response = get_response_for_query("xyz123 unknown query")
        assert response["confidence"] < 0.5

    def test_returns_dict(self) -> None:
        """Always returns a dict."""
        response = get_response_for_query("anything")
        assert isinstance(response, dict)
