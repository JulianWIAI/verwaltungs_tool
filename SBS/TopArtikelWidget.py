"""
TopArtikelWidget – Ranked list of the best-selling articles.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Display the top articles as numbered rows with a progress bar and revenue amount.
  - Use distinct accent colours for ranks 1–5 (cycling for additional ranks).

Dependencies:
  - styles: centralised colour constants
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from styles import (
    COLOR_WHITE, COLOR_BORDER, COLOR_PRIMARY, COLOR_TEXT_LIGHT,
    COLOR_SECONDARY, COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING
)


class TopArtikelWidget(QFrame):
    """
    Ranked list of the best-selling articles.

    Shows the top articles as numbered rows with a progress bar and
    a revenue figure.
    """

    def __init__(self, data: list, parent=None):
        """
        Create the top-articles list.

        :param data:   List of dictionaries with keys "bezeichnung" and "umsatz".
                       The list should already be sorted in descending order by revenue.
        :param parent: Optional parent widget
        """
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            #card {{
                background: {COLOR_WHITE};
                border-radius: 12px;
                border: 1px solid {COLOR_BORDER};
                padding: 16px;
            }}
        """)
        layout = QVBoxLayout(self)

        # Heading.
        title = QLabel("🏆 Top Artikel")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_PRIMARY};")
        layout.addWidget(title)

        # Empty state: no sales in the database yet.
        if not data:
            empty = QLabel("Noch keine Verkäufe")
            empty.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
            layout.addWidget(empty)
            return

        # Different accent colours for ranks 1–5 (cycled for additional ranks).
        farben = [COLOR_SECONDARY, COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING, "#9b59b6"]

        # Revenue of the leading article as the reference value for bar width.
        max_u = data[0]["umsatz"] if data else 1

        # Build one row for each article.
        for i, art in enumerate(data):
            row = QHBoxLayout()

            # Rank number (e.g. "#1").
            rang = QLabel(f"#{i+1}")
            rang.setFixedWidth(28)
            rang.setStyleSheet(f"""
                font-weight: 700; font-size: 13px;
                color: {farben[i % len(farben)]};
            """)

            # Article name, truncated to 30 characters to prevent overflow.
            name = QLabel(art["bezeichnung"][:30])
            name.setStyleSheet("font-size: 12px;")
            # Expanding: the name fills the available space between rank and bar.
            name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

            # ── Progress bar ──────────────────────────────────────────────────
            # Grey background frame of the bar.
            bar_bg = QFrame()
            bar_bg.setFixedHeight(6)
            bar_bg.setStyleSheet(f"background: #f0f2f5; border-radius: 3px;")

            # Coloured progress bar as a child of the background frame.
            bar_w = QFrame(bar_bg)

            # Width proportional to the maximum revenue; at least 4 pixels visible.
            breite = max(4, int((art["umsatz"] / max_u) * 120))
            bar_w.setFixedSize(breite, 6)
            bar_w.setStyleSheet(f"background: {farben[i % len(farben)]}; border-radius: 3px;")

            # Revenue label on the right side of the row.
            val = QLabel(f"€ {art['umsatz']:,.0f}")
            val.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLOR_PRIMARY};")
            val.setFixedWidth(80)
            val.setAlignment(Qt.AlignmentFlag.AlignRight)

            # Pack the bar into a container so the layout works correctly.
            row.addWidget(rang)
            row.addWidget(name)
            bar_container = QWidget()
            bar_container.setFixedWidth(130)
            bar_container.setLayout(QVBoxLayout())
            bar_container.layout().setContentsMargins(0, 4, 0, 0)  # Small top indent.
            bar_container.layout().addWidget(bar_bg)
            row.addWidget(bar_container)
            row.addWidget(val)

            # Add the finished row to the overall layout.
            layout.addLayout(row)
