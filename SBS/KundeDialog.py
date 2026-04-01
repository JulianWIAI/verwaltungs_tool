"""
KundeDialog – Modal dialog for creating and editing a customer record.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Display a form for entering or editing all customer fields (name, contact,
    address, date of birth, notes).
  - Validate mandatory fields (first name, last name) before saving.
  - Return the validated form data in result_data after accept().

Dependencies:
  - database (db): all SQLite operations
  - styles: centralised colour constants
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QTextEdit, QComboBox, QMessageBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from styles import (
    COLOR_PRIMARY, COLOR_WHITE, COLOR_TEXT_LIGHT, COLOR_BORDER
)


class KundeDialog(QDialog):
    """
    Modal dialog for creating a new customer or editing an existing one.

    A modal dialog blocks all other windows of the application while open –
    the user must save or cancel before continuing.

    Parameters:
        parent (QWidget, optional): The parent widget.
        kunde  (dict, optional):    Dictionary with the existing customer data.
                                    If None, an empty form for a new customer is shown.

    Attributes:
        kunde       (dict): The passed customer data (or {}).
        result_data (dict): After saving, this attribute holds all form data as a dict.
    """

    def __init__(self, parent=None, kunde: dict = None):
        """
        Construct the dialog.

        Calls the parent class constructor, stores the customer data, sets the
        window title and minimum width, then builds the user interface.

        Args:
            parent (QWidget, optional): Parent widget.
            kunde  (dict, optional):    Existing customer data for editing. None = new customer.
        """
        # Initialise the parent class – mandatory for every Qt class.
        super().__init__(parent)

        # Store customer data; "kunde or {}" yields {} when kunde is None.
        self.kunde = kunde or {}

        # Window title depends on the mode: edit or create.
        self.setWindowTitle("Kunde bearbeiten" if kunde else "Neuen Kunden anlegen")

        # Minimum window width in pixels.
        self.setMinimumWidth(520)

        # Mark the dialog as modal: it blocks the parent window.
        self.setModal(True)

        # Build all input fields and the layout.
        self._setup_ui()

        # If an existing customer was passed, fill the fields with their data.
        if kunde:
            self._fill_data()

    def _setup_ui(self):
        """
        Create and configure all widgets of the dialog.

        The dialog is divided into three areas:
          1. Header  – coloured title bar at the top.
          2. Form    – all input fields (name, contact, address, etc.).
          3. Buttons – "Cancel" and "Save" at the bottom.

        This method is called only once when the dialog is created.
        """
        # Set the background colour of the entire dialog to white.
        # The curly braces in f"QDialog {{ ... }}" must be doubled so Python
        # does not interpret them as format characters.
        self.setStyleSheet(f"QDialog {{ background: {COLOR_WHITE}; }}")

        # Main layout: arrange all three areas vertically.
        layout = QVBoxLayout(self)
        layout.setSpacing(0)          # No gap between areas.
        layout.setContentsMargins(0, 0, 0, 0)  # No outer margin.

        # --- Area 1: Header ---
        header = QFrame()
        # Primary colour as background; border-radius: 0 = no rounded corners.
        header.setStyleSheet(f"background: {COLOR_PRIMARY}; border-radius: 0;")
        header.setFixedHeight(64)     # Fixed height of 64 pixels.

        # Horizontal layout inside the header (for the title label).
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)  # Left/right padding of 24 px.

        # Title text with emoji icon; content depends on whether a customer is being edited.
        title = QLabel("👤  " + ("Kunde bearbeiten" if self.kunde else "Neuen Kunden anlegen"))
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_WHITE};")
        h_layout.addWidget(title)

        # Add the header to the main layout.
        layout.addWidget(header)

        # --- Area 2: Form ---
        form_widget = QWidget()
        form_widget.setObjectName("kunde_form")  # Name for the CSS selector (see below).
        # Only the widget with this object name gets a white background.
        form_widget.setStyleSheet(f"QWidget#kunde_form {{ background: {COLOR_WHITE}; }}")

        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(24, 20, 24, 20)  # Inner padding: top/bottom 20 px.
        form_layout.setSpacing(14)                       # Spacing between rows.

        # --- Helper function: create a form row ---
        def make_row(label_text, widget):
            """
            Create a vertical group consisting of a small uppercase label and
            the associated input widget.

            Args:
                label_text (str): Label text.
                widget (QWidget): Input widget (e.g. QLineEdit).

            Returns:
                QVBoxLayout: The finished layout containing the label and widget.
            """
            row = QVBoxLayout()

            # Small, bold label in uppercase.
            lbl = QLabel(label_text)
            lbl.setStyleSheet(
                f"font-size: 11px; font-weight: 600; color: {COLOR_TEXT_LIGHT}; "
                "text-transform: uppercase;"
            )
            row.addWidget(lbl)
            row.addWidget(widget)   # Input field below the label.
            return row

        # --- Form row: first name and last name ---
        # name_row is a horizontal layout: first name on the left, last name on the right.
        name_row = QHBoxLayout()
        name_row.setSpacing(12)   # 12 px gap between the two fields.

        # Input fields for first and last name.
        self.vorname_edit = QLineEdit()
        self.vorname_edit.setPlaceholderText("Vorname *")   # Grey hint text.
        self.nachname_edit = QLineEdit()
        self.nachname_edit.setPlaceholderText("Nachname *")

        # Add both fields with labels as columns into the row.
        name_row.addLayout(make_row("Vorname *", self.vorname_edit))
        name_row.addLayout(make_row("Nachname *", self.nachname_edit))
        form_layout.addLayout(name_row)

        # --- Form row: contact details ---
        kontakt_row = QHBoxLayout()
        kontakt_row.setSpacing(12)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@beispiel.de")
        self.telefon_edit = QLineEdit()
        self.telefon_edit.setPlaceholderText("0911 123456")

        kontakt_row.addLayout(make_row("E-Mail", self.email_edit))
        kontakt_row.addLayout(make_row("Telefon", self.telefon_edit))
        form_layout.addLayout(kontakt_row)

        # --- Form row: street ---
        # Street gets its own full-width row.
        self.strasse_edit = QLineEdit()
        self.strasse_edit.setPlaceholderText("Straße und Hausnummer")
        form_layout.addLayout(make_row("Straße", self.strasse_edit))

        # --- Form row: postcode, city, country ---
        adresse_row = QHBoxLayout()
        adresse_row.setSpacing(12)

        self.plz_edit = QLineEdit()
        self.plz_edit.setPlaceholderText("PLZ")
        self.plz_edit.setMaximumWidth(100)   # Postcode field is intentionally narrow.

        self.ort_edit = QLineEdit()
        self.ort_edit.setPlaceholderText("Ort")

        # Dropdown for country selection.
        self.land_combo = QComboBox()
        self.land_combo.addItems(["Deutschland", "Österreich", "Schweiz", "Anderes"])
        self.land_combo.setMaximumWidth(140)

        adresse_row.addLayout(make_row("PLZ", self.plz_edit))
        adresse_row.addLayout(make_row("Ort", self.ort_edit))
        adresse_row.addLayout(make_row("Land", self.land_combo))
        form_layout.addLayout(adresse_row)

        # --- Form row: date of birth ---
        self.geb_edit = QDateEdit()
        self.geb_edit.setDisplayFormat("dd.MM.yyyy")  # Display in German date format.
        self.geb_edit.setCalendarPopup(True)           # Enable calendar popup.
        self.geb_edit.setDate(QDate(1990, 1, 1))       # Default value: 01.01.1990.
        self.geb_edit.setMaximumWidth(160)
        form_layout.addLayout(make_row("Geburtsdatum", self.geb_edit))

        # --- Form row: notes ---
        # QTextEdit allows multi-line text (unlike QLineEdit).
        self.notizen_edit = QTextEdit()
        self.notizen_edit.setPlaceholderText("Interne Notizen zum Kunden...")
        self.notizen_edit.setMaximumHeight(80)  # Limit height to keep the dialog compact.
        form_layout.addLayout(make_row("Notizen", self.notizen_edit))

        # Add the completed form widget to the main layout.
        layout.addWidget(form_widget)

        # --- Area 3: Buttons (Cancel / Save) ---
        btn_frame = QFrame()
        btn_frame.setObjectName("kunde_btn_frame")
        # Light grey background with a separator line at the top.
        btn_frame.setStyleSheet(
            f"QFrame#kunde_btn_frame {{ background: #f8f9fa; border-top: 1px solid {COLOR_BORDER}; }}"
        )
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(24, 14, 24, 14)
        btn_layout.setSpacing(10)
        btn_layout.addStretch()   # Empty placeholder pushes buttons to the right.

        # "Cancel" button: closes the dialog without saving (reject()).
        abbruch_btn = QPushButton("Abbrechen")
        abbruch_btn.setObjectName("btn_icon")  # CSS class for styling.
        abbruch_btn.setFixedHeight(38)
        # reject() is a built-in QDialog method – sets the result to "Rejected".
        abbruch_btn.clicked.connect(self.reject)

        # "Save" button: calls the internal _speichern() method.
        speichern_btn = QPushButton("💾  Speichern")
        speichern_btn.setObjectName("btn_primary")
        speichern_btn.setFixedHeight(38)
        speichern_btn.clicked.connect(self._speichern)

        btn_layout.addWidget(abbruch_btn)
        btn_layout.addWidget(speichern_btn)
        layout.addWidget(btn_frame)

    def _fill_data(self):
        """
        Fill all input fields with the data of the customer being edited.

        This method is only called when an existing customer dictionary was
        passed at dialog creation time.  Values are read with .get() which
        returns "" instead of raising an error when a key is missing.
        """
        # Fill text fields directly with the stored values.
        self.vorname_edit.setText(self.kunde.get("vorname", ""))
        self.nachname_edit.setText(self.kunde.get("nachname", ""))
        self.email_edit.setText(self.kunde.get("email", ""))
        self.telefon_edit.setText(self.kunde.get("telefon", ""))
        self.strasse_edit.setText(self.kunde.get("strasse", ""))
        self.plz_edit.setText(self.kunde.get("plz", ""))
        self.ort_edit.setText(self.kunde.get("ort", ""))

        # Find and select the country in the dropdown.
        # findText() returns the index of the entry, or -1 if not found.
        idx = self.land_combo.findText(self.kunde.get("land", "Deutschland"))
        if idx >= 0:
            self.land_combo.setCurrentIndex(idx)  # Select the found entry.

        # Convert the date of birth from the database format "yyyy-MM-dd".
        geb = self.kunde.get("geburtsdatum", "")
        if geb:
            try:
                # QDate.fromString() converts the string to a QDate object.
                d = QDate.fromString(geb, "yyyy-MM-dd")
                if d.isValid():   # Only set if the date is valid.
                    self.geb_edit.setDate(d)
            except Exception:
                # On unexpected error (e.g. corrupt data), keep the default date
                # rather than crashing.
                pass

        # Fill the multi-line notes field with plain text (no HTML).
        self.notizen_edit.setPlainText(self.kunde.get("notizen", ""))

    def _speichern(self):
        """
        Read all input fields, validate mandatory fields, and store the data in
        self.result_data before closing the dialog with accept().

        Mandatory fields: first name and last name.  If either is missing, a
        warning message is shown and the dialog stays open.

        After accept() is called, dlg.exec() returns QDialog.DialogCode.Accepted,
        signalling to the caller that the user pressed Save.
        """
        # Read inputs; .strip() removes leading/trailing whitespace.
        vorname = self.vorname_edit.text().strip()
        nachname = self.nachname_edit.text().strip()

        # Mandatory field check: both fields must contain a value.
        if not vorname or not nachname:
            # Show a warning dialog and exit the method early (dialog stays open).
            QMessageBox.warning(self, "Pflichtfelder", "Bitte Vor- und Nachname eingeben.")
            return  # Dialog stays open; nothing is saved.

        # Collect all form data into a dictionary.
        # This dict is later passed to the database function.
        self.result_data = {
            "id":          self.kunde.get("id"),          # None for a new customer.
            "vorname":     vorname,
            "nachname":    nachname,
            "email":       self.email_edit.text().strip(),
            "telefon":     self.telefon_edit.text().strip(),
            "strasse":     self.strasse_edit.text().strip(),
            "plz":         self.plz_edit.text().strip(),
            "ort":         self.ort_edit.text().strip(),
            "land":        self.land_combo.currentText(),  # Currently selected entry.
            # Convert the date back to the database format "yyyy-MM-dd".
            "geburtsdatum": self.geb_edit.date().toString("yyyy-MM-dd"),
            "notizen":     self.notizen_edit.toPlainText().strip(),
        }

        # Close the dialog successfully – signals to the caller: "Save was pressed".
        self.accept()
