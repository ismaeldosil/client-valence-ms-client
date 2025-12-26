"""
Tests for Adaptive Card Builder.
"""

import pytest

from src.teams.sender.cards import AdaptiveCardBuilder


class TestAdaptiveCardBuilder:
    """Tests for AdaptiveCardBuilder class."""

    @pytest.fixture
    def builder(self) -> AdaptiveCardBuilder:
        """Create a card builder instance."""
        return AdaptiveCardBuilder()

    def test_build_alert_card(self, builder: AdaptiveCardBuilder) -> None:
        """Test building an alert card."""
        card = builder.build_alert_card(
            title="System Alert",
            message="CPU usage is high",
            priority="critical",
        )

        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.4"
        assert len(card["body"]) >= 2

        # Check title container has attention style
        title_container = card["body"][0]
        assert title_container["type"] == "Container"
        assert title_container["style"] == "attention"

    def test_build_alert_card_with_action(self, builder: AdaptiveCardBuilder) -> None:
        """Test alert card with action URL."""
        card = builder.build_alert_card(
            title="Alert",
            message="Check the dashboard",
            priority="high",
            action_url="https://example.com/dashboard",
            action_title="View Dashboard",
        )

        assert "actions" in card
        assert len(card["actions"]) == 1
        assert card["actions"][0]["type"] == "Action.OpenUrl"
        assert card["actions"][0]["url"] == "https://example.com/dashboard"
        assert card["actions"][0]["title"] == "View Dashboard"

    def test_build_info_card(self, builder: AdaptiveCardBuilder) -> None:
        """Test building an info card."""
        card = builder.build_info_card(
            title="Information",
            message="This is an info message",
            priority="low",
        )

        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.4"
        assert "ℹ️" in card["body"][0]["text"]

    def test_build_report_card(self, builder: AdaptiveCardBuilder) -> None:
        """Test building a report card."""
        card = builder.build_report_card(
            title="Daily Report",
            message="Summary of today's activities",
            priority="medium",
            data={
                "Total Users": "1,234",
                "Active Sessions": "567",
                "Errors": "3",
            },
        )

        assert card["type"] == "AdaptiveCard"
        # Find FactSet
        fact_set = next(
            (item for item in card["body"] if item.get("type") == "FactSet"),
            None,
        )
        assert fact_set is not None
        assert len(fact_set["facts"]) == 3

    def test_build_by_type(self, builder: AdaptiveCardBuilder) -> None:
        """Test build method with type selection."""
        card = builder.build(
            card_type="alert",
            title="Test",
            message="Test message",
            priority="high",
        )

        assert card["type"] == "AdaptiveCard"

    def test_build_unknown_type_raises(self, builder: AdaptiveCardBuilder) -> None:
        """Test that unknown card type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            builder.build(
                card_type="unknown",
                title="Test",
                message="Test",
            )

        assert "Unknown card type" in str(exc_info.value)

    def test_priority_colors(self, builder: AdaptiveCardBuilder) -> None:
        """Test that different priorities use different colors."""
        priorities = ["low", "medium", "high", "critical"]
        colors = set()

        for priority in priorities:
            card = builder.build_alert_card(
                title="Test",
                message="Test",
                priority=priority,
            )
            color = card["body"][0]["style"]
            colors.add(color)

        # Each priority should have a different color
        assert len(colors) == 4

    def test_priority_icons(self, builder: AdaptiveCardBuilder) -> None:
        """Test that different priorities use different icons."""
        icons = {
            "low": "ℹ️",
            "medium": "📢",
            "high": "⚠️",
            "critical": "🚨",
        }

        for priority, expected_icon in icons.items():
            card = builder.build_info_card(
                title="Test",
                message="Test",
                priority=priority,
            )
            assert expected_icon in card["body"][0]["text"]
