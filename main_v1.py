"""
Radsport Koch GmbH – Hauptfenster
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QStatusBar,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor

# Projektpfad
sys.path.insert(0, os.path.dirname(__file__))

import database as db
from styles import MAIN_STYLE, COLOR_PRIMARY, COLOR_SECONDARY, COLOR_WHITE, COLOR_TEXT_LIGHT


class NavButton(QPushButton):
    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(f"  {icon}  {text}", parent)
        self.setObjectName("nav_btn")
        self.setCheckable(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(46)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_active(self, active: bool):
        self.setObjectName("nav_btn_active" if active else "nav_btn")
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo-Bereich
        logo_frame = QFrame()
        logo_frame.setStyleSheet(f"""
            background: rgba(0,0,0,0.2);
            border-bottom: 1px solid rgba(255,255,255,0.08);
        """)
        logo_frame.setFixedHeight(88)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(16, 12, 16, 12)
        logo_layout.setSpacing(2)

        bike_icon = QLabel("🚲")
        bike_icon.setFont(QFont("Segoe UI Emoji", 22))
        bike_icon.setStyleSheet("color: white;")

        title = QLabel("Radsport Koch")
        title.setObjectName("sidebar_title")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))

        subtitle = QLabel("GmbH · Verwaltungssystem")
        subtitle.setObjectName("sidebar_subtitle")

        logo_layout.addWidget(bike_icon)
        logo_layout.addWidget(title)
        logo_layout.addWidget(subtitle)
        layout.addWidget(logo_frame)

        # Navigations-Sektion
        layout.addSpacing(12)
        nav_label = QLabel("  NAVIGATION")
        nav_label.setStyleSheet("""
            color: rgba(255,255,255,0.35);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 0 16px;
        """)
        layout.addWidget(nav_label)
        layout.addSpacing(4)

        self.btn_dashboard   = NavButton("🏠", "Dashboard")
        self.btn_kunden      = NavButton("👥", "Kunden")
        self.btn_artikel     = NavButton("🚲", "Artikel")
        self.btn_bestellungen = NavButton("📦", "Bestellungen")

        self.nav_buttons = [
            self.btn_dashboard,
            self.btn_kunden,
            self.btn_artikel,
            self.btn_bestellungen,
        ]

        for btn in self.nav_buttons:
            layout.addWidget(btn)

        layout.addStretch()

        # Footer
        footer = QFrame()
        footer.setStyleSheet("border-top: 1px solid rgba(255,255,255,0.08);")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        footer_layout.setSpacing(2)

        version = QLabel("v1.0.0 · 2025")
        version.setStyleSheet("color: rgba(255,255,255,0.35); font-size: 10px;")
        copy = QLabel("© Radsport Koch GmbH")
        copy.setStyleSheet("color: rgba(255,255,255,0.25); font-size: 10px;")

        footer_layout.addWidget(version)
        footer_layout.addWidget(copy)
        layout.addWidget(footer)

    def set_active(self, index: int):
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == index)


class PageHeader(QFrame):
    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("page_header")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 14, 24, 14)
        layout.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("page_title")
        t.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("page_subtitle")
            layout.addWidget(s)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Radsport Koch GmbH – Verwaltungssystem")
        self.setMinimumSize(1280, 780)
        self.resize(1400, 860)

        # Zentriert starten
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

        self._setup_ui()
        self._navigate(0)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.btn_dashboard.clicked.connect(lambda: self._navigate(0))
        self.sidebar.btn_kunden.clicked.connect(lambda: self._navigate(1))
        self.sidebar.btn_artikel.clicked.connect(lambda: self._navigate(2))
        self.sidebar.btn_bestellungen.clicked.connect(lambda: self._navigate(3))
        main_layout.addWidget(self.sidebar)

        # Content
        content_frame = QFrame()
        content_frame.setObjectName("content_area")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Page Stack
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: #f0f2f5;")

        # Seiten lazy laden
        self._pages = {}
        self._page_configs = [
            ("🏠 Dashboard",    "Aktuelle Übersicht & Statistiken"),
            ("👥 Kunden",       "Kundenstammdaten verwalten"),
            ("🚲 Artikel",      "Produktkatalog & Lager"),
            ("📦 Bestellungen", "Auftragsverwaltung"),
        ]

        for i, (title, subtitle) in enumerate(self._page_configs):
            wrapper = QWidget()
            wrapper.setStyleSheet("background: #f0f2f5;")
            w_layout = QVBoxLayout(wrapper)
            w_layout.setContentsMargins(0, 0, 0, 0)
            w_layout.setSpacing(0)
            header = PageHeader(title, subtitle)
            w_layout.addWidget(header)
            self.stack.addWidget(wrapper)
            self._pages[i] = w_layout  # Layouts speichern

        content_layout.addWidget(self.stack)
        main_layout.addWidget(content_frame, stretch=1)

        # Statusbar
        status = QStatusBar()
        status.setFixedHeight(26)
        self.setStatusBar(status)
        self._status_bar = status
        self._update_status()

    def _navigate(self, index: int):
        self.sidebar.set_active(index)
        self.stack.setCurrentIndex(index)

        # Lazy Load der eigentlichen Widgets
        layout = self._pages[index]
        if layout.count() == 1:  # Nur Header vorhanden
            if index == 0:
                from dashboard import DashboardWidget
                w = DashboardWidget()
            elif index == 1:
                from kunden import KundenWidget
                w = KundenWidget()
                w.kunden_geaendert.connect(self._update_status)
            elif index == 2:
                from artikel import ArtikelWidget
                w = ArtikelWidget()
                w.artikel_geaendert.connect(self._update_status)
            elif index == 3:
                from bestellungen import BestellungenWidget
                w = BestellungenWidget()
                w.bestellungen_geaendert.connect(self._update_status)
                w.bestellungen_geaendert.connect(self._refresh_dashboard)
            else:
                return
            layout.addWidget(w)
        self._update_status()

    def _update_status(self):
        stats = db.get_dashboard_stats()
        self._status_bar.showMessage(
            f"  👥 {stats['kunden_gesamt']} Kunden  "
            f"·  🚲 {stats['artikel_gesamt']} Artikel  "
            f"·  📦 {stats['bestellungen_gesamt']} Bestellungen  "
            f"·  💰 Umsatz gesamt: € {stats['umsatz_gesamt']:,.2f}  "
            f"·  ⏳ {stats['bestellungen_offen']} offen"
        )

    def _refresh_dashboard(self):
        layout = self._pages[0]
        if layout.count() > 1:
            w = layout.itemAt(1).widget()
            if hasattr(w, "refresh"):
                w.refresh()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Radsport Koch GmbH")
    app.setApplicationVersion("1.0.0")
    app.setStyleSheet(MAIN_STYLE)

    # Datenbank initialisieren
    db.init_db()

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
