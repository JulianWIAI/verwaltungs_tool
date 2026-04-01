"""
DashboardWidget – Main widget for the dashboard page.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Combine all dashboard cards and charts into a scrollable overview page.
  - Auto-refresh all displayed data every 60 seconds using a QTimer.
  - Load and update six StatCards, one MiniChart, one TopArtikelWidget and one
    StatusVerteilungWidget.

Dependencies:
  - database (db): all SQLite operations
  - styles: centralised colour constants
  - SBS.StatCard: individual KPI card
  - SBS.MiniChart: bar chart for monthly revenue
  - SBS.TopArtikelWidget: ranked list of best-selling articles
  - SBS.StatusVerteilungWidget: order-status breakdown
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

import database as db
from styles import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_SUCCESS, COLOR_WARNING,
    COLOR_DANGER, COLOR_WHITE, COLOR_TEXT_LIGHT, COLOR_INFO
)
from SBS.StatCard import StatCard
from SBS.MiniChart import MiniChart
from SBS.TopArtikelWidget import TopArtikelWidget
from SBS.StatusVerteilungWidget import StatusVerteilungWidget


class DashboardWidget(QWidget):
    """
    Main widget for the dashboard page.

    Combines all cards and charts into a scrollable overview.
    Refreshes automatically every 60 seconds via a QTimer.

    Page layout (top to bottom):
    1. Greeting row
    2. Row of 6 StatCards (Customers, Articles, Orders, Open, Revenue, Reorder)
    3. Charts row (MiniChart + TopArtikelWidget)
    4. Bottom row (StatusVerteilungWidget + optional stock warning)
    """

    def __init__(self, parent=None):
        """
        Create the dashboard widget, build the UI and start the auto-refresh timer.

        :param parent: Optional parent widget
        """
        super().__init__(parent)

        # Build the user interface.
        self._setup_ui()

        # Immediately populate with data from the database.
        self.refresh()

        # Auto-refresh every 60 s.
        # QTimer emits a timeout signal after each interval;
        # that signal is connected to the refresh() method here.
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(60_000)  # 60,000 milliseconds = 60 seconds.

    def _setup_ui(self):
        """
        Build the static frame of the dashboard page:
        - Scroll area for all content.
        - Greeting row.
        - Empty placeholder layouts for cards, charts and the bottom row.

        The placeholders are filled with real content inside refresh().
        """
        # QScrollArea: makes all content scrollable if the window is too small.
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)             # Content adapts to the available width.
        scroll.setFrameShape(QFrame.Shape.NoFrame)  # No visible frame around the scroll area.
        scroll.setStyleSheet("background: transparent;")

        # Container widget inside the scroll area.
        container = QWidget()
        scroll.setWidget(container)

        # Outer layout of the DashboardWidget – only the scroll area.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # Inner layout inside the scroll area with outer margins.
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(24, 20, 24, 24)
        self.main_layout.setSpacing(20)  # Spacing between individual rows.

        # ── Greeting ──────────────────────────────────────────────────────────
        greet_row = QHBoxLayout()

        # Large greeting text.
        greet = QLabel("👋 Willkommen zurück!")
        greet.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        greet.setStyleSheet(f"color: {COLOR_PRIMARY};")

        # Small subtitle below the greeting.
        sub = QLabel("Hier ist Ihre aktuelle Übersicht")
        sub.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")

        # Stack greeting and subtitle vertically.
        greet_col = QVBoxLayout()
        greet_col.setSpacing(2)
        greet_col.addWidget(greet)
        greet_col.addWidget(sub)

        greet_row.addLayout(greet_col)
        greet_row.addStretch()  # Leave remaining space on the right empty.

        self.main_layout.addLayout(greet_row)

        # ── Stat cards ────────────────────────────────────────────────────────
        # Horizontal row of six KPI cards.
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(16)

        # Each StatCard is created with title, placeholder value "-", icon and colour.
        self.card_kunden       = StatCard("Kunden",         "-",  "👥", COLOR_INFO,      self)
        self.card_artikel      = StatCard("Artikel",        "-",  "🚲", COLOR_PRIMARY,   self)
        self.card_bestellungen = StatCard("Bestellungen",   "-",  "📦", COLOR_SUCCESS,   self)
        self.card_offen        = StatCard("Offen",          "-",  "⏳", COLOR_WARNING,   self)
        self.card_umsatz       = StatCard("Umsatz (Monat)", "-",  "💰", COLOR_SECONDARY, self)
        self.card_lager        = StatCard("Nachbestellen",  "-",  "⚠️", COLOR_DANGER,    self)

        # Add all cards to the layout.
        for card in [self.card_kunden, self.card_artikel, self.card_bestellungen,
                     self.card_offen, self.card_umsatz, self.card_lager]:
            # Expanding: cards share the available space equally.
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.stats_row.addWidget(card)

        self.main_layout.addLayout(self.stats_row)

        # ── Charts (placeholders – filled in refresh()) ───────────────────────
        # charts_row: revenue chart (left) + top articles (right).
        self.charts_row = QHBoxLayout()
        self.charts_row.setSpacing(16)
        self.main_layout.addLayout(self.charts_row)

        # bottom_row: status distribution + optional stock warning.
        self.bottom_row = QHBoxLayout()
        self.bottom_row.setSpacing(16)
        self.main_layout.addLayout(self.bottom_row)

        # Stretch at the end pushes everything upward and prevents ugly stretching.
        self.main_layout.addStretch()

        # Placeholder widgets (replaced by real widgets on the first refresh()).
        self._chart_widget  = None
        self._top_widget    = None
        self._status_widget = None

    def _clear_layout(self, layout):
        """
        Remove all widgets from a layout and free their memory.

        Called before each refresh() so that chart rows can be rebuilt
        without creating duplicates.

        :param layout: The QLayout object to empty.
        """
        # Keep removing items as long as the layout contains any.
        while layout.count():
            # takeAt(0) removes the first item and returns it.
            item = layout.takeAt(0)
            if item.widget():
                # deleteLater() frees the widget after the current event cycle.
                item.widget().deleteLater()

    def refresh(self):
        """
        Load current data from the database and update all dashboard elements.

        This method is called:
        - Once at startup.
        - Automatically every 60 seconds by the QTimer.
        - Manually when order data changes.
        """
        # Fetch all KPIs from the database in a single call.
        stats = db.get_dashboard_stats()

        # ── Update StatCards ──────────────────────────────────────────────────
        self.card_kunden.update_wert(str(stats["kunden_gesamt"]))
        self.card_artikel.update_wert(str(stats["artikel_gesamt"]))
        self.card_bestellungen.update_wert(str(stats["bestellungen_gesamt"]))
        self.card_offen.update_wert(str(stats["bestellungen_offen"]))
        # Revenue formatted with thousands separator and no decimal places.
        self.card_umsatz.update_wert(f"€ {stats['umsatz_monat']:,.0f}")
        self.card_lager.update_wert(str(stats["nachbestellen"]))

        # ── Rebuild charts ────────────────────────────────────────────────────
        # Remove old chart widgets (otherwise new ones would be added every refresh).
        self._clear_layout(self.charts_row)
        self._clear_layout(self.bottom_row)

        # Revenue bar chart with monthly data for the last 6 months.
        chart = MiniChart("📈 Umsatz (letzte 6 Monate)", stats["umsatz_verlauf"])
        chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        chart.setMinimumHeight(180)
        # stretch=2: the chart gets twice as much space as the top-articles list.
        self.charts_row.addWidget(chart, stretch=2)

        # Top-articles list (best article at the top).
        top = TopArtikelWidget(stats["top_artikel"])
        top.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # stretch=1: top articles get half as much space as the chart.
        self.charts_row.addWidget(top, stretch=1)

        # Status distribution (always shown).
        status_w = StatusVerteilungWidget(stats["status_verteilung"])
        status_w.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        status_w.setFixedWidth(260)  # Fixed width for the status widget.
        self.bottom_row.addWidget(status_w)

        # ── Stock warning (only when needed) ──────────────────────────────────
        # Show the warning only when there are actually articles to reorder.
        if stats["nachbestellen"] > 0:
            # Yellow warning frame.
            warn = QFrame()
            warn.setStyleSheet(f"""
                background: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 10px;
                padding: 12px;
            """)
            warn_layout = QHBoxLayout(warn)

            # Warning icon.
            icon = QLabel("⚠️")
            icon.setFont(QFont("Segoe UI Emoji", 18))

            # Warning text with the number of affected articles in bold.
            msg = QLabel(
                f"<b>{stats['nachbestellen']} Artikel</b> haben den Mindestbestand unterschritten "
                "und sollten nachbestellt werden."
            )
            msg.setWordWrap(True)  # Allow line wrapping for long texts.
            msg.setStyleSheet("color: #856404; font-size: 13px;")

            warn_layout.addWidget(icon)
            warn_layout.addWidget(msg)
            self.bottom_row.addWidget(warn)

        # Leave remaining space in the bottom row empty.
        self.bottom_row.addStretch()
