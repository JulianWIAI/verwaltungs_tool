"""
StatCard – Single key-metric card for the dashboard.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Display one KPI as an emoji icon, a large numeric value and a label text.
  - Use a coloured left border to visually distinguish cards from each other.
  - Expose an update_wert() method so the dashboard can refresh the value without
    rebuilding the widget.

Dependencies:
  - styles: centralised colour constants
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from styles import COLOR_WHITE, COLOR_TEXT_LIGHT


class StatCard(QFrame):
    """
    Key-metric card for the dashboard.

    Each card shows an emoji icon, a large numeric value and a label text.
    The left edge is coloured to visually distinguish cards from one another.

    Example: "👥  342  Customers"
    """

    def __init__(self, titel: str, wert: str, icon: str, farbe: str, parent=None):
        """
        Create a new StatCard.

        :param titel:  Label below the value (e.g. "Customers")
        :param wert:   Displayed numeric value as a string (e.g. "342")
        :param icon:   Emoji character on the left side of the card (e.g. "👥")
        :param farbe:  Accent colour of the card as a hex code (e.g. "#0066cc")
        :param parent: Optional parent widget
        """
        super().__init__(parent)

        # Object name enables targeted addressing in the stylesheet.
        self.setObjectName("stat_card")

        # Inline stylesheet: white background, rounded corners, coloured left border.
        self.setStyleSheet(f"""
            #stat_card {{
                background: {COLOR_WHITE};
                border-radius: 12px;
                border-left: 5px solid {farbe};
                padding: 16px 20px;
            }}
        """)

        # Horizontal layout: icon on the left, text (value + label) on the right.
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Icon label ────────────────────────────────────────────────────────
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 28))  # Large emoji rendering.
        icon_lbl.setFixedSize(56, 56)                  # Square container.
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Background with very low opacity (18 hex ≈ 9 %) in the accent colour.
        icon_lbl.setStyleSheet(f"""
            background: {farbe}18;
            border-radius: 12px;
        """)

        # ── Text layout (value above, label below) ────────────────────────────
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        # Large, coloured numeric value (updated later via update_wert()).
        self.wert_lbl = QLabel(wert)
        self.wert_lbl.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        self.wert_lbl.setStyleSheet(f"color: {farbe};")

        # Label text in a muted colour.
        titel_lbl = QLabel(titel)
        titel_lbl.setWordWrap(True)  # Allow wrapping if the label is long.
        titel_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px; font-weight: 500;")

        text_layout.addWidget(self.wert_lbl)
        text_layout.addWidget(titel_lbl)

        # Assemble everything in the main layout.
        layout.addWidget(icon_lbl)
        layout.addSpacing(12)        # Gap between icon and text.
        layout.addLayout(text_layout)
        layout.addStretch()          # Leave remaining space on the right empty.

    def update_wert(self, wert: str):
        """
        Update the displayed numeric value of the card.

        :param wert: New value as a string (e.g. "347" or "€ 12.500")
        """
        self.wert_lbl.setText(wert)
