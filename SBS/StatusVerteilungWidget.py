"""
StatusVerteilungWidget – Order-status distribution panel for the dashboard.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Display a breakdown of all orders by their current status.
  - Show a coloured dot, the status name, the count and the percentage share for each status.

Dependencies:
  - styles: centralised colour constants and STATUS_FARBEN mapping
  - SBS._utils: shared _farbe_badge helper (imported but not used here directly;
    the widget builds its rows manually for layout reasons)
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QFont
from styles import COLOR_WHITE, COLOR_BORDER, COLOR_PRIMARY, COLOR_TEXT_LIGHT, STATUS_FARBEN


class StatusVerteilungWidget(QFrame):
    """
    Shows the distribution of all orders by their status.

    For each status (e.g. "Offen", "In Bearbeitung", "Geliefert") a row is
    displayed with a coloured dot, the status name, the count and the
    percentage share.
    """

    def __init__(self, data: list, parent=None):
        """
        Create the status-distribution widget.

        :param data:   List of dictionaries with keys "status" and "anzahl".
                       Example: [{"status": "Offen", "anzahl": 12}, …]
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
        title = QLabel("📦 Bestellstatus")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_PRIMARY};")
        layout.addWidget(title)

        # Calculate the total number of orders (used for percentage values).
        # "or 1" prevents a division-by-zero error.
        total = sum(d["anzahl"] for d in data) or 1

        # Build one row for each status.
        for d in data:
            # Look up the colour from the global STATUS_FARBEN dictionary;
            # fall back to muted grey if the status is unknown.
            farbe = STATUS_FARBEN.get(d["status"], COLOR_TEXT_LIGHT)

            row = QHBoxLayout()

            # Coloured bullet point ("●") as a visual status indicator.
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {farbe}; font-size: 16px;")
            dot.setFixedWidth(20)  # Fixed width keeps all rows aligned.

            # Status name.
            name = QLabel(d["status"])
            name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            name.setStyleSheet("font-size: 12px;")

            # Calculate and display the percentage share alongside the count.
            pct = int(d["anzahl"] / total * 100)
            val = QLabel(f"{d['anzahl']}  ({pct}%)")
            val.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_LIGHT};")

            row.addWidget(dot)
            row.addWidget(name)
            row.addWidget(val)
            layout.addLayout(row)
