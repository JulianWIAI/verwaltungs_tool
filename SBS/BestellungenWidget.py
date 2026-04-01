"""
BestellungenWidget – Main order management widget (the "Orders" tab).

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Display all orders in a searchable and filterable table.
  - Allow viewing, editing and deleting orders via action buttons per row.
  - Allow creating new orders via the "New Order" button.
  - Export the currently visible list to a CSV file.
  - Emit the bestellungen_geaendert signal after any data change so the
    dashboard can refresh its statistics.

Dependencies:
  - database (db): all SQLite operations
  - styles: centralised colour constants and STATUS_FARBEN / ZAHLUNG_FARBEN mappings
  - SBS.BestellungDialog: modal dialog for creating / editing an order
  - SBS.BestellungDetailDialog: read-only order detail view with quick status update
"""

import csv
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QDialog, QComboBox, QMessageBox, QAbstractItemView, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal

import database as db
from styles import (
    COLOR_TEXT_LIGHT, COLOR_BORDER, STATUS_FARBEN, ZAHLUNG_FARBEN
)
from SBS.BestellungDialog import BestellungDialog
from SBS.BestellungDetailDialog import BestellungDetailDialog


class BestellungenWidget(QWidget):
    """
    Main widget for the orders overview.

    Displays all orders in a table with search and filter functions.
    Each order can be viewed, edited or deleted via action buttons in the
    last column.  New orders can be created via the "New Order" button.

    The bestellungen_geaendert signal is emitted when the data set changes
    (e.g. for dashboard updates).
    """

    # Signal for parent widgets (e.g. Dashboard) that need to be notified
    # of changes to the order data.
    bestellungen_geaendert = pyqtSignal()

    def __init__(self, parent=None):
        """
        Construct the widget: build the UI and immediately load current order data.

        Parameters:
            parent: Parent widget (or None).
        """
        super().__init__(parent)
        self._setup_ui()    # Build the interface.
        self.refresh()      # Load data and populate the table.

    def _setup_ui(self):
        """
        Create the user interface of the orders main widget.

        Structure:
          1. Toolbar: search field + status filter + "New Order" button.
          2. Info row: number of orders + total revenue.
          3. Table: all filtered orders with action buttons.
        """
        # Main layout with margins.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # --- Toolbar ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Search field in a rounded frame.
        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            background: white;
            border: 1.5px solid {COLOR_BORDER};
            border-radius: 20px;
        """)
        search_frame.setFixedHeight(40)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(14, 0, 14, 0)
        search_layout.addWidget(QLabel("🔍"))   # Magnifying glass emoji as visual icon.

        # Single-line text input for the search.
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Bestellungen suchen (Nummer, Kunde...)")
        self.search_edit.setFrame(False)
        self.search_edit.setStyleSheet("background: transparent; border: none; font-size: 13px;")
        # Every keystroke immediately triggers a table refresh.
        self.search_edit.textChanged.connect(self.refresh)
        search_layout.addWidget(self.search_edit)
        # The search field should take up most of the space (stretch=1).
        toolbar.addWidget(search_frame, stretch=1)

        # Status filter: shows only orders with the selected status.
        self.status_filter = QComboBox()
        self.status_filter.setFixedHeight(40)
        self.status_filter.addItem("Alle Status", "")   # No filter.
        for s in ["Neu","In Bearbeitung","Versendet","Geliefert","Storniert","Zurückgegeben"]:
            # userData = the status string that is passed to the DB query.
            self.status_filter.addItem(s, s)
        # Filter change → reload the table.
        self.status_filter.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.status_filter)

        # Button for a new order.
        neu_btn = QPushButton("➕  Neue Bestellung")
        neu_btn.setObjectName("btn_primary")
        neu_btn.setFixedHeight(40)
        neu_btn.clicked.connect(self._neue_bestellung)
        toolbar.addWidget(neu_btn)

        # "Export CSV" button: saves the currently filtered order list as a CSV file.
        csv_btn = QPushButton("📥  CSV exportieren")
        csv_btn.setObjectName("btn_icon")  # Secondary styling.
        csv_btn.setFixedHeight(40)
        csv_btn.clicked.connect(self._exportiere_csv)
        toolbar.addWidget(csv_btn)

        layout.addLayout(toolbar)

        # --- Info row: shows count and total revenue of the filtered orders ---
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        layout.addWidget(self.info_lbl)

        # --- Main table ---
        self.table = QTableWidget()
        self.table.setColumnCount(10)   # 10 columns in total.
        self.table.setHorizontalHeaderLabels([
            "Best.-Nr.", "Datum", "Kunde", "Positionen",
            "Netto", "Brutto", "Status", "Zahlung", "Zahlstatus", "Aktionen"
        ])
        self.table.setAlternatingRowColors(True)
        # Clicking selects the entire row (not just one cell).
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        # User may not directly edit cells.
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # Column widths: default = stretched.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Individual columns adapted to their content.
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        # Actions column (index 9) gets a fixed width for the three buttons.
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(9, 200)

        # Uniform row height of 46 pixels.
        self.table.verticalHeader().setDefaultSectionSize(46)

        # Double-clicking a row opens the detail dialog.
        self.table.doubleClicked.connect(self._detail_zeile)
        layout.addWidget(self.table)

    def refresh(self):
        """
        Load all orders from the database (filtered by search text and status filter)
        and repopulate the table.

        Called:
          - On the first load of the widget.
          - After every change to the search text or status filter.
          - After saving, editing or deleting an order.
        """
        # Read the current search text and selected status filter.
        suche = self.search_edit.text().strip()
        status = self.status_filter.currentData()

        # Load orders from the database (the DB function handles filtering).
        bestellungen = db.get_alle_bestellungen(suche, status)

        # Calculate the total revenue of all displayed orders.
        # "or 0" prevents errors if the value is None (NULL in the database).
        gesamt = sum(b.get("gesamtbetrag_brutto") or 0 for b in bestellungen)
        self.info_lbl.setText(
            f"{len(bestellungen)} Bestellung(en) · Gesamtumsatz: € {gesamt:,.2f}"
        )

        # Set the table to the correct number of rows.
        self.table.setRowCount(len(bestellungen))

        for row, b in enumerate(bestellungen):
            # --- Text columns (0–5) ---
            items = [
                b.get("bestellnummer",""),
                str(b.get("bestelldatum",""))[:10],    # Date only, no time.
                b.get("kunde_name",""),
                str(b.get("anzahl_positionen",0)),     # Number of positions.
                f"€ {b.get('gesamtbetrag_netto', 0):.2f}",
                f"€ {b.get('gesamtbetrag_brutto', 0):.2f}",
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text or "")
                # Store the order ID as invisible "UserRole" data so we know
                # which order is meant when a row is clicked.
                item.setData(Qt.ItemDataRole.UserRole, b["id"])
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, col, item)

            # --- Column 6: Status badge ---
            # Get the status colour from the mapping (fallback: grey).
            status_farbe = STATUS_FARBEN.get(b["status"], "#666")
            status_lbl = QLabel(b.get("status",""))
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_lbl.setStyleSheet(f"""
                background: {status_farbe}22;
                color: {status_farbe};
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
                margin: 6px 8px;
            """)
            # "22" at the end of the colour code = hex value for ~13% alpha transparency
            # (semi-transparent background in the status colour).
            self.table.setCellWidget(row, 6, status_lbl)

            # --- Column 7: Payment method ---
            za_lbl = QLabel(b.get("zahlungsart",""))
            za_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            za_lbl.setStyleSheet("font-size: 12px; color: " + COLOR_TEXT_LIGHT + "; margin: 6px 4px;")
            self.table.setCellWidget(row, 7, za_lbl)

            # --- Column 8: Payment status badge ---
            z_farbe = ZAHLUNG_FARBEN.get(b["zahlungsstatus"], "#666")
            z_lbl = QLabel(b.get("zahlungsstatus",""))
            z_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            z_lbl.setStyleSheet(f"""
                background: {z_farbe}22;
                color: {z_farbe};
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
                margin: 6px 8px;
            """)
            self.table.setCellWidget(row, 8, z_lbl)

            # --- Column 9: Action buttons ---
            # A container widget with three buttons side by side.
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            # "Details" button opens the detail dialog.
            detail_btn = QPushButton("🔍 Details")
            detail_btn.setObjectName("btn_icon")
            detail_btn.setFixedHeight(30)
            # Store the order ID as a property so the slot knows which order is meant.
            detail_btn.setProperty("bid", b["id"])
            detail_btn.clicked.connect(self._zeige_detail)

            # "Edit" button opens the edit dialog.
            edit_btn = QPushButton("✏️")
            edit_btn.setObjectName("btn_icon")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setProperty("bid", b["id"])
            edit_btn.clicked.connect(self._bearbeite_bestellung)

            # "Delete" button with red highlighting (btn_danger).
            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("btn_danger")
            del_btn.setFixedSize(30, 30)
            del_btn.setProperty("bid", b["id"])
            del_btn.clicked.connect(self._loesche_bestellung)

            btn_layout.addWidget(detail_btn)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            # Insert the button container as a widget into the table cell.
            self.table.setCellWidget(row, 9, btn_widget)

    def _neue_bestellung(self):
        """
        Slot: Open BestellungDialog in "New" mode.

        If the user confirms the dialog with "Save" (returns Accepted), the
        order is created in the database, the table is refreshed and the
        bestellungen_geaendert signal is emitted.
        """
        # Open the dialog without an order dict → New mode.
        dlg = BestellungDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Save the order with header data and positions to the database.
            db.speichere_bestellung(dlg.result_data, dlg.result_positionen)
            self.refresh()                      # Reload the table.
            self.bestellungen_geaendert.emit()  # Notify the dashboard.

    def _detail_zeile(self, index):
        """
        Slot: Triggered when the user double-clicks a table row.

        Reads the order ID from the clicked cell (UserRole data) and opens
        the detail dialog for that order.

        Parameters:
            index: QModelIndex – gives the row and column of the double-click.
        """
        # Read the cell in column 0 of the clicked row.
        item = self.table.item(index.row(), 0)
        if item:
            # Get the stored order ID from the UserRole data.
            bid = item.data(Qt.ItemDataRole.UserRole)
            dlg = BestellungDetailDialog(self, bid)
            # If the status is changed in the dialog, refresh the table.
            dlg.status_geaendert.connect(self.refresh)
            dlg.exec()

    def _zeige_detail(self):
        """
        Slot: Called when the "Details" button of a row is clicked.

        Reads the order ID from the "bid" property of the button and opens
        the detail dialog.
        """
        # Get the button that emitted the signal and read its property.
        bid = self.sender().property("bid")
        dlg = BestellungDetailDialog(self, bid)
        # Status change in the dialog → refresh the table AND the dashboard.
        dlg.status_geaendert.connect(self.refresh)
        dlg.status_geaendert.connect(self.bestellungen_geaendert)
        dlg.exec()

    def _bearbeite_bestellung(self):
        """
        Slot: Open BestellungDialog in "Edit" mode for the order whose "Edit"
        button was clicked.

        First loads the full order data from the database and passes it to the
        dialog.  If confirmed, the changed data is saved.
        """
        # Read the order ID from the button property.
        bid = self.sender().property("bid")
        # Load the full order data from the database.
        b = db.get_bestellung(bid)
        if b:
            # Open the dialog in edit mode (with pre-filled data).
            dlg = BestellungDialog(self, b)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                # Save the changed data to the database.
                db.speichere_bestellung(dlg.result_data, dlg.result_positionen)
                self.refresh()
                self.bestellungen_geaendert.emit()

    def _loesche_bestellung(self):
        """
        Slot: Delete an order after confirmation by the user.

        Shows a confirmation dialog with the order name first.  Only if the
        user confirms with "Yes" is the order actually deleted from the database.
        """
        # Read the order ID from the button property.
        bid = self.sender().property("bid")
        # Load the order data to display its name in the dialog.
        b = db.get_bestellung(bid)
        if not b:
            return   # Order no longer exists – nothing to do.

        # Confirmation dialog with "Yes"/"No" selection.
        reply = QMessageBox.question(
            self, "Bestellung löschen",
            f"Bestellung <b>{b['bestellnummer']}</b> von <b>{b['kunde_name']}</b> löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No   # Default selection: No (for safety).
        )

        # Only delete if the user explicitly clicked "Yes".
        if reply == QMessageBox.StandardButton.Yes:
            db.loesche_bestellung(bid)          # Remove the database row.
            self.refresh()                       # Reload the table.
            self.bestellungen_geaendert.emit()   # Notify the dashboard.

    def _exportiere_csv(self):
        """
        Export all currently displayed orders as a CSV file.

        The current search text and the selected status filter are taken into
        account – only the orders currently visible in the table are exported.

        The file is saved with a semicolon delimiter and UTF-8 BOM encoding so
        that Excel displays umlauts correctly.
        """
        # Open the file save dialog.
        pfad, _ = QFileDialog.getSaveFileName(
            self,
            "Bestellungen exportieren",
            "bestellungen_export.csv",
            "CSV-Dateien (*.csv)"
        )
        if not pfad:
            return  # Cancel pressed – do nothing.

        # Read the current filters from the toolbar (same logic as in refresh()).
        suche = self.search_edit.text().strip()
        status = self.status_filter.currentData()

        # Load orders with the same filters as shown in the table.
        bestellungen = db.get_alle_bestellungen(suche, status)

        try:
            with open(pfad, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")

                # Write the header row with all column names.
                writer.writerow([
                    "Bestellnummer", "Datum", "Kunde", "Anzahl Positionen",
                    "Netto (€)", "Brutto (€)", "Status",
                    "Zahlungsart", "Zahlungsstatus"
                ])

                # Write one row per order.
                for b in bestellungen:
                    writer.writerow([
                        b.get("bestellnummer", ""),
                        # Truncate the date to the first 10 characters (no time).
                        str(b.get("bestelldatum", ""))[:10],
                        b.get("kunde_name", ""),
                        b.get("anzahl_positionen", 0),
                        f"{b.get('gesamtbetrag_netto', 0):.2f}",
                        f"{b.get('gesamtbetrag_brutto', 0):.2f}",
                        b.get("status", ""),
                        b.get("zahlungsart", ""),
                        b.get("zahlungsstatus", ""),
                    ])

            # Show a success message with the number of exported records.
            QMessageBox.information(
                self, "Export erfolgreich",
                f"{len(bestellungen)} Bestellung(en) wurden exportiert nach:\n{pfad}"
            )

        except Exception as fehler:
            # Show an error message if writing fails (e.g. missing permissions).
            QMessageBox.warning(self, "Fehler beim Export", str(fehler))
