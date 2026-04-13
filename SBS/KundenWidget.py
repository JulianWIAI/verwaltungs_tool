"""
KundenWidget – Main customer management widget (the "Customers" tab).

Part of the Radsport Koch GmbH management system.

Responsibilities:
  - Display a searchable table of all customers.
  - Allow creating, editing and deleting customers.
  - Export the currently visible list to a CSV file.
  - Emit the kunden_geaendert signal after any data change.

Note: Login protection for customer data has been moved to the online web portal.
      The desktop Verwaltungstool is for internal staff only.
"""

import csv
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QDialog, QMessageBox, QAbstractItemView, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal

import database as db
from styles import COLOR_TEXT_LIGHT, COLOR_BORDER
from SBS.KundeDialog import KundeDialog


class KundenWidget(QWidget):
    """
    Main widget for the "Customers" tab of the internal management tool.

    Displays a searchable table of all customers with action buttons.

    Signals:
        kunden_geaendert: Emitted after a customer is created, edited or deleted.
    """

    kunden_geaendert = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    # ──────────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            background: white;
            border: 1.5px solid {COLOR_BORDER};
            border-radius: 20px;
        """)
        search_frame.setFixedHeight(40)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(14, 0, 14, 0)
        search_layout.addWidget(QLabel("🔍"))

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Kunden suchen (Name, E-Mail, Ort…)")
        self.search_edit.setFrame(False)
        self.search_edit.setStyleSheet("background: transparent; border: none; font-size: 13px;")
        self.search_edit.textChanged.connect(self.refresh)
        search_layout.addWidget(self.search_edit)
        toolbar.addWidget(search_frame, stretch=1)

        self.neu_btn = QPushButton("➕  Neuer Kunde")
        self.neu_btn.setObjectName("btn_primary")
        self.neu_btn.setFixedHeight(40)
        self.neu_btn.clicked.connect(self._neuer_kunde)
        toolbar.addWidget(self.neu_btn)

        csv_btn = QPushButton("📥  CSV exportieren")
        csv_btn.setObjectName("btn_icon")
        csv_btn.setFixedHeight(40)
        csv_btn.clicked.connect(self._exportiere_csv)
        toolbar.addWidget(csv_btn)

        layout.addLayout(toolbar)

        # ── Info row ──────────────────────────────────────────────────────────
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        layout.addWidget(self.info_lbl)

        # ── Table ─────────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Nr.", "Vorname", "Nachname", "E-Mail", "Telefon",
            "PLZ", "Ort", "Erstellt", "Aktionen"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 160)
        self.table.setRowHeight(0, 48)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.doubleClicked.connect(self._bearbeite_zeile)
        layout.addWidget(self.table)

    # ──────────────────────────────────────────────────────────────────────────
    # Data loading
    # ──────────────────────────────────────────────────────────────────────────

    def refresh(self):
        suche = self.search_edit.text().strip()
        kunden = db.get_alle_kunden(suche)
        self.info_lbl.setText(f"{len(kunden)} Kunde(n) gefunden")
        self.table.setRowCount(len(kunden))

        for row, k in enumerate(kunden):
            items = [
                k.get("kundennummer", ""),
                k.get("vorname", ""),
                k.get("nachname", ""),
                k.get("email", ""),
                k.get("telefon", ""),
                k.get("plz", ""),
                k.get("ort", ""),
                (k.get("erstellt_am", "") or "")[:10],
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text or "")
                item.setData(Qt.ItemDataRole.UserRole, k["id"])
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, col, item)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(6, 4, 6, 4)
            btn_layout.setSpacing(6)

            edit_btn = QPushButton("✏️ Bearbeiten")
            edit_btn.setObjectName("btn_icon")
            edit_btn.setFixedHeight(30)
            edit_btn.setProperty("kunde_id", k["id"])
            edit_btn.clicked.connect(self._bearbeite_kunde)

            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("btn_danger")
            del_btn.setFixedSize(30, 30)
            del_btn.setProperty("kunde_id", k["id"])
            del_btn.clicked.connect(self._loesche_kunde)

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 8, btn_widget)

    # ──────────────────────────────────────────────────────────────────────────
    # Slots
    # ──────────────────────────────────────────────────────────────────────────

    def _neuer_kunde(self):
        dlg = KundeDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            db.speichere_kunde(dlg.result_data)
            self.refresh()
            self.kunden_geaendert.emit()

    def _bearbeite_zeile(self, index):
        item = self.table.item(index.row(), 0)
        if item:
            k = db.get_kunde(item.data(Qt.ItemDataRole.UserRole))
            if k:
                dlg = KundeDialog(self, k)
                if dlg.exec() == QDialog.DialogCode.Accepted:
                    db.speichere_kunde(dlg.result_data)
                    self.refresh()
                    self.kunden_geaendert.emit()

    def _bearbeite_kunde(self):
        btn = self.sender()
        k = db.get_kunde(btn.property("kunde_id"))
        if k:
            dlg = KundeDialog(self, k)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                db.speichere_kunde(dlg.result_data)
                self.refresh()
                self.kunden_geaendert.emit()

    def _loesche_kunde(self):
        btn = self.sender()
        kid = btn.property("kunde_id")
        k = db.get_kunde(kid)
        if not k:
            return
        reply = QMessageBox.question(
            self, "Kunden löschen",
            f"Soll <b>{k['vorname']} {k['nachname']}</b> wirklich gelöscht werden?<br>"
            "<small style='color:gray'>Kunden mit Bestellungen können nicht gelöscht werden.</small>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok = db.loesche_kunde(kid)
            if ok:
                self.refresh()
                self.kunden_geaendert.emit()
            else:
                QMessageBox.warning(
                    self, "Nicht möglich",
                    "Dieser Kunde hat noch Bestellungen und kann nicht gelöscht werden."
                )

    def _exportiere_csv(self):
        pfad, _ = QFileDialog.getSaveFileName(
            self, "Kunden exportieren", "kunden_export.csv", "CSV-Dateien (*.csv)"
        )
        if not pfad:
            return
        kunden = db.get_alle_kunden(self.search_edit.text().strip())
        try:
            with open(pfad, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow([
                    "Kundennummer", "Vorname", "Nachname", "E-Mail",
                    "Telefon", "Straße", "PLZ", "Ort", "Land",
                    "Geburtsdatum", "Erstellt am"
                ])
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
                        (k.get("erstellt_am", "") or "")[:10],
                    ])
            QMessageBox.information(
                self, "Export erfolgreich",
                f"{len(kunden)} Kunde(n) wurden exportiert nach:\n{pfad}"
            )
        except Exception as fehler:
            QMessageBox.warning(self, "Fehler beim Export", str(fehler))