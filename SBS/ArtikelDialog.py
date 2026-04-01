"""
ArtikelDialog – Modal dialog for creating and editing an article record.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Display a form for entering or editing all article fields (name, category,
    manufacturer, supplier, prices, stock, description, active flag).
  - Validate the mandatory field (article name) before saving.
  - Return the validated form data in result_data after accept().

Dependencies:
  - database (db): all SQLite operations (used to load categories)
  - styles: centralised colour constants
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import database as db
from styles import (
    COLOR_PRIMARY, COLOR_WHITE, COLOR_TEXT_LIGHT, COLOR_BORDER
)


class ArtikelDialog(QDialog):
    """
    Modal dialog for creating a new article or editing an existing one.

    "Modal" means: the dialog blocks all other windows of the application
    until the user saves or cancels.

    Parameters:
        parent  (QWidget, optional): The parent widget.
        artikel (dict, optional):    Dictionary with existing article data.
                                     None = new article.

    Attributes:
        artikel     (dict): The passed article data (or {}).
        kategorien  (list): List of all categories from the database.
        result_data (dict): After saving: all form data as a dictionary.
    """

    def __init__(self, parent=None, artikel: dict = None):
        """
        Construct the dialog.

        Calls the parent class constructor, stores the article data, sets the
        window title and builds the user interface.

        Args:
            parent  (QWidget, optional): Parent widget.
            artikel (dict, optional):    Existing article data or None.
        """
        # Initialise the parent class – mandatory for every Qt class.
        super().__init__(parent)

        # Store article data; "artikel or {}" yields {} when None is passed.
        self.artikel = artikel or {}

        # Window title depends on whether an article is being edited or newly created.
        self.setWindowTitle("Artikel bearbeiten" if artikel else "Neuen Artikel anlegen")

        # Minimum window width in pixels.
        self.setMinimumWidth(580)

        # The dialog blocks the parent window.
        self.setModal(True)

        # Build all widgets and the layout.
        self._setup_ui()

        # If an existing article was passed, fill the fields with its data.
        if artikel:
            self._fill_data()

    def _setup_ui(self):
        """
        Create and configure all widgets of the article dialog.

        The dialog is divided into three areas:
          1. Header  – coloured title bar at the top with a bicycle icon.
          2. Form    – input fields (name, category, prices, stock,
                       description, active checkbox).
          3. Buttons – "Cancel" and "Save" at the bottom.
        """
        # Set the background of the entire dialog to white.
        self.setStyleSheet(f"QDialog {{ background: {COLOR_WHITE}; }}")

        # Main layout: arrange all three areas vertically.
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Area 1: Header ---
        header = QFrame()
        header.setStyleSheet(f"background: {COLOR_PRIMARY};")
        header.setFixedHeight(64)

        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        # Title text with bicycle emoji; content depends on the mode.
        title_lbl = QLabel("🚲  " + ("Artikel bearbeiten" if self.artikel else "Neuen Artikel anlegen"))
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLOR_WHITE};")
        h_layout.addWidget(title_lbl)
        layout.addWidget(header)

        # --- Area 2: Form ---
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(24, 20, 24, 20)
        form_layout.setSpacing(12)

        # --- Helper: create a small bold field label ---
        def lbl(text):
            """
            Create a small, bold field label in COLOR_TEXT_LIGHT.
            Used above each input field.

            Args:
                text (str): Label text (e.g. "Name *").

            Returns:
                QLabel: The finished label.
            """
            l = QLabel(text)
            l.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {COLOR_TEXT_LIGHT};")
            return l

        # --- Helper: create a horizontal row from multiple widgets ---
        def row(*widgets):
            """
            Create a horizontal layout from an arbitrary number of widgets.
            Integers are inserted as fixed spacers (addSpacing), everything
            else as widgets.

            Args:
                *widgets: Any number of QWidget objects or int spacer values.

            Returns:
                QHBoxLayout: The finished horizontal layout.
            """
            r = QHBoxLayout()
            r.setSpacing(12)
            for w in widgets:
                # Check if w is an integer (spacer) or a widget.
                r.addWidget(w) if not isinstance(w, int) else r.addSpacing(w)
            return r

        # --- Form row 1: Name + Category ---
        # Name field (mandatory, takes 2/3 of the width).
        self.bez_edit = QLineEdit()
        self.bez_edit.setPlaceholderText("Artikelbezeichnung *")

        # Category dropdown: first load all categories from the database.
        self.kat_combo = QComboBox()
        self.kategorien = db.get_kategorien()   # List of dicts: [{id, name}, …]
        self.kat_combo.addItem("-- Kategorie wählen --", None)   # Empty default entry.

        # Insert each category with its name (displayed) and ID (as data value).
        for k in self.kategorien:
            self.kat_combo.addItem(k["name"], k["id"])

        # Two columns side by side: name gets stretch factor 2, category gets 1.
        col1 = QVBoxLayout()
        col1.setSpacing(4)
        col1.addWidget(lbl("Bezeichnung *"))
        col1.addWidget(self.bez_edit)

        col2 = QVBoxLayout()
        col2.setSpacing(4)
        col2.addWidget(lbl("Kategorie"))
        col2.addWidget(self.kat_combo)

        r1 = QHBoxLayout()
        r1.setSpacing(12)
        r1.addLayout(col1, 2)   # Stretch factor 2 = twice as wide as col2.
        r1.addLayout(col2, 1)   # Stretch factor 1.
        form_layout.addLayout(r1)

        # --- Form row 2: Manufacturer + Supplier ---
        self.hersteller_edit = QLineEdit()
        self.hersteller_edit.setPlaceholderText("z.B. Shimano, Trek, Cube")
        self.lieferant_edit = QLineEdit()
        self.lieferant_edit.setPlaceholderText("Lieferantenname")

        r2 = QHBoxLayout()
        r2.setSpacing(12)
        # Compact notation: create col3/col4 inline.
        col3 = QVBoxLayout(); col3.setSpacing(4)
        col3.addWidget(lbl("Hersteller")); col3.addWidget(self.hersteller_edit)
        col4 = QVBoxLayout(); col4.setSpacing(4)
        col4.addWidget(lbl("Lieferant")); col4.addWidget(self.lieferant_edit)
        r2.addLayout(col3)
        r2.addLayout(col4)
        form_layout.addLayout(r2)

        # --- Form row 3: Prices (purchase price, sale price, VAT) ---
        # Purchase price: QDoubleSpinBox allows decimals (e.g. 12.50).
        self.ek_spin = QDoubleSpinBox()
        self.ek_spin.setRange(0, 99999.99)      # Range: 0 to 99,999.99 €.
        self.ek_spin.setDecimals(2)              # Always 2 decimal places.
        self.ek_spin.setPrefix("€ ")             # "€ " is shown before the value.
        self.ek_spin.setSingleStep(0.50)         # Arrow click changes value by 0.50 €.

        # Sale price (net, excluding VAT).
        self.vk_spin = QDoubleSpinBox()
        self.vk_spin.setRange(0, 99999.99)
        self.vk_spin.setDecimals(2)
        self.vk_spin.setPrefix("€ ")
        self.vk_spin.setSingleStep(0.50)

        # VAT rate as a dropdown (Germany: 19% standard, 7% reduced).
        self.mwst_combo = QComboBox()
        self.mwst_combo.addItems(["19.0", "7.0", "0.0"])
        self.mwst_combo.setFixedWidth(80)

        # Arrange all three fields in one row (using a loop).
        r3 = QHBoxLayout(); r3.setSpacing(12)
        for lbl_t, widget in [("Einkaufspreis", self.ek_spin),
                                ("Verkaufspreis *", self.vk_spin),
                                ("MwSt. %", self.mwst_combo)]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(lbl(lbl_t)); col.addWidget(widget)
            r3.addLayout(col)
        form_layout.addLayout(r3)

        # --- Form row 4: Stock data ---
        # Stock quantity: QSpinBox for integers (no decimal places).
        self.bestand_spin = QSpinBox()
        self.bestand_spin.setRange(0, 99999)   # 0 to 99,999 units.

        # Minimum stock: if stock falls below this, "Reorder" is shown.
        self.mindest_spin = QSpinBox()
        self.mindest_spin.setRange(0, 9999)

        # Unit: dropdown for various units of measure.
        self.einheit_combo = QComboBox()
        self.einheit_combo.addItems(["Stück", "Paar", "Satz", "Meter", "Liter", "kg"])

        # Again arranged in one row using a loop.
        r4 = QHBoxLayout(); r4.setSpacing(12)
        for lbl_t, widget in [("Lagerbestand", self.bestand_spin),
                                ("Mindestbestand", self.mindest_spin),
                                ("Einheit", self.einheit_combo)]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(lbl(lbl_t)); col.addWidget(widget)
            r4.addLayout(col)
        form_layout.addLayout(r4)

        # --- Form row 5: Article description ---
        # QTextEdit allows multi-line text (unlike QLineEdit).
        self.beschr_edit = QTextEdit()
        self.beschr_edit.setPlaceholderText("Artikelbeschreibung, technische Details...")
        self.beschr_edit.setMaximumHeight(80)  # Limit height for a compact layout.
        col_d = QVBoxLayout(); col_d.setSpacing(4)
        col_d.addWidget(lbl("Beschreibung")); col_d.addWidget(self.beschr_edit)
        form_layout.addLayout(col_d)

        # --- Active checkbox ---
        # Inactive articles are shown in the list but not offered for sale.
        self.aktiv_check = QCheckBox("Artikel ist aktiv / verkäuflich")
        self.aktiv_check.setChecked(True)   # Checked by default for new articles.
        form_layout.addWidget(self.aktiv_check)

        # Add the completed form widget to the main layout.
        layout.addWidget(form_widget)

        # --- Area 3: Buttons ---
        btn_frame = QFrame()
        btn_frame.setObjectName("artikel_btn_frame")
        # Light grey background with a separator line at the top.
        btn_frame.setStyleSheet(
            f"QFrame#artikel_btn_frame {{ background: #f8f9fa; border-top: 1px solid {COLOR_BORDER}; }}"
        )
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(24, 14, 24, 14)
        btn_layout.addStretch()   # Pushes buttons to the right.

        # "Cancel" button: closes the dialog without saving.
        abbruch_btn = QPushButton("Abbrechen")
        abbruch_btn.setObjectName("btn_icon")
        abbruch_btn.setFixedHeight(38)
        # reject() is a built-in QDialog method (result = "Rejected").
        abbruch_btn.clicked.connect(self.reject)

        # "Save" button: calls the validation and save logic.
        speichern_btn = QPushButton("💾  Speichern")
        speichern_btn.setObjectName("btn_primary")
        speichern_btn.setFixedHeight(38)
        speichern_btn.clicked.connect(self._speichern)

        btn_layout.addWidget(abbruch_btn)
        btn_layout.addWidget(speichern_btn)
        layout.addWidget(btn_frame)

    def _fill_data(self):
        """
        Fill all input fields with the data of the article being edited.

        Only called when an existing article dictionary was passed at dialog
        creation time.

        Special handling:
          - Category: found in the dropdown via its ID (findData).
          - VAT:      found via its text value (findText).
          - Unit:     found via its text value (findText).
          - Active:   boolean value (0/1 in the DB) converted to True/False.
        """
        # Short reference to self.artikel for more compact code.
        a = self.artikel

        # Fill the name field.
        self.bez_edit.setText(a.get("bezeichnung", ""))

        # Find the category in the dropdown using the stored data ID.
        # findData() searches for the data value (the ID), not the displayed text.
        idx = self.kat_combo.findData(a.get("kategorie_id"))
        if idx >= 0:
            self.kat_combo.setCurrentIndex(idx)

        # Manufacturer and supplier; "or ''" catches None values from the database.
        self.hersteller_edit.setText(a.get("hersteller", "") or "")
        self.lieferant_edit.setText(a.get("lieferant", "") or "")

        # Prices: float() safely converts the DB value to a decimal number.
        # "or 0" prevents errors when the value is None.
        self.ek_spin.setValue(float(a.get("einkaufspreis", 0) or 0))
        self.vk_spin.setValue(float(a.get("verkaufspreis", 0) or 0))

        # Find the VAT rate as text in the dropdown (e.g. "19.0").
        mwst_idx = self.mwst_combo.findText(str(a.get("mwst_satz", 19.0)))
        if mwst_idx >= 0:
            self.mwst_combo.setCurrentIndex(mwst_idx)

        # Set stock quantity and minimum stock as integers.
        self.bestand_spin.setValue(int(a.get("lagerbestand", 0) or 0))
        self.mindest_spin.setValue(int(a.get("mindestbestand", 5) or 5))

        # Find the unit in the dropdown (e.g. "Stück").
        einheit_idx = self.einheit_combo.findText(a.get("einheit", "Stück"))
        if einheit_idx >= 0:
            self.einheit_combo.setCurrentIndex(einheit_idx)

        # Set the description as plain text (no HTML).
        self.beschr_edit.setPlainText(a.get("beschreibung", "") or "")

        # Active status: bool() converts 1 to True and 0 to False.
        self.aktiv_check.setChecked(bool(a.get("aktiv", 1)))

    def _speichern(self):
        """
        Read all input fields, validate the mandatory field and store the data
        in self.result_data before closing the dialog.

        Mandatory field: article name (must be filled in).

        After accept(), dlg.exec() returns the Accepted value so the calling
        code can save the data to the database.
        """
        # Read the article name (.strip() removes surrounding whitespace).
        bez = self.bez_edit.text().strip()
        # Read the sale price (decimal number).
        vk = self.vk_spin.value()

        # Mandatory field check: name must be present.
        if not bez:
            QMessageBox.warning(self, "Pflichtfeld", "Bitte eine Artikelbezeichnung eingeben.")
            return  # Exit the method early – dialog stays open.

        # Collect all form data into a dictionary.
        self.result_data = {
            "id":            self.artikel.get("id"),          # None for a new article.
            "bezeichnung":   bez,
            # currentData() returns the data value stored with addItem() (the ID).
            "kategorie_id":  self.kat_combo.currentData(),
            "hersteller":    self.hersteller_edit.text().strip(),
            "lieferant":     self.lieferant_edit.text().strip(),
            "einkaufspreis": self.ek_spin.value(),
            "verkaufspreis": vk,
            # Convert the VAT rate from the dropdown text to a decimal number.
            "mwst_satz":     float(self.mwst_combo.currentText()),
            "lagerbestand":  self.bestand_spin.value(),
            "mindestbestand": self.mindest_spin.value(),
            "einheit":       self.einheit_combo.currentText(),
            "beschreibung":  self.beschr_edit.toPlainText().strip(),
            # int() converts True/False from the checkbox to 1/0 (for the database).
            "aktiv":         int(self.aktiv_check.isChecked()),
        }

        # Close the dialog successfully.
        self.accept()
