"""
KundenWidget – Main customer management widget (the "Customers" tab).

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Display a searchable table of all customers.
  - Allow creating new customers and editing or deleting existing ones via action
    buttons in the last column.
  - Export the currently visible list to a CSV file.
  - Emit the kunden_geaendert signal after any data change so other parts of the
    application (e.g. the orders view) can react.

Dependencies:
  - database (db): all SQLite operations
  - styles: centralised colour constants
  - SBS.KundeDialog: the dialog for creating / editing a single customer
"""

import csv
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QDialog, QMessageBox, QAbstractItemView, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import database as db
from styles import COLOR_TEXT_LIGHT, COLOR_BORDER
from SBS.KundeDialog import KundeDialog


class KundenWidget(QWidget):
    """
    Main widget for the "Customers" tab.

    Displays a searchable and filterable table of all customers.
    Allows creating new customers as well as editing and deleting existing
    ones via action buttons in the last column.

    Signals:
        kunden_geaendert: Emitted after a customer is created, edited or deleted.
                          Other parts of the application (e.g. the orders view)
                          can receive this signal and update themselves.
    """

    # Define the signal: no return value (empty parentheses).
    # pyqtSignal() creates a new application-specific signal.
    kunden_geaendert = pyqtSignal()

    def __init__(self, parent=None):
        """
        Construct the KundenWidget.

        Builds the user interface and immediately loads all existing customers
        from the database.

        Args:
            parent (QWidget, optional): Parent widget.
        """
        # Initialise the parent class QWidget.
        super().__init__(parent)

        # Build the user interface.
        self._setup_ui()

        # Populate the table with current data from the database.
        self.refresh()

    def _setup_ui(self):
        """
        Create the layout of the KundenWidget:

          1. Toolbar  – search bar + "New Customer" button.
          2. Info row – shows the number of customers found.
          3. Table    – shows all customers with action buttons.
        """
        # Main layout: arrange all three areas vertically.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)  # Outer margin (left, top, right, bottom).
        layout.setSpacing(16)                       # Spacing between areas.

        # --- Toolbar ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Search bar inside a rounded frame ("pill design").
        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            background: white;
            border: 1.5px solid {COLOR_BORDER};
            border-radius: 20px;
        """)
        search_frame.setFixedHeight(40)

        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(14, 0, 14, 0)

        # Magnifying glass as a decorative text label (not a real icon widget).
        search_icon = QLabel("🔍")

        # Single-line text input for the search term.
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Kunden suchen (Name, E-Mail, Ort...)")
        self.search_edit.setFrame(False)   # Do not draw its own frame.
        self.search_edit.setStyleSheet("background: transparent; border: none; font-size: 13px;")
        # Signal: search immediately on every keystroke.
        # textChanged is a Qt signal; refresh() is the connected slot.
        self.search_edit.textChanged.connect(self.refresh)

        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_edit)
        # stretch=1: the search bar fills all available horizontal space.
        toolbar.addWidget(search_frame, stretch=1)

        # "New Customer" button.
        self.neu_btn = QPushButton("➕  Neuer Kunde")
        self.neu_btn.setObjectName("btn_primary")  # CSS class for primary colour.
        self.neu_btn.setFixedHeight(40)
        self.neu_btn.clicked.connect(self._neuer_kunde)
        toolbar.addWidget(self.neu_btn)

        # "Export CSV" button: saves the currently displayed list as a CSV file.
        csv_btn = QPushButton("📥  CSV exportieren")
        csv_btn.setObjectName("btn_icon")  # Secondary styling (grey button).
        csv_btn.setFixedHeight(40)
        csv_btn.clicked.connect(self._exportiere_csv)
        toolbar.addWidget(csv_btn)

        layout.addLayout(toolbar)

        # --- Info row ---
        # Shows e.g. "12 Customer(s) found"; updated in refresh().
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        layout.addWidget(self.info_lbl)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(9)   # 9 columns: 8 data columns + 1 action column.

        # Set column headers.
        self.table.setHorizontalHeaderLabels([
            "Nr.", "Vorname", "Nachname", "E-Mail", "Telefon",
            "PLZ", "Ort", "Erstellt", "Aktionen"
        ])

        # Every other row gets a slightly different background colour (zebra pattern).
        self.table.setAlternatingRowColors(True)

        # Clicking selects the entire row, not just one cell.
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # Table cells cannot be edited directly (only via the dialog).
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Hide row numbers on the left side (looks cleaner).
        self.table.verticalHeader().setVisible(False)

        # Hide grid lines for a modern appearance.
        self.table.setShowGrid(False)

        # All columns stretch evenly to fill the available width.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Column 0 (Nr.) adapts to its content instead of stretching.
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        # Column 8 (Actions) gets a fixed width.
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 160)

        # Row height: first row 48 px, all others 46 px.
        self.table.setRowHeight(0, 48)
        self.table.verticalHeader().setDefaultSectionSize(46)

        # Double-clicking a row opens the edit dialog.
        self.table.doubleClicked.connect(self._bearbeite_zeile)

        layout.addWidget(self.table)

    def refresh(self):
        """
        Load all customers from the database and repopulate the table.

        Takes the current text in the search field into account – the
        database function get_alle_kunden() filters server-side by name,
        email and city.

        This method is called:
          - On the first load of the widget (in the constructor),
          - On every keystroke in the search bar (signal textChanged),
          - After creating, editing or deleting a customer.
        """
        # Get the current search term from the input field.
        suche = self.search_edit.text().strip()

        # Retrieve all matching customers from the database.
        # The function returns a list of dictionaries.
        kunden = db.get_alle_kunden(suche)

        # Show the number of results in the info row.
        self.info_lbl.setText(f"{len(kunden)} Kunde(n) gefunden")

        # Adjust the number of table rows to match the number of customers found.
        self.table.setRowCount(len(kunden))

        # Fill each row with customer data.
        for row, k in enumerate(kunden):
            # Prepare the 8 data values to display as a list.
            items = [
                k.get("kundennummer", ""),
                k.get("vorname", ""),
                k.get("nachname", ""),
                k.get("email", ""),
                k.get("telefon", ""),
                k.get("plz", ""),
                k.get("ort", ""),
                # Truncate the date to the first 10 characters ("2024-01-15T..." → "2024-01-15").
                (k.get("erstellt_am", "") or "")[:10],
            ]

            # Fill each column in the current row.
            for col, text in enumerate(items):
                item = QTableWidgetItem(text or "")

                # Store the database ID invisibly in the cell (UserRole).
                # This allows reading the ID from a cell later without showing
                # it as visible text in the table.
                item.setData(Qt.ItemDataRole.UserRole, k["id"])

                # Text aligned vertically centred and left-aligned.
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, col, item)

            # --- Action buttons in the last column ---
            # Buttons are not normal table cells, so we need a separate widget
            # as a container (setCellWidget).
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(6, 4, 6, 4)
            btn_layout.setSpacing(6)

            # "Edit" button.
            edit_btn = QPushButton("✏️ Bearbeiten")
            edit_btn.setObjectName("btn_icon")
            edit_btn.setFixedHeight(30)
            # Store the customer ID as a property on the button so the slot
            # (_bearbeite_kunde) knows which customer to edit.
            edit_btn.setProperty("kunde_id", k["id"])
            edit_btn.clicked.connect(self._bearbeite_kunde)

            # "Delete" button (trash icon only, square).
            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("btn_danger")  # Red colour from CSS.
            del_btn.setFixedSize(30, 30)          # Square: 30 × 30 pixels.
            del_btn.setProperty("kunde_id", k["id"])
            del_btn.clicked.connect(self._loesche_kunde)

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)

            # Insert the button widget into column 8 (Actions) of the current row.
            self.table.setCellWidget(row, 8, btn_widget)

    def _neuer_kunde(self):
        """
        Open KundeDialog to create a new customer.

        When the dialog is confirmed with "Save" (Accepted), the form data is
        saved to the database, the table is refreshed and the kunden_geaendert
        signal is emitted.
        """
        # Open a new dialog without existing customer data.
        dlg = KundeDialog(self)

        # exec() opens the dialog and blocks until it is closed.
        # The return value indicates whether "Save" or "Cancel" was pressed.
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Write the data from the dialog to the database.
            db.speichere_kunde(dlg.result_data)
            # Reload the table so the new customer appears.
            self.refresh()
            # Notify other widgets about the change.
            self.kunden_geaendert.emit()

    def _bearbeite_zeile(self, index):
        """
        Called when the user double-clicks a table row.
        Opens KundeDialog for the customer in the clicked row.

        Args:
            index (QModelIndex): Position of the clicked cell (contains row and column).
        """
        # Get the cell in column 0 of the clicked row.
        item = self.table.item(index.row(), 0)
        if item:
            # Read the hidden customer ID from the cell (set in refresh()).
            k = db.get_kunde(item.data(Qt.ItemDataRole.UserRole))
            if k:
                # Open the dialog with the existing customer data.
                dlg = KundeDialog(self, k)
                if dlg.exec() == QDialog.DialogCode.Accepted:
                    db.speichere_kunde(dlg.result_data)
                    self.refresh()
                    self.kunden_geaendert.emit()

    def _bearbeite_kunde(self):
        """
        Slot for the "Edit" button in the action column.

        self.sender() returns the widget that emitted the signal – in this case
        the clicked Edit button.  The correct customer is loaded via the stored
        "kunde_id" property.
        """
        # Determine the widget that triggered the click (the button itself).
        btn = self.sender()

        # Read the customer ID from the button property.
        kid = btn.property("kunde_id")

        # Load the full customer data from the database.
        k = db.get_kunde(kid)
        if k:
            dlg = KundeDialog(self, k)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                db.speichere_kunde(dlg.result_data)
                self.refresh()
                self.kunden_geaendert.emit()

    def _loesche_kunde(self):
        """
        Slot for the "Delete" button in the action column.

        Shows a confirmation dialog before actually deleting the customer.
        Customers with existing orders cannot be deleted – in that case an
        error message is shown.
        """
        # The button that triggered the click and the associated customer ID.
        btn = self.sender()
        kid = btn.property("kunde_id")

        # Load the customer data to display the name in the confirmation dialog.
        k = db.get_kunde(kid)
        if not k:
            return  # Customer no longer exists – nothing to do.

        # Show a confirmation dialog with "Yes" and "No".
        # The default is "No" to prevent accidental deletion.
        reply = QMessageBox.question(
            self, "Kunden löschen",
            f"Soll <b>{k['vorname']} {k['nachname']}</b> wirklich gelöscht werden?<br>"
            "<small style='color:gray'>Kunden mit Bestellungen können nicht gelöscht werden.</small>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No   # Pre-selected default answer.
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Attempt to delete from the database; returns True if successful.
            ok = db.loesche_kunde(kid)
            if ok:
                # Refresh the table and notify other widgets.
                self.refresh()
                self.kunden_geaendert.emit()
            else:
                # Deletion not possible because the customer still has orders.
                QMessageBox.warning(
                    self, "Nicht möglich",
                    "Dieser Kunde hat noch Bestellungen und kann nicht gelöscht werden."
                )

    def _exportiere_csv(self):
        """
        Export all currently displayed customers as a CSV file.

        The user selects the save location and file name via a file dialog.
        The CSV file contains all customer columns and is saved with a semicolon
        delimiter so it can be opened directly in German Excel.

        The current search filter is taken into account – only the customers
        currently visible in the table are exported.
        """
        # Open the file save dialog; returns the chosen path (or empty string if cancelled).
        pfad, _ = QFileDialog.getSaveFileName(
            self,                       # Parent window.
            "Kunden exportieren",       # Window title.
            "kunden_export.csv",        # Suggested file name.
            "CSV-Dateien (*.csv)"       # File type filter.
        )
        # If no path was chosen (Cancel pressed), do nothing.
        if not pfad:
            return

        # Load the current customers with the active search filter from the database.
        kunden = db.get_alle_kunden(self.search_edit.text().strip())

        try:
            # Open the file for writing.
            # newline="" is required for csv.writer on Windows (prevents double line breaks).
            # encoding="utf-8-sig" adds a BOM marker so Excel displays umlauts correctly.
            with open(pfad, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")

                # Write the header row with column names.
                writer.writerow([
                    "Kundennummer", "Vorname", "Nachname", "E-Mail",
                    "Telefon", "Straße", "PLZ", "Ort", "Land",
                    "Geburtsdatum", "Erstellt am"
                ])

                # Write one row per customer.
                for k in kunden:
                    writer.writerow([
                        k.get("kundennummer", ""),
                        k.get("vorname", ""),
                        k.get("nachname", ""),
                        k.get("email", ""),
                        k.get("telefon", ""),
                        k.get("strasse", ""),
                        k.get("plz", ""),
                        k.get("ort", ""),
                        k.get("land", ""),
                        k.get("geburtsdatum", ""),
                        # Truncate the date to the first 10 characters (remove time part).
                        (k.get("erstellt_am", "") or "")[:10],
                    ])

            # Show a success message with the number of exported records.
            QMessageBox.information(
                self, "Export erfolgreich",
                f"{len(kunden)} Kunde(n) wurden exportiert nach:\n{pfad}"
            )

        except Exception as fehler:
            # Show an error message if writing failed (e.g. no write permission,
            # file already open).
            QMessageBox.warning(self, "Fehler beim Export", str(fehler))
