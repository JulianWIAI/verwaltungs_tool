"""
Radsport Koch GmbH – Dashboard
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import database as db
from styles import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_SUCCESS, COLOR_WARNING,
    COLOR_DANGER, COLOR_WHITE, COLOR_BG, COLOR_TEXT_LIGHT,
    COLOR_INFO, COLOR_CARD, COLOR_BORDER, STATUS_FARBEN
)


def _farbe_badge(text: str, farbe: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        background-color: {farbe}22;
        color: {farbe};
        border-radius: 10px;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: 600;
    """)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


class StatCard(QFrame):
    def __init__(self, titel: str, wert: str, icon: str, farbe: str, parent=None):
        super().__init__(parent)
        self.setObjectName("stat_card")
        self.setStyleSheet(f"""
            #stat_card {{
                background: {COLOR_WHITE};
                border-radius: 12px;
                border-left: 5px solid {farbe};
                padding: 16px 20px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 28))
        icon_lbl.setFixedSize(56, 56)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            background: {farbe}18;
            border-radius: 12px;
        """)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        self.wert_lbl = QLabel(wert)
        self.wert_lbl.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        self.wert_lbl.setStyleSheet(f"color: {farbe};")

        titel_lbl = QLabel(titel)
        titel_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px; font-weight: 500;")

        text_layout.addWidget(self.wert_lbl)
        text_layout.addWidget(titel_lbl)

        layout.addWidget(icon_lbl)
        layout.addSpacing(12)
        layout.addLayout(text_layout)
        layout.addStretch()

    def update_wert(self, wert: str):
        self.wert_lbl.setText(wert)


class MiniChart(QFrame):
    """Einfaches Balkendiagramm (kein matplotlib nötig)."""
    def __init__(self, title: str, data: list, parent=None):
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
        self.data = data
        layout = QVBoxLayout(self)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLOR_PRIMARY};")
        layout.addWidget(title_lbl)

        if not data:
            empty = QLabel("Noch keine Daten vorhanden")
            empty.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)
            return

        max_val = max(d.get("umsatz", 0) for d in data) or 1
        bars_widget = QWidget()
        bars_layout = QHBoxLayout(bars_widget)
        bars_layout.setSpacing(8)
        bars_layout.setContentsMargins(0, 8, 0, 0)

        for d in data:
            bar_container = QVBoxLayout()
            bar_container.setSpacing(4)
            bar_container.setAlignment(Qt.AlignmentFlag.AlignBottom)

            umsatz = d.get("umsatz", 0)
            hoehe = max(4, int((umsatz / max_val) * 100))

            bar = QFrame()
            bar.setFixedSize(40, hoehe)
            bar.setStyleSheet(f"""
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {COLOR_SECONDARY}, stop:1 #c1121f);
                border-radius: 4px;
            """)

            val_lbl = QLabel(f"{umsatz/1000:.1f}k")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_lbl.setStyleSheet("font-size: 10px; color: " + COLOR_TEXT_LIGHT + ";")
            val_lbl.setFixedWidth(50)

            monat_lbl = QLabel(d.get("monat", "")[-5:])  # MM-YY
            monat_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            monat_lbl.setStyleSheet("font-size: 10px; color: " + COLOR_TEXT_LIGHT + ";")
            monat_lbl.setFixedWidth(50)

            bar_container.addWidget(val_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            bar_container.addWidget(bar, alignment=Qt.AlignmentFlag.AlignCenter)
            bar_container.addWidget(monat_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            bars_layout.addLayout(bar_container)

        bars_layout.addStretch()
        layout.addWidget(bars_widget)


class TopArtikelWidget(QFrame):
    def __init__(self, data: list, parent=None):
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

        title = QLabel("🏆 Top Artikel")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_PRIMARY};")
        layout.addWidget(title)

        if not data:
            empty = QLabel("Noch keine Verkäufe")
            empty.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
            layout.addWidget(empty)
            return

        farben = [COLOR_SECONDARY, COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING, "#9b59b6"]
        max_u = data[0]["umsatz"] if data else 1

        for i, art in enumerate(data):
            row = QHBoxLayout()
            rang = QLabel(f"#{i+1}")
            rang.setFixedWidth(28)
            rang.setStyleSheet(f"""
                font-weight: 700; font-size: 13px;
                color: {farben[i % len(farben)]};
            """)
            name = QLabel(art["bezeichnung"][:30])
            name.setStyleSheet("font-size: 12px;")
            name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

            bar_bg = QFrame()
            bar_bg.setFixedHeight(6)
            bar_bg.setStyleSheet(f"background: #f0f2f5; border-radius: 3px;")
            bar_w = QFrame(bar_bg)
            breite = max(4, int((art["umsatz"] / max_u) * 120))
            bar_w.setFixedSize(breite, 6)
            bar_w.setStyleSheet(f"background: {farben[i % len(farben)]}; border-radius: 3px;")

            val = QLabel(f"€ {art['umsatz']:,.0f}")
            val.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLOR_PRIMARY};")
            val.setFixedWidth(80)
            val.setAlignment(Qt.AlignmentFlag.AlignRight)

            row.addWidget(rang)
            row.addWidget(name)
            bar_container = QWidget()
            bar_container.setFixedWidth(130)
            bar_container.setLayout(QVBoxLayout())
            bar_container.layout().setContentsMargins(0, 4, 0, 0)
            bar_container.layout().addWidget(bar_bg)
            row.addWidget(bar_container)
            row.addWidget(val)
            layout.addLayout(row)


