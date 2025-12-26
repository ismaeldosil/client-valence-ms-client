"""
Adaptive Card Builder for Microsoft Teams.

Builds Adaptive Cards following the 1.4 schema.
"""

from datetime import datetime
from typing import Any, Optional


class AdaptiveCardBuilder:
    """
    Builder for creating Adaptive Cards.

    Supports:
    - Alert cards (with priority colors)
    - Info cards (informational messages)
    - Report cards (with data tables)

    Note:
        Only 'openURL' action is supported in Teams webhooks.
        Other actions (submit, execute, etc.) will not work.
    """

    PRIORITY_COLORS = {
        "low": "good",        # Green
        "medium": "accent",   # Blue
        "high": "warning",    # Yellow
        "critical": "attention",  # Red
    }

    PRIORITY_ICONS = {
        "low": "ℹ️",
        "medium": "📢",
        "high": "⚠️",
        "critical": "🚨",
    }

    def build(
        self,
        card_type: str,
        title: str,
        message: str,
        priority: str = "medium",
        **kwargs: Any,
    ) -> dict:
        """
        Build a card by type.

        Args:
            card_type: One of "alert", "info", "report"
            title: Card title
            message: Main message text
            priority: Priority level (low, medium, high, critical)
            **kwargs: Additional parameters for specific card types

        Returns:
            Adaptive Card dictionary
        """
        builders = {
            "alert": self.build_alert_card,
            "info": self.build_info_card,
            "report": self.build_report_card,
        }

        builder = builders.get(card_type)
        if not builder:
            raise ValueError(f"Unknown card type: {card_type}")

        return builder(title=title, message=message, priority=priority, **kwargs)

    def build_alert_card(
        self,
        title: str,
        message: str,
        priority: str = "medium",
        source: Optional[str] = None,
        action_url: Optional[str] = None,
        action_title: str = "Ver detalles",
        **kwargs: Any,
    ) -> dict:
        """
        Build an alert card with priority styling.

        Args:
            title: Alert title
            message: Alert message
            priority: Priority level
            source: Optional source system
            action_url: Optional URL for action button
            action_title: Action button text

        Returns:
            Adaptive Card dictionary
        """
        icon = self.PRIORITY_ICONS.get(priority, "📢")
        color = self.PRIORITY_COLORS.get(priority, "accent")

        body = [
            {
                "type": "Container",
                "style": color,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"{icon} {title}",
                        "weight": "Bolder",
                        "size": "Large",
                        "wrap": True,
                    }
                ],
            },
            {
                "type": "TextBlock",
                "text": message,
                "wrap": True,
            },
        ]

        # Add source if provided
        if source:
            body.append({
                "type": "TextBlock",
                "text": f"Fuente: {source}",
                "size": "Small",
                "isSubtle": True,
            })

        # Add timestamp
        body.append({
            "type": "TextBlock",
            "text": f"_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
            "size": "Small",
            "isSubtle": True,
        })

        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body,
        }

        # Add action button if URL provided
        if action_url:
            card["actions"] = [
                {
                    "type": "Action.OpenUrl",
                    "title": action_title,
                    "url": action_url,
                }
            ]

        return card

    def build_info_card(
        self,
        title: str,
        message: str,
        priority: str = "medium",
        footer: Optional[str] = None,
        **kwargs: Any,
    ) -> dict:
        """
        Build an informational card.

        Args:
            title: Card title
            message: Information message
            priority: Priority level (affects icon only)
            footer: Optional footer text

        Returns:
            Adaptive Card dictionary
        """
        icon = self.PRIORITY_ICONS.get(priority, "ℹ️")

        body = [
            {
                "type": "TextBlock",
                "text": f"{icon} {title}",
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True,
            },
            {
                "type": "TextBlock",
                "text": message,
                "wrap": True,
            },
        ]

        if footer:
            body.append({
                "type": "TextBlock",
                "text": footer,
                "size": "Small",
                "isSubtle": True,
                "wrap": True,
            })

        return {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body,
        }

    def build_report_card(
        self,
        title: str,
        message: str,
        priority: str = "medium",
        data: Optional[dict] = None,
        columns: Optional[list] = None,
        **kwargs: Any,
    ) -> dict:
        """
        Build a report card with data table.

        Args:
            title: Report title
            message: Report description
            priority: Priority level
            data: Dictionary of key-value pairs to display
            columns: List of column definitions for table

        Returns:
            Adaptive Card dictionary
        """
        icon = self.PRIORITY_ICONS.get(priority, "📊")

        body = [
            {
                "type": "TextBlock",
                "text": f"{icon} {title}",
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True,
            },
            {
                "type": "TextBlock",
                "text": message,
                "wrap": True,
            },
        ]

        # Add data as fact set
        if data:
            facts = [
                {"title": str(k), "value": str(v)}
                for k, v in data.items()
            ]
            body.append({
                "type": "FactSet",
                "facts": facts,
            })

        # Add timestamp
        body.append({
            "type": "TextBlock",
            "text": f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "size": "Small",
            "isSubtle": True,
        })

        return {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body,
        }
