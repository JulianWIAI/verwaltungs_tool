"""
Radsport Koch GmbH – Kundenverwaltung
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QDialog, QFormLayout, QTextEdit, QComboBox,
    QMessageBox, QSizePolicy, QDateEdit, QAbstractItemView
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QColor
import database as db
from styles import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_SUCCESS, COLOR_DANGER,
    COLOR_WHITE, COLOR_BG, COLOR_TEXT_LIGHT, COLOR_BORDER, COLOR_WARNING
)


class KundeDialog(QDialog):
    def __init__(self, parent=None, kunde: dict = None):
        super().__init__(parent)
        self.kunde = kunde or {}
        self.setWindowTitle("Kunde bearbeiten" if kunde else "Neuen Kunden anlegen")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._setup_ui()
        if kunde:
            self._fill_data()

    def _setup_ui(self):
        self.setStyleSheet(f"background: {COLOR_WHITE};")
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"background: {COLOR_PRIMARY}; border-radius: 0;")
        header.setFixedHeight(64)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        title = QLabel("👤  " + ("Kunde bearbeiten" if self.kunde else "Neuen Kunden anlegen"))
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_WHITE};")
        h_layout.addWidget(title)
        layout.addWidget(header)

        # Form
        form_widget = QWidget()
        form_widget.setStyleSheet(f"background: {COLOR_WHITE};")
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(24, 20, 24, 20)
        form_layout.setSpacing(14)

        def make_row(label_text, widget):
            row = QVBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {COLOR_TEXT_LIGHT}; text-transform: uppercase;")
            row.addWidget(lbl)
            row.addWidget(widget)
            return row

        # Name Zeile
        name_row = QHBoxLayout()
        name_row.setSpacing(12)
        self.vorname_edit = QLineEdit()
        self.vorname_edit.setPlaceholderText("Vorname *")
        self.nachname_edit = QLineEdit()
        self.nachname_edit.setPlaceholderText("Nachname *")
        name_row.addLayout(make_row("Vorname *", self.vorname_edit))
        name_row.addLayout(make_row("Nachname *", self.nachname_edit))
        form_layout.addLayout(name_row)

        # Kontakt
        kontakt_row = QHBoxLayout()
        kontakt_row.setSpacing(12)
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@beispiel.de")
        self.telefon_edit = QLineEdit()
        self.telefon_edit.setPlaceholderText("0911 123456")
        kontakt_row.addLayout(make_row("E-Mail", self.email_edit))
        kontakt_row.addLayout(make_row("Telefon", self.telefon_edit))
        form_layout.addLayout(kontakt_row)

        # Adresse
        self.strasse_edit = QLineEdit()
        self.strasse_edit.setPlaceholderText("Straße und Hausnummer")
        form_layout.addLayout(make_row("Straße", self.strasse_edit))

        adresse_row = QHBoxLayout()
        adresse_row.setSpacing(12)
        self.plz_edit = QLineEdit()
        self.plz_edit.setPlaceholderText("PLZ")
        self.plz_edit.setMaximumWidth(100)
        self.ort_edit = QLineEdit()
        self.ort_edit.setPlaceholderText("Ort")
        self.land_combo = QComboBox()
        self.land_combo.addItems(["Deutschland", "Österreich", "Schweiz", "Anderes"])
        self.land_combo.setMaximumWidth(140)
        adresse_row.addLayout(make_row("PLZ", self.plz_edit))
        adresse_row.addLayout(make_row("Ort", self.ort_edit))
        adresse_row.addLayout(make_row("Land", self.land_combo))
        form_layout.addLayout(adresse_row)

        # Geburtsdatum
        self.geb_edit = QDateEdit()
        self.geb_edit.setDisplayFormat("dd.MM.yyyy")
        self.geb_edit.setCalendarPopup(True)
        self.geb_edit.setDate(QDate(1990, 1, 1))
        self.geb_edit.setMaximumWidth(160)
        form_layout.addLayout(make_row("Geburtsdatum", self.geb_edit))

        # Notizen
        self.notizen_edit = QTextEdit()
        self.notizen_edit.setPlaceholderText("Interne Notizen zum Kunden...")
        self.notizen_edit.setMaximumHeight(80)
        form_layout.addLayout(make_row("Notizen", self.notizen_edit))

        layout.addWidget(form_widget)

        # Buttons
        btn_frame = QFrame()
        btn_frame.setStyleSheet(f"background: #f8f9fa; border-top: 1px solid {COLOR_BORDER};")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(24, 14, 24, 14)
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        abbruch_btn = QPushButton("Abbrechen")
        abbruch_btn.setObjectName("btn_icon")
        abbruch_btn.setFixedHeight(38)
        abbruch_btn.clicked.connect(self.reject)

        speichern_btn = QPushButton("💾  Speichern")
        speichern_btn.setObjectName("btn_primary")
        speichern_btn.setFixedHeight(38)
        speichern_btn.clicked.connect(self._speichern)

        btn_layout.addWidget(abbruch_btn)
        btn_layout.addWidget(speichern_btn)
        layout.addWidget(btn_frame)

    def _fill_data(self):
        self.vorname_edit.setText(self.kunde.get("vorname", ""))
        self.nachname_edit.setText(self.kunde.get("nachname", ""))
        self.email_edit.setText(self.kunde.get("email", ""))
        self.telefon_edit.setText(self.kunde.get("telefon", ""))
        self.strasse_edit.setText(self.kunde.get("strasse", ""))
        self.plz_edit.setText(self.kunde.get("plz", ""))
        self.ort_edit.setText(self.kunde.get("ort", ""))
        idx = self.land_combo.findText(self.kunde.get("land", "Deutschland"))
        if idx >= 0:
            self.land_combo.setCurrentIndex(idx)
        geb = self.kunde.get("geburtsdatum", "")
        if geb:
            try:
                d = QDate.fromString(geb, "yyyy-MM-dd")
                if d.isValid():
                    self.geb_edit.setDate(d)
            except Exception:
                pass
        self.notizen_edit.setPlainText(self.kunde.get("notizen", ""))

    def _speichern(self):
        vorname = self.vorname_edit.text().strip()
        nachname = self.nachname_edit.text().strip()
        if not vorname or not nachname:
            QMessageBox.warning(self, "Pflichtfelder", "Bitte Vor- und Nachname eingeben.")
            return
        self.result_data = {
            "id":          self.kunde.get("id"),
            "vorname":     vorname,
            "nachname":    nachname,
            "email":       self.email_edit.text().strip(),
            "telefon":     self.telefon_edit.text().strip(),
            "strasse":     self.strasse_edit.text().strip(),
            "plz":         self.plz_edit.text().strip(),
            "ort":         self.ort_edit.text().strip(),
            "land":        self.land_combo.currentText(),
            "geburtsdatum": self.geb_edit.date().toString("yyyy-MM-dd"),
            "notizen":     self.notizen_edit.toPlainText().strip(),
        }
        self.accept()


class KundenWidget(QWidget):
    kunden_geaendert = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Suchleiste
        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            background: white;
            border: 1.5px solid {COLOR_BORDER};
            border-radius: 20px;
        """)
        search_frame.setFixedHeight(40)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(14, 0, 14, 0)
        search_icon = QLabel("🔍")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Kunden suchen (Name, E-Mail, Ort...)")
        self.search_edit.setFrame(False)
        self.search_edit.setStyleSheet("background: transparent; border: none; font-size: 13px;")
        self.search_edit.textChanged.connect(self.refresh)
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_edit)
        toolbar.addWidget(search_frame, stretch=1)

        self.neu_btn = QPushButton("➕  Neuer Kunde")
        self.neu_btn.setObjectName("btn_primary")
        self.neu_btn.setFixedHeight(40)
        self.neu_btn.clicked.connect(self._neuer_kunde)
        toolbar.addWidget(self.neu_btn)

        layout.addLayout(toolbar)

        # Info-Zeile
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        layout.addWidget(self.info_lbl)

        # Tabelle
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

    def refresh(self):
        suche = self.search_edit.text().strip()
        kunden = db.get_alle_kunden(suche)
        self.info_lbl.setText(f"{len(kunden)} Kunde(n) gefunden")
        self.table.setRowCount(len(kunden))
        for row, k in enumerate(kunden):
            items = [
                k.get("kundennummer",""),
                k.get("vorname",""),
                k.get("nachname",""),
                k.get("email",""),
                k.get("telefon",""),
                k.get("plz",""),
                k.get("ort",""),
                (k.get("erstellt_am","") or "")[:10],
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text or "")
                item.setData(Qt.ItemDataRole.UserRole, k["id"])
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, col, item)

            # Aktionen
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
        kid = btn.property("kunde_id")
        k = db.get_kunde(kid)
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