class StatusVerteilungWidget(QFrame):
    def __init__(self, data: list, parent=None):
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
        title = QLabel("📦 Bestellstatus")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_PRIMARY};")
        layout.addWidget(title)

        total = sum(d["anzahl"] for d in data) or 1
        for d in data:
            farbe = STATUS_FARBEN.get(d["status"], COLOR_TEXT_LIGHT)
            row = QHBoxLayout()
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {farbe}; font-size: 16px;")
            dot.setFixedWidth(20)
            name = QLabel(d["status"])
            name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            name.setStyleSheet("font-size: 12px;")
            pct = int(d["anzahl"] / total * 100)
            val = QLabel(f"{d['anzahl']}  ({pct}%)")
            val.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_LIGHT};")
            row.addWidget(dot)
            row.addWidget(name)
            row.addWidget(val)
            layout.addLayout(row)


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

        # Auto-Refresh alle 60s
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(60_000)

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(24, 20, 24, 24)
        self.main_layout.setSpacing(20)

        # Begrüßung
        greet_row = QHBoxLayout()
        greet = QLabel("👋 Willkommen zurück!")
        greet.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        greet.setStyleSheet(f"color: {COLOR_PRIMARY};")
        sub = QLabel("Hier ist Ihre aktuelle Übersicht")
        sub.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        greet_col = QVBoxLayout()
        greet_col.setSpacing(2)
        greet_col.addWidget(greet)
        greet_col.addWidget(sub)
        greet_row.addLayout(greet_col)
        greet_row.addStretch()
        self.main_layout.addLayout(greet_row)

        # Stat-Karten
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(16)
        self.card_kunden    = StatCard("Kunden",          "-",  "👥", COLOR_INFO,     self)
        self.card_artikel   = StatCard("Artikel",          "-",  "🚲", COLOR_PRIMARY,  self)
        self.card_bestellungen = StatCard("Bestellungen",  "-",  "📦", COLOR_SUCCESS,  self)
        self.card_offen     = StatCard("Offen",            "-",  "⏳", COLOR_WARNING,  self)
        self.card_umsatz    = StatCard("Umsatz (Monat)",   "-",  "💰", COLOR_SECONDARY,self)
        self.card_lager     = StatCard("Nachbestellen",    "-",  "⚠️", COLOR_DANGER,   self)

        for card in [self.card_kunden, self.card_artikel, self.card_bestellungen,
                     self.card_offen, self.card_umsatz, self.card_lager]:
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.stats_row.addWidget(card)

        self.main_layout.addLayout(self.stats_row)

        # Diagramme (Platzhalter – werden bei refresh() befüllt)
        self.charts_row = QHBoxLayout()
        self.charts_row.setSpacing(16)
        self.main_layout.addLayout(self.charts_row)

        self.bottom_row = QHBoxLayout()
        self.bottom_row.setSpacing(16)
        self.main_layout.addLayout(self.bottom_row)
        self.main_layout.addStretch()

        # Platzhalter-Widgets
        self._chart_widget = None
        self._top_widget   = None
        self._status_widget = None

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def refresh(self):
        stats = db.get_dashboard_stats()

        self.card_kunden.update_wert(str(stats["kunden_gesamt"]))
        self.card_artikel.update_wert(str(stats["artikel_gesamt"]))
        self.card_bestellungen.update_wert(str(stats["bestellungen_gesamt"]))
        self.card_offen.update_wert(str(stats["bestellungen_offen"]))
        self.card_umsatz.update_wert(f"€ {stats['umsatz_monat']:,.0f}")
        self.card_lager.update_wert(str(stats["nachbestellen"]))

        # Charts neu aufbauen
        self._clear_layout(self.charts_row)
        self._clear_layout(self.bottom_row)

        chart = MiniChart("📈 Umsatz (letzte 6 Monate)", stats["umsatz_verlauf"])
        chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        chart.setMinimumHeight(180)
        self.charts_row.addWidget(chart, stretch=2)

        top = TopArtikelWidget(stats["top_artikel"])
        top.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.charts_row.addWidget(top, stretch=1)

        status_w = StatusVerteilungWidget(stats["status_verteilung"])
        status_w.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        status_w.setFixedWidth(260)
        self.bottom_row.addWidget(status_w)

        # Schnellinfo Lager
        if stats["nachbestellen"] > 0:
            warn = QFrame()
            warn.setStyleSheet(f"""
                background: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 10px;
                padding: 12px;
            """)
            warn_layout = QHBoxLayout(warn)
            icon = QLabel("⚠️")
            icon.setFont(QFont("Segoe UI Emoji", 18))
            msg = QLabel(
                f"<b>{stats['nachbestellen']} Artikel</b> haben den Mindestbestand unterschritten "
                "und sollten nachbestellt werden."
            )
            msg.setWordWrap(True)
            msg.setStyleSheet("color: #856404; font-size: 13px;")
            warn_layout.addWidget(icon)
            warn_layout.addWidget(msg)
            self.bottom_row.addWidget(warn)

        self.bottom_row.addStretch()
