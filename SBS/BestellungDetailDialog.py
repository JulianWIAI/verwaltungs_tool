"""
BestellungDetailDialog – Read-only order detail view with quick status update.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Display full order details (header info, positions table, notes) in a
    read-only scrollable view.
  - Allow quick update of order status and payment status without reopening
    the full edit dialog.
  - Emit the status_geaendert signal after a status update so the order list
    can refresh automatically.

Dependencies:
  - database (db): all SQLite operations
  - styles: centralised colour constants and STATUS_FARBEN / ZAHLUNG_FARBEN mappings
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QScrollArea, QAbstractItemView
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

import database as db
from styles import (
    COLOR_PRIMARY, COLOR_WHITE, COLOR_TEXT_LIGHT, COLOR_BORDER,
    STATUS_FARBEN, ZAHLUNG_FARBEN
)


class BestellungDetailDialog(QDialog):
    """
    Read-only view of an existing order with the option to quickly update the
    order and payment status.

    The status_geaendert signal is emitted when the user changes the status via
    the dialog, so the order list can refresh automatically.
    """

    # Signal emitted when the order status has been changed.
    status_geaendert = pyqtSignal()

    def __init__(self, parent, bestell_id: int):
        """
        Construct the detail dialog.

        Parameters:
            parent      : Parent widget.
            bestell_id  : Database primary key (ID) of the order to display.
        """
        super().__init__(parent)
        # Remember the order ID for later database access.
        self.bestell_id = bestell_id
        self.setWindowTitle("Bestelldetails")
        self.setMinimumWidth(640)
        self.setModal(True)   # Blocks interaction with the parent window.
        self._setup_ui()

    def _setup_ui(self):
        """
        Create the order detail view.

        First loads all required data from the database, then builds the
        following structure:
          1. Coloured header with order number and status badge.
          2. Scrollable content area:
             a. Info tiles (customer, date, payment method, total amount).
             b. Table with all order positions.
             c. Quick-update bar for status and payment.
             d. Notes (if present).
          3. Footer with a "Close" button.
        """
        # Load order data and positions from the database.
        b = db.get_bestellung(self.bestell_id)
        pos = db.get_bestellpositionen(self.bestell_id)

        # Safety check: the order might have been deleted in the meantime.
        if not b:
            return

        self.setStyleSheet(f"QDialog {{ background: {COLOR_WHITE}; }}")
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Header with order number and coloured status badge ---
        # Get the status colour from the mapping in styles.py (fallback: grey).
        status_farbe = STATUS_FARBEN.get(b["status"], "#666")
        header = QFrame()
        header.setObjectName("detail_header")
        header.setStyleSheet(f"QFrame#detail_header {{ background: {COLOR_PRIMARY}; }}")
        header.setFixedHeight(70)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        # Title: order number.
        title = QLabel(f"📦  Bestellung {b['bestellnummer']}")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_WHITE};")

        # Status badge: small coloured label with the current status.
        status_badge = QLabel(b["status"])
        status_badge.setStyleSheet(f"""
            background: {status_farbe}; color: white;
            border-radius: 10px; padding: 4px 14px;
            font-size: 12px; font-weight: 600;
        """)

        h_layout.addWidget(title)
        h_layout.addStretch()       # Empty space between title and badge.
        h_layout.addWidget(status_badge)
        layout.addWidget(header)

        # --- Scrollable content area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(24, 20, 24, 20)
        c_layout.setSpacing(14)

        # --- Info tiles as a horizontal strip ---
        info_row = QHBoxLayout()
        info_row.setSpacing(12)

        def info_card(titel, wert, farbe="#fff"):
            """
            Create an info tile with a title and a value.

            Parameters:
                titel (str): Tile heading (small, grey).
                wert  (str): Value to display (large, bold).
                farbe (str): Background colour as a hex string (default: white).
            Returns:
                QFrame widget that can be inserted directly into a layout.
            """
            f = QFrame()
            f.setStyleSheet(f"""
                background: {farbe};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 10px 14px;
            """)
            fl = QVBoxLayout(f)
            fl.setSpacing(2)
            # Small title label.
            t = QLabel(titel)
            t.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_LIGHT}; font-weight: 600;")
            # Large value label.
            v = QLabel(str(wert))
            v.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            v.setStyleSheet(f"color: {COLOR_PRIMARY};")
            fl.addWidget(t); fl.addWidget(v)
            return f

        # Payment status colour from the mapping.
        z_farbe = ZAHLUNG_FARBEN.get(b["zahlungsstatus"], "#666")

        # Four info tiles side by side.
        info_row.addWidget(info_card("Kunde", b["kunde_name"]))
        info_row.addWidget(info_card("Datum", str(b["bestelldatum"])[:10]))  # Date only, no time.
        info_row.addWidget(info_card("Zahlungsart", b["zahlungsart"]))
        info_row.addWidget(info_card("Gesamtbetrag", f"€ {b.get('gesamtbetrag_brutto', 0):.2f}"))
        c_layout.addLayout(info_row)

        # --- Position table ---
        pos_title = QLabel("Bestellpositionen")
        pos_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        pos_title.setStyleSheet(f"color: {COLOR_PRIMARY};")
        c_layout.addWidget(pos_title)

        # Create the table directly with the number of positions (len(pos) rows, 5 columns).
        pos_table = QTableWidget(len(pos), 5)
        pos_table.setHorizontalHeaderLabels(["Art.-Nr.", "Bezeichnung", "Menge", "Einzelpreis", "Gesamt Netto"])
        pos_table.verticalHeader().setVisible(False)
        pos_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Read-only.
        pos_table.setShowGrid(False)
        pos_table.setAlternatingRowColors(True)
        pos_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Enter positions into the table.
        for row, p in enumerate(pos):
            pos_table.setItem(row, 0, QTableWidgetItem(p.get("artikelnummer","")))
            pos_table.setItem(row, 1, QTableWidgetItem(p.get("bezeichnung","")))
            # Quantity + unit (e.g. "2 Stk.") assembled.
            pos_table.setItem(row, 2, QTableWidgetItem(f"{p['menge']} {p.get('einheit','')}"))
            pos_table.setItem(row, 3, QTableWidgetItem(f"€ {p['einzelpreis']:.2f}"))
            # Row total = quantity × unit price.
            pos_table.setItem(row, 4, QTableWidgetItem(f"€ {p['menge']*p['einzelpreis']:.2f}"))

        # Adjust the table height exactly to its content (46 px per row + 40 px header).
        pos_table.setMaximumHeight(len(pos) * 46 + 40)
        c_layout.addWidget(pos_table)

        # --- Quick-update bar for status and payment ---
        sq_frame = QFrame()
        sq_frame.setObjectName("sq_frame")
        sq_frame.setStyleSheet(f"QFrame#sq_frame {{ background: #f8f9fa; border-radius: 8px; }}")
        sq_layout = QHBoxLayout(sq_frame)
        sq_layout.setContentsMargins(16, 10, 16, 10)

        sq_layout.addWidget(QLabel("Status ändern:"))
        # ComboBox for the new order status, pre-selected with the current status.
        self.new_status_combo = QComboBox()
        self.new_status_combo.addItems(["Neu","In Bearbeitung","Versendet","Geliefert","Storniert","Zurückgegeben"])
        self.new_status_combo.setCurrentText(b["status"])   # Pre-select the current status.
        sq_layout.addWidget(self.new_status_combo)

        sq_layout.addWidget(QLabel("Zahlung:"))
        # ComboBox for the new payment status.
        self.new_zahl_combo = QComboBox()
        self.new_zahl_combo.addItems(["Offen","Teilbezahlt","Bezahlt","Erstattet"])
        self.new_zahl_combo.setCurrentText(b["zahlungsstatus"])   # Pre-select current value.
        sq_layout.addWidget(self.new_zahl_combo)

        # Button to save the status change immediately.
        upd_btn = QPushButton("✓ Aktualisieren")
        upd_btn.setObjectName("btn_secondary")
        upd_btn.setFixedHeight(34)
        upd_btn.clicked.connect(self._update_status)
        sq_layout.addWidget(upd_btn)
        sq_layout.addStretch()
        c_layout.addWidget(sq_frame)

        # --- Show notes (only if present) ---
        if b.get("notizen"):
            notiz_lbl = QLabel(f"📝 {b['notizen']}")
            notiz_lbl.setWordWrap(True)   # Long text wraps automatically.
            notiz_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px; font-style: italic;")
            c_layout.addWidget(notiz_lbl)

        c_layout.addStretch()   # Empty space at the end of the content.
        layout.addWidget(scroll)

        # --- Footer with "Close" button ---
        btn_frame = QFrame()
        btn_frame.setObjectName("detail_btn_frame")
        btn_frame.setStyleSheet(f"QFrame#detail_btn_frame {{ background: #f8f9fa; border-top: 1px solid {COLOR_BORDER}; }}")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(24, 12, 24, 12)
        btn_layout.addStretch()

        # "Close" button – accept() closes the dialog normally.
        close_btn = QPushButton("Schließen")
        close_btn.setObjectName("btn_icon")
        close_btn.setFixedHeight(38)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addWidget(btn_frame)

    def _update_status(self):
        """
        Slot: Save the changed order and payment status to the database and
        notify all connected receivers via the signal.

        Reads the currently selected values from the status ComboBoxes and
        passes them to the database function update_bestellstatus.
        A short success message is then shown.
        """
        # Call the database function that updates the order status.
        db.update_bestellstatus(
            self.bestell_id,                       # Which order?
            self.new_status_combo.currentText(),   # New order status.
            self.new_zahl_combo.currentText()      # New payment status.
        )
        # Emit the signal so e.g. the order list can refresh and display the new status.
        self.status_geaendert.emit()

        # Show a confirmation dialog.
        QMessageBox.information(self, "Aktualisiert", "Status wurde erfolgreich aktualisiert.")
