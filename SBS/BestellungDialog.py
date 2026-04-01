"""
BestellungDialog – Modal dialog for creating and editing an order.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Provide a form for entering or editing all order header fields (customer,
    delivery address, status, payment details, delivery date, notes).
  - Embed a PositionenTabelle widget for managing order line items.
  - Calculate and display net, VAT and gross totals in real time.
  - Validate mandatory fields (customer selection, at least one position) before saving.
  - Return validated data in result_data and result_positionen after accept().

Dependencies:
  - database (db): all SQLite operations
  - styles: centralised colour constants
  - SBS.PositionenTabelle: the order-position entry widget
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QComboBox, QTextEdit, QDoubleSpinBox,
    QMessageBox, QScrollArea, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

import database as db
from styles import (
    COLOR_PRIMARY, COLOR_WHITE, COLOR_TEXT_LIGHT, COLOR_BORDER, COLOR_SECONDARY
)
from SBS.PositionenTabelle import PositionenTabelle


class BestellungDialog(QDialog):
    """
    Modal dialog for creating a new order or editing an existing one.

    If no bestellung dict is passed, the dialog opens in "New" mode.
    If an existing order dict is passed, all fields are pre-filled ("Edit" mode).

    After a successful save the result data is available in:
        self.result_data       – order header data (dict)
        self.result_positionen – list of order positions
    """

    def __init__(self, parent=None, bestellung: dict = None):
        """
        Construct the order dialog.

        Parameters:
            parent     : Parent widget (or None).
            bestellung : Dict with the data of an existing order to edit,
                         or None for a new order.
        """
        # Call the Qt base class constructor.
        super().__init__(parent)

        # Store the order data; empty dict if none was passed.
        self.bestellung = bestellung or {}

        # Set the window title depending on the mode.
        self.setWindowTitle("Bestellung bearbeiten" if bestellung else "Neue Bestellung anlegen")

        # Set the minimum dialog size.
        self.setMinimumWidth(720)
        self.setMinimumHeight(700)

        # Modal = the dialog blocks interaction with the main window until closed.
        self.setModal(True)

        # Build the UI elements.
        self._setup_ui()

        # In edit mode: fill the fields with the existing data.
        if bestellung:
            self._fill_data()

        # Calculate and display the initial total.
        self._update_summe()

    def _setup_ui(self):
        """
        Create the complete user interface of the dialog.

        Structure (top to bottom):
          1. Coloured header with the dialog title.
          2. Scrollable content area:
             a. Customer selection + delivery address.
             b. Order status, payment method, payment status, delivery date.
             c. PositionenTabelle widget.
             d. Discount + shipping costs.
             e. Totals box (net / VAT / gross).
             f. Notes field.
          3. Footer with Cancel and Save buttons.
        """
        # Set the background colour of the dialog to white.
        self.setStyleSheet(f"QDialog {{ background: {COLOR_WHITE}; }}")

        # Main layout with no margins – header and footer should be flush with the edges.
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Header area ---
        header = QFrame()
        header.setObjectName("bestellung_header")
        # Primary colour as background for the header bar.
        header.setStyleSheet(f"QFrame#bestellung_header {{ background: {COLOR_PRIMARY}; }}")
        header.setFixedHeight(64)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        # Title: "Edit order" or "New order".
        title_lbl = QLabel("📦  " + ("Bestellung bearbeiten" if self.bestellung else "Neue Bestellung"))
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLOR_WHITE};")
        h_layout.addWidget(title_lbl)
        layout.addWidget(header)

        # --- Scrollable content area ---
        # QScrollArea allows scrolling when the content exceeds the window size –
        # important for small screens.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)    # Widget adapts to the available size.
        scroll.setFrameShape(QFrame.Shape.NoFrame)  # No frame around the scroll area.

        content = QWidget()               # Content widget that goes into the scroll area.
        scroll.setWidget(content)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(16)

        # --- Helper functions for a consistent layout ---

        def section(text):
            """
            Create a section heading with a separator line.

            Parameters:
                text (str): Text to display as the heading.
            Returns:
                QLabel with appropriate styling.
            """
            lbl = QLabel(text)
            lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            lbl.setStyleSheet(f"""
                color: {COLOR_PRIMARY};
                border-bottom: 2px solid {COLOR_SECONDARY};
                padding-bottom: 4px;
            """)
            return lbl

        def lbl(text):
            """
            Create a small field label for form fields.

            Parameters:
                text (str): Field label text.
            Returns:
                QLabel with small, grey font.
            """
            l = QLabel(text)
            l.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {COLOR_TEXT_LIGHT};")
            return l

        # ── Section: Customer ──────────────────────────────────────────────────
        content_layout.addWidget(section("👤 Kunde"))
        kunde_row = QHBoxLayout()

        # Load all customers from the database.
        self.kunden = db.get_alle_kunden()
        self.kunde_combo = QComboBox()
        self.kunde_combo.addItem("-- Kunden wählen --", None)  # Placeholder.

        # Add one entry for each customer (customer number | name (city)).
        for k in self.kunden:
            self.kunde_combo.addItem(
                f"{k['kundennummer']}  |  {k['vorname']} {k['nachname']}  ({k.get('ort','')})",
                k["id"]   # Store the customer ID as userData.
            )

        # When a customer is selected, automatically fill in the delivery address.
        self.kunde_combo.currentIndexChanged.connect(self._update_lieferadresse)

        # Customer selection column (weight 2 = twice as wide as others).
        col_k = QVBoxLayout(); col_k.setSpacing(4)
        col_k.addWidget(lbl("Kunde *")); col_k.addWidget(self.kunde_combo)
        kunde_row.addLayout(col_k, 2)

        # Delivery address – filled automatically, but can be edited manually
        # (e.g. for a different delivery address).
        self.liefer_edit = QLineEdit()
        self.liefer_edit.setPlaceholderText("Wird automatisch befüllt oder manuell eingeben")
        col_l = QVBoxLayout(); col_l.setSpacing(4)
        col_l.addWidget(lbl("Lieferadresse"))
        col_l.addWidget(self.liefer_edit)
        kunde_row.addLayout(col_l, 2)
        content_layout.addLayout(kunde_row)

        # ── Section: Status & Payment ──────────────────────────────────────────
        content_layout.addWidget(section("📋 Status & Zahlung"))
        status_row = QHBoxLayout(); status_row.setSpacing(12)

        # Dropdown for the order status.
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Neu","In Bearbeitung","Versendet","Geliefert","Storniert","Zurückgegeben"])

        # Dropdown for the payment method.
        self.zahlung_combo = QComboBox()
        self.zahlung_combo.addItems(["Bar","EC-Karte","Kreditkarte","Überweisung","Rechnung","PayPal"])

        # Dropdown for the payment status.
        self.zahlstatus_combo = QComboBox()
        self.zahlstatus_combo.addItems(["Offen","Teilbezahlt","Bezahlt","Erstattet"])

        # Date input with calendar popup for the desired delivery date.
        self.liefer_datum = QDateEdit()
        self.liefer_datum.setDisplayFormat("dd.MM.yyyy")   # German date format.
        self.liefer_datum.setCalendarPopup(True)            # Small calendar popup.
        # Default: suggest 7 days from today.
        self.liefer_datum.setDate(QDate.currentDate().addDays(7))

        # Arrange all four controls uniformly in columns.
        for lbl_t, widget in [("Bestellstatus", self.status_combo),
                                ("Zahlungsart", self.zahlung_combo),
                                ("Zahlungsstatus", self.zahlstatus_combo),
                                ("Lieferdatum", self.liefer_datum)]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(lbl(lbl_t)); col.addWidget(widget)
            status_row.addLayout(col)
        content_layout.addLayout(status_row)

        # ── Section: Order positions ───────────────────────────────────────────
        content_layout.addWidget(section("🛒 Bestellpositionen"))
        # Embed the reusable PositionenTabelle widget.
        self.positionen_widget = PositionenTabelle(self)
        # When positions change, update the grand total in the dialog.
        self.positionen_widget.geaendert.connect(self._update_summe)
        content_layout.addWidget(self.positionen_widget)

        # ── Conditions: discount and shipping ─────────────────────────────────
        cond_row = QHBoxLayout(); cond_row.setSpacing(12)

        # Discount in percent (0–100 %, one decimal place).
        self.rabatt_spin = QDoubleSpinBox()
        self.rabatt_spin.setRange(0, 100)
        self.rabatt_spin.setSuffix(" %")     # Unit shown after the value.
        self.rabatt_spin.setDecimals(1)
        # Recalculate the total immediately on change.
        self.rabatt_spin.valueChanged.connect(self._update_summe)

        # Shipping costs in euros.
        self.versand_spin = QDoubleSpinBox()
        self.versand_spin.setRange(0, 999.99)
        self.versand_spin.setPrefix("€ ")
        self.versand_spin.setDecimals(2)
        # Recalculate the total immediately on change.
        self.versand_spin.valueChanged.connect(self._update_summe)

        # Arrange both fields side by side uniformly.
        for lbl_t, widget in [("Gesamtrabatt (%)", self.rabatt_spin),
                                ("Versandkosten", self.versand_spin)]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(lbl(lbl_t)); col.addWidget(widget)
            cond_row.addLayout(col)
        cond_row.addStretch()   # Leave remaining space empty.
        content_layout.addLayout(cond_row)

        # ── Totals box ────────────────────────────────────────────────────────
        # Frame with a light colour background for visual emphasis.
        summe_frame = QFrame()
        summe_frame.setStyleSheet(f"""
            background: {COLOR_PRIMARY}18;
            border: 1px solid {COLOR_PRIMARY}30;
            border-radius: 10px;
            padding: 14px;
        """)
        # Note: "18" and "30" at the end are hex alpha values
        # (18hex ≈ 9 %, 30hex ≈ 19 % opacity).
        summe_layout = QHBoxLayout(summe_frame)
        summe_layout.addStretch()

        # Three labels for the split total display.
        self.gesamt_netto_lbl = QLabel("Netto: € 0,00")
        self.gesamt_netto_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")

        self.gesamt_mwst_lbl  = QLabel("MwSt.: € 0,00")
        self.gesamt_mwst_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")

        # Gross amount highlighted (larger, bold, primary colour).
        self.gesamt_brutto_lbl = QLabel("Gesamt Brutto: € 0,00")
        self.gesamt_brutto_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.gesamt_brutto_lbl.setStyleSheet(f"color: {COLOR_PRIMARY};")

        # Labels side by side with small spacers.
        summe_layout.addWidget(self.gesamt_netto_lbl)
        summe_layout.addSpacing(20)
        summe_layout.addWidget(self.gesamt_mwst_lbl)
        summe_layout.addSpacing(20)
        summe_layout.addWidget(self.gesamt_brutto_lbl)
        content_layout.addWidget(summe_frame)

        # ── Notes ─────────────────────────────────────────────────────────────
        # Multi-line text field for remarks about the order.
        self.notizen_edit = QTextEdit()
        self.notizen_edit.setPlaceholderText("Anmerkungen zur Bestellung...")
        self.notizen_edit.setMaximumHeight(70)  # Keep compact.
        col_n = QVBoxLayout(); col_n.setSpacing(4)
        col_n.addWidget(lbl("Notizen")); col_n.addWidget(self.notizen_edit)
        content_layout.addLayout(col_n)
        # Flexible empty space at the end for visual breathing room.
        content_layout.addStretch()

        # Add the scrollable area to the main layout.
        layout.addWidget(scroll)

        # --- Footer with buttons ---
        btn_frame = QFrame()
        btn_frame.setObjectName("bestellung_btn_frame")
        # Light background and separator line above.
        btn_frame.setStyleSheet(f"QFrame#bestellung_btn_frame {{ background: #f8f9fa; border-top: 1px solid {COLOR_BORDER}; }}")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(24, 14, 24, 14)
        btn_layout.addStretch()   # Push buttons to the right.

        # "Cancel" button – closes the dialog without saving.
        abbruch_btn = QPushButton("Abbrechen")
        abbruch_btn.setObjectName("btn_icon")
        abbruch_btn.setFixedHeight(38)
        # reject() closes the dialog with the result code "Rejected".
        abbruch_btn.clicked.connect(self.reject)

        # "Save" button – validates and saves the order.
        speichern_btn = QPushButton("💾  Bestellung speichern")
        speichern_btn.setObjectName("btn_primary")
        speichern_btn.setFixedHeight(38)
        speichern_btn.clicked.connect(self._speichern)

        btn_layout.addWidget(abbruch_btn)
        btn_layout.addWidget(speichern_btn)
        layout.addWidget(btn_frame)

    def _update_lieferadresse(self):
        """
        Slot: Automatically fill the delivery address field with the address of
        the currently selected customer.

        Searches the local customer list for the customer whose ID is selected
        in the ComboBox and sets the address as a "Street, Postcode, City" string
        in the text field.
        """
        # Read the customer ID from the ComboBox (stored as userData).
        kid = self.kunde_combo.currentData()

        for k in self.kunden:
            if k["id"] == kid:
                # Build the address components; filter out empty parts.
                teile = [k.get("strasse",""), k.get("plz",""), k.get("ort","")]
                addr = ", ".join(t for t in teile if t)  # Join only non-empty parts.
                self.liefer_edit.setText(addr)
                break   # Stop the loop once the customer is found.

    def _update_summe(self):
        """
        Calculate the grand totals (net, VAT, gross) and update the three total
        labels in the dialog.

        Calculation order:
          1. Get the net subtotal from the positions.
          2. Subtract the discount.
          3. Add the shipping costs.
          4. Calculate VAT at a flat rate of 19 %.
          5. Gross = net × 1.19.
        """
        # Net subtotal of all positions from the PositionenTabelle widget.
        netto = self.positionen_widget.get_netto()

        # Discount as a decimal (e.g. 10 % → 0.10).
        rabatt = self.rabatt_spin.value() / 100
        versand = self.versand_spin.value()

        # Net after deducting the discount + shipping costs.
        netto_nach_rabatt = netto * (1 - rabatt) + versand

        # Approximated VAT (19 %) – simplified calculation, as in a real business
        # different tax rates may apply per article.
        mwst = netto_nach_rabatt * 0.19
        brutto = netto_nach_rabatt * 1.19  # Gross = net + 19 % VAT.

        # Update the labels; :,.2f → thousands separator + 2 decimal places.
        self.gesamt_netto_lbl.setText(f"Netto: € {netto_nach_rabatt:,.2f}")
        self.gesamt_mwst_lbl.setText(f"MwSt. (19%): € {mwst:,.2f}")
        self.gesamt_brutto_lbl.setText(f"Gesamt Brutto: € {brutto:,.2f}")

    def _fill_data(self):
        """
        Fill all form fields with the data of an existing order (only called
        in edit mode).

        Reads all relevant values from self.bestellung (the passed dict) and
        sets them in the corresponding input fields.
        Also loads the order positions from the database.
        """
        b = self.bestellung   # Short alias for readability.

        # Find and select the customer in the ComboBox by the stored ID.
        idx = self.kunde_combo.findData(b.get("kunden_id"))
        if idx >= 0:
            # findData() returns -1 if nothing is found;
            # therefore only set if a valid index was found.
            self.kunde_combo.setCurrentIndex(idx)

        # Fill text fields and ComboBoxes with the order data.
        self.liefer_edit.setText(b.get("lieferadresse","") or "")
        self.status_combo.setCurrentText(b.get("status","Neu"))
        self.zahlung_combo.setCurrentText(b.get("zahlungsart","Rechnung"))
        self.zahlstatus_combo.setCurrentText(b.get("zahlungsstatus","Offen"))

        # Convert the delivery date from ISO format "YYYY-MM-DD" to a QDate.
        d = b.get("lieferdatum","")
        if d:
            # str(d)[:10] extracts the first 10 characters (date only,
            # without any time part).
            qd = QDate.fromString(str(d)[:10], "yyyy-MM-dd")
            if qd.isValid():   # Only set if the date was parsed correctly.
                self.liefer_datum.setDate(qd)

        # Numeric fields; "or 0" catches None values from the database.
        self.rabatt_spin.setValue(float(b.get("rabatt_prozent",0) or 0))
        self.versand_spin.setValue(float(b.get("versandkosten",0) or 0))
        self.notizen_edit.setPlainText(b.get("notizen","") or "")

        # Load the order positions from the database and put them in the widget.
        positionen = db.get_bestellpositionen(b["id"])
        self.positionen_widget.set_positionen(positionen)

        # Recalculate the total after loading the positions.
        self._update_summe()

    def _speichern(self):
        """
        Validate the inputs and save the order.

        Mandatory field checks:
          - A customer must be selected.
          - At least one order position must be present.

        If validation passes, the result data is stored in the attributes
        result_data and result_positionen, and the dialog is closed with accept().
        The calling code can then check dlg.exec() == QDialog.DialogCode.Accepted
        to determine whether saving was successful.
        """
        # Read the customer ID from the ComboBox.
        kid = self.kunde_combo.currentData()

        # Mandatory field: a customer must be selected.
        if not kid:
            QMessageBox.warning(self, "Pflichtfeld", "Bitte einen Kunden auswählen.")
            return   # Abort saving.

        # Mandatory field: at least one position must be present.
        positionen = self.positionen_widget.get_positionen()
        if not positionen:
            QMessageBox.warning(self, "Keine Positionen",
                "Bitte mindestens einen Artikel zur Bestellung hinzufügen.")
            return   # Abort saving.

        # Assemble the result data into a dict that will be passed to the database.
        # "id" is None for new orders.
        self.result_data = {
            "id":             self.bestellung.get("id"),   # None for a new order.
            "kunden_id":      kid,
            "lieferadresse":  self.liefer_edit.text().strip(),
            "status":         self.status_combo.currentText(),
            "zahlungsart":    self.zahlung_combo.currentText(),
            "zahlungsstatus": self.zahlstatus_combo.currentText(),
            # Store the date in ISO format for the database.
            "lieferdatum":    self.liefer_datum.date().toString("yyyy-MM-dd"),
            "rabatt_prozent": self.rabatt_spin.value(),
            "versandkosten":  self.versand_spin.value(),
            "notizen":        self.notizen_edit.toPlainText().strip(),
        }
        # Store the positions separately.
        self.result_positionen = positionen

        # Close the dialog successfully – signals to the caller: "Save was OK".
        self.accept()
