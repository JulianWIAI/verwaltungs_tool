"""
Sidebar – Left-hand navigation panel of the application.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Display the company logo, name and slogan.
  - Provide four NavButtons for the main pages (Dashboard, Customers, Articles, Orders).
  - Highlight the button that corresponds to the currently visible page.
  - Show a version and copyright footer at the bottom.

Dependencies:
  - styles: centralised colour constants
  - SBS.NavButton: the individual navigation button widget
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from SBS.NavButton import NavButton


class Sidebar(QFrame):
    """
    Left navigation panel of the application.

    Contains:
    - Logo area with company name and icon.
    - Section label "NAVIGATION".
    - Four NavButtons for the individual pages.
    - Footer with version and copyright information.
    """

    def __init__(self, parent=None):
        """
        Build the sidebar completely.

        :param parent: Optional parent widget (normally the MainWindow)
        """
        # Call the QFrame constructor.
        super().__init__(parent)

        # Object name for the stylesheet (colours the sidebar background).
        self.setObjectName("sidebar")

        # Vertical main layout with no margins and no row spacing.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Logo area ─────────────────────────────────────────────────────────
        logo_frame = QFrame()
        # Slightly darkened background with a thin separator line at the bottom.
        logo_frame.setStyleSheet(f"""
            background: rgba(0,0,0,0.2);
            border-bottom: 1px solid rgba(255,255,255,0.08);
        """)
        logo_frame.setMinimumHeight(100)  # Minimum height of the logo area.

        # Horizontal layout inside the logo frame.
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(14, 14, 14, 14)  # Padding: top/right/bottom/left
        logo_layout.setSpacing(10)  # Space between icon and text block.

        # Bicycle emoji used as a visual company logo.
        bike_icon = QLabel("🚲")
        bike_icon.setFont(QFont("Segoe UI Emoji", 26))  # Emoji font, size 26.
        bike_icon.setStyleSheet("color: white;")
        bike_icon.setFixedSize(40, 40)   # Square placeholder for the icon.
        bike_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Vertical column for company name and subtitle.
        text_col = QVBoxLayout()
        text_col.setSpacing(2)  # Only 2 px between the two labels.

        # Company name in bold.
        title = QLabel("Radsport Koch")
        title.setObjectName("sidebar_title")  # Used for stylesheet targeting.
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))

        # Subtitle with legal suffix and system name.
        subtitle = QLabel("GmbH · Verwaltungssystem")
        subtitle.setObjectName("sidebar_subtitle")
        subtitle.setWordWrap(True)  # Allow line wrapping if width is too small.

        text_col.addWidget(title)
        text_col.addWidget(subtitle)

        # Combine icon and text block horizontally.
        logo_layout.addWidget(bike_icon)
        logo_layout.addLayout(text_col)
        layout.addWidget(logo_frame)  # Add logo area to the main layout.

        # ── Navigation section ────────────────────────────────────────────────
        layout.addSpacing(12)  # Small gap between logo and section label.

        # Section label "NAVIGATION" in uppercase, semi-transparent.
        nav_label = QLabel("  NAVIGATION")
        nav_label.setStyleSheet("""
            color: rgba(255,255,255,0.35);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 0 16px;
        """)
        layout.addWidget(nav_label)
        layout.addSpacing(4)  # Small gap between label and the first button.

        # The four navigation buttons are stored as instance variables so that
        # MainWindow can connect their clicked signals.
        self.btn_dashboard    = NavButton("🏠", "Dashboard")
        self.btn_kunden       = NavButton("👥", "Kunden")
        self.btn_artikel      = NavButton("🚲", "Artikel")
        self.btn_bestellungen = NavButton("📦", "Bestellungen")

        # List of all nav buttons – handy for iteration (e.g. set_active).
        self.nav_buttons = [
            self.btn_dashboard,
            self.btn_kunden,
            self.btn_artikel,
            self.btn_bestellungen,
        ]

        # Add all buttons to the layout.
        for btn in self.nav_buttons:
            layout.addWidget(btn)

        # Stretch pushes the footer to the bottom of the sidebar.
        layout.addStretch()

        # ── Footer ────────────────────────────────────────────────────────────
        footer = QFrame()
        # Thin separator line at the top of the footer area.
        footer.setStyleSheet("border-top: 1px solid rgba(255,255,255,0.08);")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        footer_layout.setSpacing(2)

        # Version information.
        version = QLabel("v1.0.0 · 2025")
        version.setStyleSheet("color: rgba(255,255,255,0.35); font-size: 10px;")

        # Copyright notice.
        copy = QLabel("© Radsport Koch GmbH")
        copy.setStyleSheet("color: rgba(255,255,255,0.25); font-size: 10px;")

        footer_layout.addWidget(version)
        footer_layout.addWidget(copy)
        layout.addWidget(footer)  # Footer at the very bottom of the sidebar.

    def set_active(self, index: int):
        """
        Mark the button at the given position as active and all others as inactive.

        :param index: Index of the currently active button (0 = Dashboard, …)
        """
        # Iterate over all buttons and activate or deactivate each one.
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == index)  # True only for the button with the matching index.
