"""
PositionenTabelle – Reusable order-position entry widget with live subtotal.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Display a dropdown of all active articles for selection.
  - Provide quantity and unit-price input fields.
  - Maintain an internal list of added positions and render them in a table.
  - Calculate and display the net subtotal in real time.
  - Emit the geaendert signal whenever the position list changes so parent
    dialogs (e.g. BestellungDialog) can update their total display.

Dependencies:
  - database (db): all SQLite operations
  - styles: centralised colour constants
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QSpinBox, QDoubleSpinBox, QAbstractItemView
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

import database as db
from styles import COLOR_PRIMARY, COLOR_DANGER


class PositionenTabelle(QWidget):
    """
    Reusable widget for order positions with a live subtotal.

    This widget shows:
      1. A dropdown list of all active articles for selection.
      2. Input fields for quantity and unit price.
      3. An "Add position" button.
      4. A table with all already-added positions (including a delete button per row).
      5. A row showing the current net subtotal.

    The widget emits the geaendert signal whenever the position list changes,
    allowing parent dialogs (e.g. BestellungDialog) to update their totals.
    """

    # Signal emitted when positions are added or removed.
    # Receivers can react to this (e.g. by recalculating the total).
    geaendert = pyqtSignal()

    def __init__(self, parent=None):
        """
        Construct the widget.

        Loads all active articles from the database first, then builds the
        entire user interface.

        Parameters:
            parent: The parent Qt widget (or None for standalone use).
        """
        # Call the base class constructor – mandatory for all Qt widgets.
        super().__init__(parent)

        # Load all active articles from the database (only active ones, so that
        # deactivated articles can no longer be ordered).
        self.artikel_liste = db.get_alle_artikel(nur_aktiv=True)

        # Build the user interface.
        self._setup_ui()

    def _setup_ui(self):
        """
        Create and configure all UI elements of the widget.

        Structure (top to bottom):
          - Row 1: article selection (dropdown / ComboBox)
          - Row 2: quantity spinner + price spinner + "Add" button
          - Table:  list of added positions
          - Total:  display of the net subtotal
        """
        # Vertical main layout for this widget.
        layout = QVBoxLayout(self)
        # No outer margin because the widget is embedded in a dialog.
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)  # 8 px spacing between elements.

        # --- Row 1: Article dropdown ---
        # QComboBox = a dropdown list for selecting one entry.
        self.art_combo = QComboBox()
        # Add the first entry as a placeholder; userData=None so we can detect
        # that no article has been selected yet.
        self.art_combo.addItem("-- Artikel wählen --", None)

        # Add one entry for each article from the database.
        # Display text: article number | name (price).
        # userData: the full article dictionary for convenient field access later.
        for a in self.artikel_liste:
            self.art_combo.addItem(
                f"{a['artikelnummer']}  |  {a['bezeichnung']}  (€ {a['verkaufspreis']:.2f})",
                a  # The full article dictionary is stored as the data value.
            )

        # When a different article is selected, automatically copy its price
        # into the price input field.
        self.art_combo.currentIndexChanged.connect(self._art_selected)
        layout.addWidget(self.art_combo)

        # --- Row 2: Quantity / Price / Button ---
        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)

        # QSpinBox = integer input field with up/down arrow buttons.
        self.menge_spin = QSpinBox()
        self.menge_spin.setRange(1, 9999)   # Minimum quantity 1, maximum 9999.
        self.menge_spin.setValue(1)          # Default value: 1 unit.
        self.menge_spin.setFixedWidth(80)    # Fixed width for a clean layout.

        # QDoubleSpinBox = decimal input field (for monetary amounts).
        self.einzelpreis_spin = QDoubleSpinBox()
        self.einzelpreis_spin.setRange(0, 99999.99)   # Price range in euros.
        self.einzelpreis_spin.setDecimals(2)           # Two decimal places (cents).
        self.einzelpreis_spin.setPrefix("€ ")          # Euro sign before the value.
        self.einzelpreis_spin.setFixedWidth(120)

        # Button to add the selected position to the list.
        add_btn = QPushButton("➕ Position hinzufügen")
        add_btn.setObjectName("btn_secondary")   # CSS class from styles.py.
        add_btn.setFixedHeight(36)
        # Connection: clicking the button calls _position_hinzufuegen.
        add_btn.clicked.connect(self._position_hinzufuegen)

        # Add controls to the horizontal row.
        controls_row.addWidget(QLabel("Menge:"))
        controls_row.addWidget(self.menge_spin)
        controls_row.addWidget(QLabel("Preis:"))
        controls_row.addWidget(self.einzelpreis_spin)
        controls_row.addStretch()             # Empty space keeps the button on the right.
        controls_row.addWidget(add_btn)
        layout.addLayout(controls_row)

        # --- Positions table ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # 6 columns: Art.-Nr., Name, Qty, Price, Total, Delete.
        self.table.setHorizontalHeaderLabels([
            "Art.-Nr.", "Bezeichnung", "Menge", "Einzelpreis", "Gesamt (Netto)", ""
        ])
        # Hide row numbers on the left – looks cleaner.
        self.table.verticalHeader().setVisible(False)
        # User may not directly edit cells – only via buttons.
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # No grid – more modern appearance.
        self.table.setShowGrid(False)
        # Alternating row background colours for better readability.
        self.table.setAlternatingRowColors(True)

        # Column widths:
        # Stretch = column expands to fill available space.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Columns 2–4 adapt to their content (no artificial expansion).
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        # Column 5 (delete button) gets a fixed, small width.
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 40)

        # Limit the minimum and maximum height of the table.
        self.table.setMinimumHeight(120)
        self.table.setMaximumHeight(280)
        layout.addWidget(self.table)

        # --- Subtotal row ---
        sum_row = QHBoxLayout()
        sum_row.addStretch()  # Empty space on the left aligns the subtotal to the right.
        self.summe_lbl = QLabel("Zwischensumme Netto: € 0,00")
        # Bold, slightly larger font so the total stands out.
        self.summe_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.summe_lbl.setStyleSheet(f"color: {COLOR_PRIMARY};")
        sum_row.addWidget(self.summe_lbl)
        layout.addLayout(sum_row)

        # Internal list where all added positions are stored as dicts
        # (e.g. {"artikel_id": 3, "menge": 2, …}).
        self.positionen = []

    def _art_selected(self, idx):
        """
        Slot: Called when the user selects a different article in the dropdown.

        Reads the sale price of the selected article and automatically enters
        it into the price input field.

        Parameters:
            idx (int): The index of the newly selected entry in the ComboBox
                       (not used directly since we use currentData()).
        """
        # currentData() returns the article dictionary that was stored as userData
        # when the ComboBox was populated.
        art = self.art_combo.currentData()
        if art:
            # Read the price from the article dict and enter it in the spinner.
            self.einzelpreis_spin.setValue(float(art.get("verkaufspreis", 0)))

    def _position_hinzufuegen(self):
        """
        Slot: Add a new position to the internal position list and update the
        table display.

        Steps:
          1. Check that an article was selected (abort if not).
          2. Read quantity and price from the input fields.
          3. If the article is already in the list, only increase its quantity
             (no duplicate entry).
          4. Otherwise create a new position dict.
          5. Re-render the table and emit the geaendert signal.
        """
        # Get the selected article dict from the ComboBox.
        art = self.art_combo.currentData()
        # If no article was selected (placeholder entry), do nothing.
        if not art:
            return

        # Read the entered quantity from the spinner.
        menge = self.menge_spin.value()

        # interpretText() forces the currently typed text to be converted to a number
        # immediately (important if the user is still typing and hasn't confirmed yet).
        self.einzelpreis_spin.interpretText()
        preis = self.einzelpreis_spin.value()

        # Check whether the article is already in the list.
        # If so, only add to the quantity instead of creating a second entry.
        for p in self.positionen:
            if p["artikel_id"] == art["id"]:
                p["menge"] += menge        # Increase quantity.
                self._render()             # Refresh the table.
                self.geaendert.emit()      # Notify parent widgets.
                return                     # Exit the function early.

        # Article not yet in the list → create a new position dict.
        self.positionen.append({
            "artikel_id":   art["id"],
            "artikelnummer": art.get("artikelnummer",""),
            "bezeichnung":  art.get("bezeichnung",""),
            "menge":        menge,
            "einzelpreis":  preis,
            # Read the VAT rate from the article; fall back to 19 % (German standard).
            "mwst_satz":    float(art.get("mwst_satz", 19)),
        })
        # Redraw the table.
        self._render()
        # Emit the signal so e.g. the dialog can update the total.
        self.geaendert.emit()

    def _render(self):
        """
        Redraw the position table based on the current self.positionen list and
        update the subtotal display.

        Five text cells are filled for each position, and a delete button is
        placed in the sixth column.  The net total is accumulated simultaneously
        and shown in the subtotal row.
        """
        # Adjust the number of table rows to match the length of the position list.
        self.table.setRowCount(len(self.positionen))

        gesamt_netto = 0.0  # Running total of all position amounts.

        for row, p in enumerate(self.positionen):
            # Calculate the net amount for this position (quantity × unit price).
            netto = p["menge"] * p["einzelpreis"]
            gesamt_netto += netto   # Add to the grand total.

            # Fill the table cells with the position data.
            self.table.setItem(row, 0, QTableWidgetItem(p.get("artikelnummer","")))
            self.table.setItem(row, 1, QTableWidgetItem(p.get("bezeichnung","")))
            self.table.setItem(row, 2, QTableWidgetItem(str(p["menge"])))
            self.table.setItem(row, 3, QTableWidgetItem(f"€ {p['einzelpreis']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"€ {netto:.2f}"))

            # Create the delete button for this row.
            del_btn = QPushButton("✕")
            # Transparent background, only a red "✕" visible.
            del_btn.setStyleSheet(f"color: {COLOR_DANGER}; background: transparent; border: none; font-weight: bold;")
            # Store the row index as a widget property so the slot _loesche_position
            # knows which position to delete.
            del_btn.setProperty("pos_idx", row)
            del_btn.clicked.connect(self._loesche_position)
            # Insert the widget (button) directly into the table cell.
            self.table.setCellWidget(row, 5, del_btn)

        # Update the subtotal label with the calculated net grand total.
        # The format specifier :,.2f adds thousands separators and exactly 2 decimal places.
        self.summe_lbl.setText(f"Zwischensumme Netto: € {gesamt_netto:,.2f}")

    def _loesche_position(self):
        """
        Slot: Remove a position from the list.

        The corresponding row index was stored as the property pos_idx when the
        button was created.  self.sender() retrieves the button that triggered
        the click, and then the property is read from it.
        """
        # sender() returns the object that emitted the signal –
        # in this case the clicked delete button.
        idx = self.sender().property("pos_idx")

        # Safety check: the index must be within the valid range.
        if 0 <= idx < len(self.positionen):
            self.positionen.pop(idx)   # Remove the position from the list.
            self._render()             # Redraw the table.
            self.geaendert.emit()      # Notify parent widgets.

    def set_positionen(self, positionen: list):
        """
        Load an external position list into the widget (e.g. when editing an
        existing order).

        The internal list is completely replaced and the table is redrawn.

        Parameters:
            positionen (list): List of position dicts from the database.
                               Each dict must contain at least the keys
                               artikel_id, menge and einzelpreis.
        """
        # Clear the internal list before inserting new data.
        self.positionen = []
        for p in positionen:
            # Convert each position to a uniform internal format;
            # missing fields are filled with default values.
            self.positionen.append({
                "artikel_id":    p["artikel_id"],
                "artikelnummer": p.get("artikelnummer",""),
                "bezeichnung":   p.get("bezeichnung",""),
                "menge":         p["menge"],
                "einzelpreis":   p["einzelpreis"],
                "mwst_satz":     p.get("mwst_satz", 19),  # Fallback: 19 %.
            })
        # Rebuild the table with the loaded data.
        self._render()

    def get_positionen(self) -> list:
        """
        Return the current position list.

        Returns:
            list: List of position dicts as stored internally.
        """
        return self.positionen

    def get_netto(self) -> float:
        """
        Calculate and return the net grand total of all positions.

        Uses a generator expression that computes quantity × unit price for
        each position and sums all values.

        Returns:
            float: Sum of all (quantity × unit price) values in euros.
        """
        # sum() with a generator: for each position p, menge × einzelpreis is
        # computed and everything is summed.
        return sum(p["menge"] * p["einzelpreis"] for p in self.positionen)
