"""
PageHeader – Header bar displayed at the top of each content page.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Display a bold page title and an optional subtitle.
  - Provide a consistent visual header for all four main pages.

Dependencies:
  - styles: centralised colour constants (applied via the global stylesheet)
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont


class PageHeader(QFrame):
    """
    Header bar for a content page.

    Displays a bold page title and an optional subtitle.
    Inserted at the top of each of the four main pages.
    """

    def __init__(self, title: str, subtitle: str = "", parent=None):
        """
        Create the page header.

        :param title:    Main heading of the page (e.g. "🏠 Dashboard")
        :param subtitle: Short description below the title (optional)
        :param parent:   Optional parent widget
        """
        super().__init__(parent)

        # Object name for the stylesheet (white background, shadow, etc.).
        self.setObjectName("page_header")

        # Vertical layout with padding.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 14, 24, 14)
        layout.setSpacing(2)

        # Main title label.
        t = QLabel(title)
        t.setObjectName("page_title")
        t.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(t)

        # Only add the subtitle label if a text was provided.
        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("page_subtitle")
            layout.addWidget(s)
