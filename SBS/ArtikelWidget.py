"""
ArtikelWidget – Main article management widget (the "Articles" tab).

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Display a searchable and category-filterable table of all articles.
  - Show price (gross, including VAT) and a coloured status badge for each article.
  - Allow creating, editing and deleting articles.
  - Export the currently visible list to a CSV file.
  - Emit the artikel_geaendert signal after any data change.

Dependencies:
  - database (db): all SQLite operations
  - styles: centralised colour constants
  - SBS.ArtikelDialog: the dialog for creating / editing a single article
"""

import csv
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QDialog, QComboBox, QMessageBox, QAbstractItemView, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

import database as db
from styles import (
    COLOR_TEXT_LIGHT, COLOR_BORDER, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS
)
from SBS.ArtikelDialog import ArtikelDialog


class ArtikelWidget(QWidget):
    """
    Main widget for the "Articles" tab.

    Displays a searchable and category-filterable table of all articles.
    For each article, the gross sale price (including VAT) and a coloured
    status badge (Available / Reorder / Inactive) are shown.

    Signals:
        artikel_geaendert: Emitted after an article is created, edited or deleted.
                           Other parts of the application can receive this signal
                           and update themselves (e.g. the order form).
    """

    # Signal without parameters: only signals that something changed.
    artikel_geaendert = pyqtSignal()

    def __init__(self, parent=None):
        """
        Construct the ArtikelWidget.

        Builds the user interface and immediately loads all existing articles
        from the database.

        Args:
            parent (QWidget, optional): Parent widget.
        """
        # Initialise the parent class QWidget.
        super().__init__(parent)

        # Build the user interface.
        self._setup_ui()

        # Immediately populate the table with current database data.
        self.refresh()

    def _setup_ui(self):
        """
        Create the layout of the ArtikelWidget:

          1. Toolbar    – search bar + category filter dropdown + "New Article" button.
          2. Info row   – shows the number of results and reorder warnings.
          3. Table      – shows all articles with a status badge and action buttons.
        """
        # Main layout: arrange areas vertically.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # --- Toolbar ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Search bar in the rounded "pill" style.
        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            background: white;
            border: 1.5px solid {COLOR_BORDER};
            border-radius: 20px;
        """)
        search_frame.setFixedHeight(40)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(14, 0, 14, 0)
        # Magnifying glass as decoration (not a real icon widget).
        search_layout.addWidget(QLabel("🔍"))

        # Text input for the search term.
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Artikel suchen (Bezeichnung, Hersteller, Kategorie...)")
        self.search_edit.setFrame(False)
        self.search_edit.setStyleSheet("background: transparent; border: none; font-size: 13px;")
        # Update the table immediately on every keystroke.
        self.search_edit.textChanged.connect(self.refresh)
        search_layout.addWidget(self.search_edit)
        # stretch=1: the search bar takes all available space in the toolbar.
        toolbar.addWidget(search_frame, stretch=1)

        # Category filter dropdown next to the search bar.
        self.filter_combo = QComboBox()
        self.filter_combo.setFixedHeight(40)
        self.filter_combo.addItem("Alle Kategorien", "")   # Empty entry = no filter.
        # Load all categories from the database and add them as entries.
        for k in db.get_kategorien():
            self.filter_combo.addItem(k["name"], k["id"])
        # Update the table immediately when the selection changes.
        self.filter_combo.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.filter_combo)

        # "New Article" button.
        neu_btn = QPushButton("➕  Neuer Artikel")
        neu_btn.setObjectName("btn_primary")
        neu_btn.setFixedHeight(40)
        neu_btn.clicked.connect(self._neuer_artikel)
        toolbar.addWidget(neu_btn)

        # "Export CSV" button: saves the currently displayed article list as a CSV file.
        csv_btn = QPushButton("📥  CSV exportieren")
        csv_btn.setObjectName("btn_icon")  # Secondary styling.
        csv_btn.setFixedHeight(40)
        csv_btn.clicked.connect(self._exportiere_csv)
        toolbar.addWidget(csv_btn)

        layout.addLayout(toolbar)

        # --- Info row ---
        # Shows e.g. "24 articles found  ·  ⚠️ 3 below minimum stock".
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        layout.addWidget(self.info_lbl)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(10)   # 10 columns: 8 data + 1 status + 1 actions.

        # Set table column headers.
        self.table.setHorizontalHeaderLabels([
            "Art.-Nr.", "Bezeichnung", "Kategorie", "Hersteller",
            "EK", "VK (Brutto)", "Bestand", "Mind.", "Status", "Aktionen"
        ])

        # Zebra pattern: every other row has a different background.
        self.table.setAlternatingRowColors(True)

        # A click selects the entire row, not just one cell.
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # Cells cannot be edited directly in the table.
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Hide row numbers on the left side.
        self.table.verticalHeader().setVisible(False)

        # Hide grid lines for a modern look.
        self.table.setShowGrid(False)

        # All columns stretch evenly; individual columns are adjusted below.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Columns with short content: adapt to their content (ResizeToContents).
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Art.-Nr.
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # EK
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # VK
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Stock
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Min.
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Status
        # Actions column: fixed width.
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(9, 160)

        # Uniform row height for all rows.
        self.table.verticalHeader().setDefaultSectionSize(46)

        # Double-click opens the edit dialog for the clicked row.
        self.table.doubleClicked.connect(self._bearbeite_zeile)

        layout.addWidget(self.table)

    def refresh(self):
        """
        Load all articles from the database and repopulate the table.

        Takes the following into account:
          - The search term from the text field (full-text search in the database).
          - The selected category filter (client-side filtering).

        The info row shows the number of results and, if applicable, a warning
        for articles below the minimum stock level.

        Called:
          - On first load (in the constructor).
          - On keystroke in the search bar.
          - On change of the category filter.
          - After creating, editing or deleting an article.
        """
        # Get the search term from the input field.
        suche = self.search_edit.text().strip()

        # Load all articles matching the search term (database-side search).
        artikel = db.get_alle_artikel(suche)

        # --- Category filter (client-side) ---
        # currentData() returns the data value of the selected entry.
        # "" means "All categories" (no filter active).
        kat_filter = self.filter_combo.currentData()
        if kat_filter:
            # Read the currently selected category name.
            kat_name = self.filter_combo.currentText()
            # Filter the list: keep only articles whose category matches.
            # This is a list comprehension – shorthand for a for-loop with an if.
            artikel = [a for a in artikel if a.get("kategorie") == kat_name]

        # Number of articles that are below the minimum stock level (reorder flag).
        nachbestellen = sum(1 for a in artikel if a.get("nachbestellen"))

        # Build the info text.
        info = f"{len(artikel)} Artikel gefunden"
        if nachbestellen:
            # Append a warning if at least one article needs to be reordered.
            info += f"  ·  ⚠️ {nachbestellen} unter Mindestbestand"
        self.info_lbl.setText(info)

        # Adjust the number of table rows.
        self.table.setRowCount(len(artikel))

        # Fill each row with article data.
        for row, a in enumerate(artikel):
            # Calculate the gross sale price: net × (1 + VAT/100).
            # Example: 100 € × (1 + 19/100) = 100 € × 1.19 = 119 €.
            vk_brutto = a.get("verkaufspreis", 0) * (1 + a.get("mwst_satz", 19) / 100)

            # The 8 data values to display as a list.
            items = [
                a.get("artikelnummer", ""),
                a.get("bezeichnung", ""),
                a.get("kategorie") or "–",       # "–" if no value present.
                a.get("hersteller") or "–",
                f"€ {a.get('einkaufspreis', 0):.2f}",  # Formatted to 2 decimal places.
                f"€ {vk_brutto:.2f}",
                str(a.get("lagerbestand", 0)),
                str(a.get("mindestbestand", 0)),
            ]

            # Fill columns 0–7 with the data values.
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)

                # Store the invisible article ID in the cell (for later access).
                item.setData(Qt.ItemDataRole.UserRole, a["id"])

                # Align text left-justified and vertically centred.
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

                # Special treatment for the stock column (column 6):
                # If the article needs to be reordered, show the text in red and bold.
                if col == 6 and a.get("nachbestellen"):
                    item.setForeground(QColor(COLOR_DANGER))   # Red text colour.
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

                self.table.setItem(row, col, item)

            # --- Status badge (column 8) ---
            # A coloured label is not a normal table item, so we need a separate
            # widget as a container (setCellWidget).
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(6, 4, 6, 4)

            # Create the appropriate badge depending on the article status.
            if not a.get("aktiv", 1):
                # Article is deactivated (e.g. discontinued model).
                badge = QLabel("Inaktiv")
                badge.setStyleSheet(
                    "background:#f0f2f5; color:#6c757d; border-radius:8px; "
                    "padding:3px 8px; font-size:11px; font-weight:600;"
                )
            elif a.get("nachbestellen"):
                # Stock is below the minimum – show a warning.
                # "22" at the end of the colour = hex alpha value (approx. 13% opacity).
                # This produces a very transparent background in the warning colour.
                badge = QLabel("⚠ Nachbestellen")
                badge.setStyleSheet(
                    f"background:{COLOR_WARNING}22; color:{COLOR_WARNING}; "
                    "border-radius:8px; padding:3px 8px; font-size:11px; font-weight:600;"
                )
            else:
                # All good: article is active and sufficiently stocked.
                badge = QLabel("✓ Verfügbar")
                badge.setStyleSheet(
                    f"background:{COLOR_SUCCESS}22; color:{COLOR_SUCCESS}; "
                    "border-radius:8px; padding:3px 8px; font-size:11px; font-weight:600;"
                )

            status_layout.addWidget(badge)
            # Insert the badge widget into column 8 of the current row.
            self.table.setCellWidget(row, 8, status_widget)

            # --- Action buttons (column 9) ---
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(6, 4, 6, 4)
            btn_layout.setSpacing(6)

            # "Edit" button with stored article ID.
            edit_btn = QPushButton("✏️ Bearbeiten")
            edit_btn.setObjectName("btn_icon")
            edit_btn.setFixedHeight(30)
            # Store the article ID as a property so the slot knows which article is meant.
            edit_btn.setProperty("art_id", a["id"])
            edit_btn.clicked.connect(self._bearbeite_artikel)

            # "Delete" button (trash icon only, square).
            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("btn_danger")
            del_btn.setFixedSize(30, 30)
            del_btn.setProperty("art_id", a["id"])
            del_btn.clicked.connect(self._loesche_artikel)

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)

            # Insert the button widget into the action column of the current row.
            self.table.setCellWidget(row, 9, btn_widget)

    def _neuer_artikel(self):
        """
        Open ArtikelDialog to create a new article.

        After saving, the article is stored in the database, the table is
        refreshed and the artikel_geaendert signal is emitted.
        """
        # Open the dialog without existing article data (new article).
        dlg = ArtikelDialog(self)

        # exec() blocks until the dialog is closed.
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Write the form data from the dialog to the database.
            db.speichere_artikel(dlg.result_data)
            # Refresh the table so the new article appears.
            self.refresh()
            # Notify other widgets (e.g. the order form) about the change.
            self.artikel_geaendert.emit()

    def _bearbeite_zeile(self, index):
        """
        Called when the user double-clicks a table row.
        Opens ArtikelDialog for the article in the clicked row.

        Args:
            index (QModelIndex): Position of the clicked cell (contains row and column).
        """
        # Get the cell in column 0 of the clicked row.
        item = self.table.item(index.row(), 0)
        if item:
            # Read the hidden article ID from the cell and load the article data.
            a = db.get_artikel(item.data(Qt.ItemDataRole.UserRole))
            if a:
                dlg = ArtikelDialog(self, a)
                if dlg.exec() == QDialog.DialogCode.Accepted:
                    db.speichere_artikel(dlg.result_data)
                    self.refresh()
                    self.artikel_geaendert.emit()

    def _bearbeite_artikel(self):
        """
        Slot for the "Edit" button in the action column.

        self.sender() returns the button that emitted the signal.
        The correct article is loaded from the database via the stored "art_id" property.
        """
        # The button that triggered the click.
        btn = self.sender()

        # Load the article data via the ID stored in the button.
        a = db.get_artikel(btn.property("art_id"))
        if a:
            dlg = ArtikelDialog(self, a)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                db.speichere_artikel(dlg.result_data)
                self.refresh()
                self.artikel_geaendert.emit()

    def _loesche_artikel(self):
        """
        Slot for the "Delete" button in the action column.

        Shows a confirmation dialog first.  If the user confirms, the article is
        deleted.  Articles that are referenced in orders cannot be deleted – in
        that case an error message is shown.
        """
        # Determine the button and the associated article ID.
        btn = self.sender()
        a = db.get_artikel(btn.property("art_id"))
        if not a:
            return  # Article no longer exists – nothing to do.

        # Show a confirmation dialog; the default answer is "No" for safety.
        reply = QMessageBox.question(
            self, "Artikel löschen",
            f"Soll <b>{a['bezeichnung']}</b> gelöscht werden?<br>"
            "<small style='color:gray'>Artikel in Bestellungen können nicht gelöscht werden.</small>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No   # Safe default: No.
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Attempt to delete; returns True if successful.
            ok = db.loesche_artikel(btn.property("art_id"))
            if ok:
                # Refresh the table and notify other widgets.
                self.refresh()
                self.artikel_geaendert.emit()
            else:
                # Article is referenced in orders and cannot be deleted.
                QMessageBox.warning(self, "Nicht möglich",
                    "Dieser Artikel ist in Bestellungen vorhanden und kann nicht gelöscht werden.")

    def _exportiere_csv(self):
        """
        Export all currently displayed articles as a CSV file.

        The current search text and the selected category filter are taken into
        account – only the articles currently visible in the table are exported.

        The file is saved with a semicolon delimiter and UTF-8 BOM encoding so
        that Excel displays umlauts correctly.
        """
        # Open the file save dialog.
        pfad, _ = QFileDialog.getSaveFileName(
            self,
            "Artikel exportieren",
            "artikel_export.csv",
            "CSV-Dateien (*.csv)"
        )
        if not pfad:
            return  # Cancel pressed – do nothing.

        # Read the current search text and load articles from the database.
        suche = self.search_edit.text().strip()
        artikel = db.get_alle_artikel(suche)

        # Apply the category filter (same logic as in refresh()).
        kat_filter = self.filter_combo.currentData()
        if kat_filter:
            kat_name = self.filter_combo.currentText()
            # List comprehension: keep only articles in the selected category.
            artikel = [a for a in artikel if a.get("kategorie") == kat_name]

        try:
            with open(pfad, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")

                # Write the header row.
                writer.writerow([
                    "Artikelnummer", "Bezeichnung", "Kategorie", "Hersteller",
                    "Lieferant", "EK (€)", "VK Netto (€)", "VK Brutto (€)",
                    "MwSt. (%)", "Lagerbestand", "Mindestbestand", "Einheit", "Status"
                ])

                # Write one row per article.
                for a in artikel:
                    # Calculate the gross price: net × (1 + VAT/100).
                    vk_brutto = a.get("verkaufspreis", 0) * (1 + a.get("mwst_satz", 19) / 100)

                    # Determine the status as readable text.
                    if not a.get("aktiv", 1):
                        status = "Inaktiv"
                    elif a.get("nachbestellen"):
                        status = "Nachbestellen"
                    else:
                        status = "Verfügbar"

                    writer.writerow([
                        a.get("artikelnummer", ""),
                        a.get("bezeichnung", ""),
                        a.get("kategorie") or "",
                        a.get("hersteller") or "",
                        a.get("lieferant") or "",
                        # :.2f formats to exactly 2 decimal places.
                        f"{a.get('einkaufspreis', 0):.2f}",
                        f"{a.get('verkaufspreis', 0):.2f}",
                        f"{vk_brutto:.2f}",
                        a.get("mwst_satz", 19),
                        a.get("lagerbestand", 0),
                        a.get("mindestbestand", 0),
                        a.get("einheit", ""),
                        status,
                    ])

            # Show a success message.
            QMessageBox.information(
                self, "Export erfolgreich",
                f"{len(artikel)} Artikel wurden exportiert nach:\n{pfad}"
            )

        except Exception as fehler:
            # Show an error message if writing fails (e.g. missing permissions).
            QMessageBox.warning(self, "Fehler beim Export", str(fehler))
