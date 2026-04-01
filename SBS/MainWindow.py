"""
MainWindow – Application main window.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Build the overall layout (Sidebar + content area).
  - Navigate between pages via a QStackedWidget.
  - Lazy-load page widgets only on first visit to avoid long startup times.
  - Keep the status bar updated with live statistics from the database.

Dependencies:
  - database (db): all SQLite operations
  - styles: centralised colour constants (MAIN_STYLE applied at app level)
  - SBS.Sidebar: left navigation panel
  - SBS.PageHeader: header bar for each content page
"""

import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QStackedWidget, QStatusBar, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

import database as db
from SBS.Sidebar import Sidebar
from SBS.PageHeader import PageHeader


class MainWindow(QMainWindow):
    """
    Main window of the application.

    Responsible for:
    - Building the overall layout (Sidebar + content area).
    - Navigation between pages via QStackedWidget.
    - Lazy loading: page widgets are only loaded on their first visit.
    - Status bar with real-time statistics from the database.
    """

    def __init__(self):
        """
        Initialise the main window, set the window title, minimum size
        and centre it on screen.
        """
        super().__init__()

        # Title bar of the operating system window.
        self.setWindowTitle("Radsport Koch GmbH – Verwaltungssystem")

        # Set the window icon (shown in the title bar).
        # os.path.dirname(__file__) returns the directory of this script file,
        # so the icon is found regardless of the working directory.
        icon_pfad = os.path.join(os.path.dirname(__file__), "..", "assets", "app_icon.png")
        self.setWindowIcon(QIcon(icon_pfad))

        # Minimum size: the app should not become smaller than 1280×780 pixels.
        self.setMinimumSize(1280, 780)

        # Initial window size when first opened.
        self.resize(1400, 860)

        # Start centred.
        # primaryScreen().geometry() returns the resolution of the primary screen.
        screen = QApplication.primaryScreen().geometry()
        self.move(
            # X position: centre of the screen minus half the window width.
            (screen.width() - self.width()) // 2,
            # Y position: centre of the screen minus half the window height.
            (screen.height() - self.height()) // 2
        )

        # Build the user interface.
        self._setup_ui()

        # Show the Dashboard (index 0) immediately on startup.
        self._navigate(0)

    def _setup_ui(self):
        """
        Build the entire main UI:
        - Central widget with a horizontal layout.
        - Sidebar on the left.
        - Content area on the right with a QStackedWidget for the pages.
        - Status bar at the bottom.
        """
        # The central widget is the content container of QMainWindow.
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout: sidebar and content area side by side.
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)  # No outer margin.
        main_layout.setSpacing(0)                    # No gap between sidebar and content.

        # ── Sidebar ───────────────────────────────────────────────────────────
        self.sidebar = Sidebar()

        # Connect each sidebar button to the _navigate method.
        # lambda: … ensures the index is only passed when the button is clicked.
        self.sidebar.btn_dashboard.clicked.connect(lambda: self._navigate(0))
        self.sidebar.btn_kunden.clicked.connect(lambda: self._navigate(1))
        self.sidebar.btn_artikel.clicked.connect(lambda: self._navigate(2))
        self.sidebar.btn_bestellungen.clicked.connect(lambda: self._navigate(3))
        main_layout.addWidget(self.sidebar)

        # ── Content area ──────────────────────────────────────────────────────
        content_frame = QFrame()
        content_frame.setObjectName("content_area")  # For stylesheet targeting.
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # ── Page stack ────────────────────────────────────────────────────────
        # QStackedWidget: shows only one page at a time.
        # Switching pages is done with setCurrentIndex().
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: #f0f2f5; }")

        # Lazy loading:
        # _pages stores the layout of each page so that the actual content widget
        # can be added dynamically on the first visit.
        self._pages = {}

        # Configuration of all pages: (title, subtitle).
        self._page_configs = [
            ("🏠 Dashboard",    "Aktuelle Übersicht & Statistiken"),
            ("👥 Kunden",       "Kundenstammdaten verwalten"),
            ("🚲 Artikel",      "Produktkatalog & Lager"),
            ("📦 Bestellungen", "Auftragsverwaltung"),
        ]

        # For each page: create a wrapper widget + header and add it to the stack.
        for i, (title, subtitle) in enumerate(self._page_configs):
            # The wrapper widget contains the header at the top and (later) the
            # content widget below.
            wrapper = QWidget()
            wrapper.setObjectName("page_wrapper")
            wrapper.setStyleSheet("QWidget#page_wrapper { background: #f0f2f5; }")

            w_layout = QVBoxLayout(wrapper)
            w_layout.setContentsMargins(0, 0, 0, 0)
            w_layout.setSpacing(0)

            # Add the page header (title + subtitle) immediately.
            header = PageHeader(title, subtitle)
            w_layout.addWidget(header)

            self.stack.addWidget(wrapper)

            # Store the layout under key i – on the first visit the actual page
            # widget will be appended here (lazy loading).
            self._pages[i] = w_layout

        content_layout.addWidget(self.stack)

        # The content area takes up all remaining horizontal space (stretch=1).
        main_layout.addWidget(content_frame, stretch=1)

        # ── Status bar ────────────────────────────────────────────────────────
        status = QStatusBar()
        status.setFixedHeight(26)  # Compact height for the status bar.
        self.setStatusBar(status)
        self._status_bar = status

        # Populate the status bar immediately with database values at startup.
        self._update_status()

    def _navigate(self, index: int):
        """
        Switch to the page with the given index.

        On the first visit to a page, the corresponding widget is dynamically
        imported and added to the layout (lazy loading).  This avoids long
        startup times because not all modules are loaded immediately.

        :param index: 0 = Dashboard, 1 = Customers, 2 = Articles, 3 = Orders
        """
        # Update the active button in the sidebar.
        self.sidebar.set_active(index)

        # Switch the visible page in the stack.
        self.stack.setCurrentIndex(index)

        # Lazy load the actual widgets.
        layout = self._pages[index]

        # layout.count() == 1 means: only the header has been added so far.
        # The actual content widget is missing → load it now.
        if layout.count() == 1:  # Only the header is present.
            if index == 0:
                # Import the dashboard module only now.
                from SBS.DashboardWidget import DashboardWidget
                w = DashboardWidget()
            elif index == 1:
                from SBS.KundenWidget import KundenWidget
                w = KundenWidget()
                # Signal: when customer data changes, update the status bar.
                w.kunden_geaendert.connect(self._update_status)
            elif index == 2:
                from SBS.ArtikelWidget import ArtikelWidget
                w = ArtikelWidget()
                # Signal: when article data changes, update the status bar.
                w.artikel_geaendert.connect(self._update_status)
            elif index == 3:
                from SBS.BestellungenWidget import BestellungenWidget
                w = BestellungenWidget()
                # Update the status bar and dashboard when orders change.
                w.bestellungen_geaendert.connect(self._update_status)
                w.bestellungen_geaendert.connect(self._refresh_dashboard)
            else:
                return  # Unknown index – do nothing.

            # Add the newly created widget to the page layout.
            layout.addWidget(w)

        # Update the status bar after every page switch.
        self._update_status()

    def _update_status(self):
        """
        Read current statistics from the database and display them in the
        status bar at the bottom of the window.
        """
        # Database query: returns a dictionary with KPIs.
        stats = db.get_dashboard_stats()

        # Build the status bar text from the KPIs.
        self._status_bar.showMessage(
            f"  👥 {stats['kunden_gesamt']} Kunden  "
            f"·  🚲 {stats['artikel_gesamt']} Artikel  "
            f"·  📦 {stats['bestellungen_gesamt']} Bestellungen  "
            f"·  💰 Umsatz gesamt: € {stats['umsatz_gesamt']:,.2f}  "
            f"·  ⏳ {stats['bestellungen_offen']} offen"
        )

    def _refresh_dashboard(self):
        """
        Refresh the dashboard widget if it has already been loaded.

        Called when order data changes, so the dashboard statistics remain
        up to date.
        """
        # Get the layout of page 0 (Dashboard).
        layout = self._pages[0]

        # layout.count() > 1: the dashboard widget has already been loaded
        # (lazy load has happened).
        if layout.count() > 1:
            # The second element in the layout is the actual dashboard widget (index 1).
            w = layout.itemAt(1).widget()

            # Safety check: does the widget have a refresh() method?
            if hasattr(w, "refresh"):
                w.refresh()  # Reload the dashboard content.
