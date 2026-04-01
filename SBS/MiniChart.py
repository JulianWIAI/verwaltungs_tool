"""
MiniChart – Simple bar chart for the dashboard revenue trend.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Render monthly revenue figures as proportionally scaled vertical bars.
  - Operate without any external charting library (pure PyQt6 widgets only).
  - Display a placeholder message when no data is available.

Dependencies:
  - styles: centralised colour constants
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from styles import COLOR_WHITE, COLOR_BORDER, COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT_LIGHT


class MiniChart(QFrame):
    """
    Simple bar chart (no matplotlib required).

    Renders the revenue trend over recent months as vertical bars.
    Each bar is scaled proportionally to the maximum value.
    """

    def __init__(self, title: str, data: list, parent=None):
        """
        Create the bar chart.

        :param title:  Heading of the chart (e.g. "📈 Revenue last 6 months")
        :param data:   List of dictionaries with keys "monat" and "umsatz".
                       Example: [{"monat": "2025-01", "umsatz": 4200.0}, …]
        :param parent: Optional parent widget
        """
        super().__init__(parent)

        # Object name "card" → white card style from the stylesheet.
        self.setObjectName("card")
        self.setStyleSheet(f"""
            #card {{
                background: {COLOR_WHITE};
                border-radius: 12px;
                border: 1px solid {COLOR_BORDER};
                padding: 16px;
            }}
        """)

        # Store data as an instance variable (currently for reference only).
        self.data = data

        layout = QVBoxLayout(self)

        # Chart heading.
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLOR_PRIMARY};")
        layout.addWidget(title_lbl)

        # Empty state: show a hint text and return early without drawing bars.
        if not data:
            empty = QLabel("Noch keine Daten vorhanden")
            empty.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)
            return  # Early exit – do not draw the chart.

        # Determine the maximum revenue value for scaling.
        # "or 1" prevents a division-by-zero error in the next step.
        max_val = max(d.get("umsatz", 0) for d in data) or 1

        # Container widget for all bars (horizontal layout).
        bars_widget = QWidget()
        bars_layout = QHBoxLayout(bars_widget)
        bars_layout.setSpacing(8)
        bars_layout.setContentsMargins(0, 8, 0, 0)

        # Draw one bar for each data point.
        for d in data:
            # Vertical sub-layout: value label on top, bar in the middle, month label at the bottom.
            bar_container = QVBoxLayout()
            bar_container.setSpacing(4)
            # Align to the bottom so small bars "grow" upward from the baseline.
            bar_container.setAlignment(Qt.AlignmentFlag.AlignBottom)

            umsatz = d.get("umsatz", 0)

            # Calculate bar height proportionally to the maximum value.
            # max(4, …) ensures even a zero value remains visible (4 px minimum).
            hoehe = max(4, int((umsatz / max_val) * 100))

            # The actual bar as a coloured QFrame.
            bar = QFrame()
            bar.setFixedSize(40, hoehe)  # Bar width fixed at 40 px, height dynamic.
            # Linear gradient from top (COLOR_SECONDARY) to bottom (darker red).
            bar.setStyleSheet(f"""
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {COLOR_SECONDARY}, stop:1 #c1121f);
                border-radius: 4px;
            """)

            # Value label above the bar (in thousands, e.g. "4.2k").
            val_lbl = QLabel(f"{umsatz/1000:.1f}k")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_lbl.setStyleSheet("font-size: 10px; color: " + COLOR_TEXT_LIGHT + ";")
            val_lbl.setFixedWidth(50)

            # Month label below the bar – last 5 characters only (MM-YY).
            monat_lbl = QLabel(d.get("monat", "")[-5:])  # MM-YY
            monat_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            monat_lbl.setStyleSheet("font-size: 10px; color: " + COLOR_TEXT_LIGHT + ";")
            monat_lbl.setFixedWidth(50)

            # Add elements to the bar container (top to bottom).
            bar_container.addWidget(val_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            bar_container.addWidget(bar, alignment=Qt.AlignmentFlag.AlignCenter)
            bar_container.addWidget(monat_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

            # Add the finished bar to the horizontal overall layout.
            bars_layout.addLayout(bar_container)

        # Leave remaining space on the right empty (bars are left-aligned).
        bars_layout.addStretch()
        layout.addWidget(bars_widget)
