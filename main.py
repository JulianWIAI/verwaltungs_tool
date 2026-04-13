"""
Radsport Koch GmbH – Application entry point
=============================================
This is the sole entry point of the application.
All UI classes live in the SBS package; this file only bootstraps PyQt6,
sets the application icon, applies the global stylesheet, initialises the
database, and starts the event loop.
"""

import sys
import os
import ctypes                          # Windows API – needed for the taskbar icon fix.
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

# Ensure the project root is on sys.path so that the root-level modules
# (database, styles) are importable from every SBS submodule.
sys.path.insert(0, os.path.dirname(__file__))

import database as db                  # Data-access layer (SQLite).
from styles import MAIN_STYLE          # Global Qt stylesheet.
from SBS.MainWindow import MainWindow  # Application main window.


def main():
    """
    Bootstrap the application.

    Creates the QApplication, sets the taskbar icon, applies the stylesheet,
    initialises the database, opens the main window and starts the Qt event loop.
    """
    # Windows taskbar icon fix:
    # Without an explicit AppUserModelID, Windows groups the process under the
    # Python interpreter icon.  Assigning a unique ID makes Windows use the
    # Qt window icon in the taskbar and Alt-Tab dialog instead.

    # Check if the operating system is Windows before calling windll
    if sys.platform == 'win32':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "RadsportKoch.Verwaltungssystem.1"
        )

    # QApplication must be the very first Qt object created.
    app = QApplication(sys.argv)
    app.setApplicationName("Radsport Koch GmbH")
    app.setApplicationVersion("1.0.0")

    # Set the application-wide icon from the assets folder.
    # Setting it on QApplication (not just the window) ensures Windows picks it
    # up for the taskbar button.
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "app_icon.png")
    app.setWindowIcon(QIcon(icon_path))

    # Apply the centralised Qt stylesheet to every widget in the application.
    app.setStyleSheet(MAIN_STYLE)

    # Initialise the database (creates tables from data/schema.sql on first run).
    db.init_db()

    # Create and show the main window.
    window = MainWindow()
    window.show()

    # Hand control to the Qt event loop; exit with Qt's return code.
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
