"""
Radsport Koch GmbH – Artikelverwaltung
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QDialog, QTextEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QMessageBox, QCheckBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import database as db
from styles import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_DANGER, COLOR_WHITE,
    COLOR_TEXT_LIGHT, COLOR_BORDER, COLOR_WARNING, COLOR_SUCCESS
)


class ArtikelDialog(QDialog):
    def __init__(self, parent=None, artikel: dict = None):
        super().__init__(parent)
        self.artikel = artikel or {}
        self.setWindowTitle("Artikel bearbeiten" if artikel else "Neuen Artikel anlegen")
        self.setMinimumWidth(580)
        self.setModal(True)
        self._setup_ui()
        if artikel:
            self._fill_data()

    def _setup_ui(self):
        self.setStyleSheet(f"background: {COLOR_WHITE};")
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"background: {COLOR_PRIMARY};")
        header.setFixedHeight(64)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        title_lbl = QLabel("🚲  " + ("Artikel bearbeiten" if self.artikel else "Neuen Artikel anlegen"))
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLOR_WHITE};")
        h_layout.addWidget(title_lbl)
        layout.addWidget(header)

        # Form
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(24, 20, 24, 20)
        form_layout.setSpacing(12)

        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {COLOR_TEXT_LIGHT};")
            return l

        def row(*widgets):
            r = QHBoxLayout()
            r.setSpacing(12)
            for w in widgets:
                r.addWidget(w) if not isinstance(w, int) else r.addSpacing(w)
            return r

        # Bezeichnung + Kategorie
        self.bez_edit = QLineEdit()
        self.bez_edit.setPlaceholderText("Artikelbezeichnung *")
        self.kat_combo = QComboBox()
        self.kategorien = db.get_kategorien()
        self.kat_combo.addItem("-- Kategorie wählen --", None)
        for k in self.kategorien:
            self.kat_combo.addItem(k["name"], k["id"])

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
        r1.addLayout(col1, 2)
        r1.addLayout(col2, 1)
        form_layout.addLayout(r1)

        # Hersteller + Lieferant
        self.hersteller_edit = QLineEdit()
        self.hersteller_edit.setPlaceholderText("z.B. Shimano, Trek, Cube")
        self.lieferant_edit = QLineEdit()
        self.lieferant_edit.setPlaceholderText("Lieferantenname")

        r2 = QHBoxLayout()
        r2.setSpacing(12)
        col3 = QVBoxLayout(); col3.setSpacing(4)
        col3.addWidget(lbl("Hersteller")); col3.addWidget(self.hersteller_edit)
        col4 = QVBoxLayout(); col4.setSpacing(4)
        col4.addWidget(lbl("Lieferant")); col4.addWidget(self.lieferant_edit)
        r2.addLayout(col3)
        r2.addLayout(col4)
        form_layout.addLayout(r2)

        # Preise
        self.ek_spin = QDoubleSpinBox()
        self.ek_spin.setRange(0, 99999.99)
        self.ek_spin.setDecimals(2)
        self.ek_spin.setPrefix("€ ")
        self.ek_spin.setSingleStep(0.50)

        self.vk_spin = QDoubleSpinBox()
        self.vk_spin.setRange(0, 99999.99)
        self.vk_spin.setDecimals(2)
        self.vk_spin.setPrefix("€ ")
        self.vk_spin.setSingleStep(0.50)

        self.mwst_combo = QComboBox()
        self.mwst_combo.addItems(["19.0", "7.0", "0.0"])
        self.mwst_combo.setFixedWidth(80)

        r3 = QHBoxLayout(); r3.setSpacing(12)
        for lbl_t, widget in [("Einkaufspreis", self.ek_spin),
                                ("Verkaufspreis *", self.vk_spin),
                                ("MwSt. %", self.mwst_combo)]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(lbl(lbl_t)); col.addWidget(widget)
            r3.addLayout(col)
        form_layout.addLayout(r3)

        # Lager
        self.bestand_spin = QSpinBox()
        self.bestand_spin.setRange(0, 99999)
        self.mindest_spin = QSpinBox()
        self.mindest_spin.setRange(0, 9999)
        self.einheit_combo = QComboBox()
        self.einheit_combo.addItems(["Stück", "Paar", "Satz", "Meter", "Liter", "kg"])

        r4 = QHBoxLayout(); r4.setSpacing(12)
        for lbl_t, widget in [("Lagerbestand", self.bestand_spin),
                                ("Mindestbestand", self.mindest_spin),
                                ("Einheit", self.einheit_combo)]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(lbl(lbl_t)); col.addWidget(widget)
            r4.addLayout(col)
        form_layout.addLayout(r4)

        # Beschreibung
        self.beschr_edit = QTextEdit()
        self.beschr_edit.setPlaceholderText("Artikelbeschreibung, technische Details...")
        self.beschr_edit.setMaximumHeight(80)
        col_d = QVBoxLayout(); col_d.setSpacing(4)
        col_d.addWidget(lbl("Beschreibung")); col_d.addWidget(self.beschr_edit)
        form_layout.addLayout(col_d)

        # Aktiv-Checkbox
        self.aktiv_check = QCheckBox("Artikel ist aktiv / verkäuflich")
        self.aktiv_check.setChecked(True)
        form_layout.addWidget(self.aktiv_check)

        layout.addWidget(form_widget)

        # Buttons
        btn_frame = QFrame()
        btn_frame.setStyleSheet(f"background: #f8f9fa; border-top: 1px solid {COLOR_BORDER};")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(24, 14, 24, 14)
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
        a = self.artikel
        self.bez_edit.setText(a.get("bezeichnung", ""))
        idx = self.kat_combo.findData(a.get("kategorie_id"))
        if idx >= 0:
            self.kat_combo.setCurrentIndex(idx)
        self.hersteller_edit.setText(a.get("hersteller", "") or "")
        self.lieferant_edit.setText(a.get("lieferant", "") or "")
        self.ek_spin.setValue(float(a.get("einkaufspreis", 0) or 0))
        self.vk_spin.setValue(float(a.get("verkaufspreis", 0) or 0))
        mwst_idx = self.mwst_combo.findText(str(a.get("mwst_satz", 19.0)))
        if mwst_idx >= 0:
            self.mwst_combo.setCurrentIndex(mwst_idx)
        self.bestand_spin.setValue(int(a.get("lagerbestand", 0) or 0))
        self.mindest_spin.setValue(int(a.get("mindestbestand", 5) or 5))
        einheit_idx = self.einheit_combo.findText(a.get("einheit", "Stück"))
        if einheit_idx >= 0:
            self.einheit_combo.setCurrentIndex(einheit_idx)
        self.beschr_edit.setPlainText(a.get("beschreibung", "") or "")
        self.aktiv_check.setChecked(bool(a.get("aktiv", 1)))

    def _speichern(self):
        bez = self.bez_edit.text().strip()
        vk = self.vk_spin.value()
        if not bez:
            QMessageBox.warning(self, "Pflichtfeld", "Bitte eine Artikelbezeichnung eingeben.")
            return
        self.result_data = {
            "id":            self.artikel.get("id"),
            "bezeichnung":   bez,
            "kategorie_id":  self.kat_combo.currentData(),
            "hersteller":    self.hersteller_edit.text().strip(),
            "lieferant":     self.lieferant_edit.text().strip(),
            "einkaufspreis": self.ek_spin.value(),
            "verkaufspreis": vk,
            "mwst_satz":     float(self.mwst_combo.currentText()),
            "lagerbestand":  self.bestand_spin.value(),
            "mindestbestand": self.mindest_spin.value(),
            "einheit":       self.einheit_combo.currentText(),
            "beschreibung":  self.beschr_edit.toPlainText().strip(),
            "aktiv":         int(self.aktiv_check.isChecked()),
        }
        self.accept()


class ArtikelWidget(QWidget):
    artikel_geaendert = pyqtSignal()

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
        self.search_edit.setPlaceholderText("Artikel suchen (Bezeichnung, Hersteller, Kategorie...)")
        self.search_edit.setFrame(False)
        self.search_edit.setStyleSheet("background: transparent; border: none; font-size: 13px;")
        self.search_edit.textChanged.connect(self.refresh)
        search_layout.addWidget(self.search_edit)
        toolbar.addWidget(search_frame, stretch=1)

        self.filter_combo = QComboBox()
        self.filter_combo.setFixedHeight(40)
        self.filter_combo.addItem("Alle Kategorien", "")
        for k in db.get_kategorien():
            self.filter_combo.addItem(k["name"], k["id"])
        self.filter_combo.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.filter_combo)

        neu_btn = QPushButton("➕  Neuer Artikel")
        neu_btn.setObjectName("btn_primary")
        neu_btn.setFixedHeight(40)
        neu_btn.clicked.connect(self._neuer_artikel)
        toolbar.addWidget(neu_btn)

        layout.addLayout(toolbar)

        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        layout.addWidget(self.info_lbl)

        # Tabelle
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Art.-Nr.", "Bezeichnung", "Kategorie", "Hersteller",
            "EK", "VK (Brutto)", "Bestand", "Mind.", "Status", "Aktionen"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(9, 160)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.doubleClicked.connect(self._bearbeite_zeile)
        layout.addWidget(self.table)

    def refresh(self):
        suche = self.search_edit.text().strip()
        artikel = db.get_alle_artikel(suche)
        # Kategorie-Filter
        kat_filter = self.filter_combo.currentData()
        if kat_filter:
            kat_name = self.filter_combo.currentText()
            artikel = [a for a in artikel if a.get("kategorie") == kat_name]

        nachbestellen = sum(1 for a in artikel if a.get("nachbestellen"))
        info = f"{len(artikel)} Artikel gefunden"
        if nachbestellen:
            info += f"  ·  ⚠️ {nachbestellen} unter Mindestbestand"
        self.info_lbl.setText(info)

        self.table.setRowCount(len(artikel))
        for row, a in enumerate(artikel):
            vk_brutto = a.get("verkaufspreis", 0) * (1 + a.get("mwst_satz", 19) / 100)
            items = [
                a.get("artikelnummer", ""),
                a.get("bezeichnung", ""),
                a.get("kategorie") or "–",
                a.get("hersteller") or "–",
                f"€ {a.get('einkaufspreis', 0):.2f}",
                f"€ {vk_brutto:.2f}",
                str(a.get("lagerbestand", 0)),
                str(a.get("mindestbestand", 0)),
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, a["id"])
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                # Bestand rot wenn unter Mindest
                if col == 6 and a.get("nachbestellen"):
                    item.setForeground(QColor(COLOR_DANGER))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.table.setItem(row, col, item)

            # Status Badge
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(6, 4, 6, 4)
            if not a.get("aktiv", 1):
                badge = QLabel("Inaktiv")
                badge.setStyleSheet("background:#f0f2f5; color:#6c757d; border-radius:8px; padding:3px 8px; font-size:11px; font-weight:600;")
            elif a.get("nachbestellen"):
                badge = QLabel("⚠ Nachbestellen")
                badge.setStyleSheet(f"background:{COLOR_WARNING}22; color:{COLOR_WARNING}; border-radius:8px; padding:3px 8px; font-size:11px; font-weight:600;")
            else:
                badge = QLabel("✓ Verfügbar")
                badge.setStyleSheet(f"background:{COLOR_SUCCESS}22; color:{COLOR_SUCCESS}; border-radius:8px; padding:3px 8px; font-size:11px; font-weight:600;")
            status_layout.addWidget(badge)
            self.table.setCellWidget(row, 8, status_widget)

            # Aktionen
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(6, 4, 6, 4)
            btn_layout.setSpacing(6)

            edit_btn = QPushButton("✏️ Bearbeiten")
            edit_btn.setObjectName("btn_icon")
            edit_btn.setFixedHeight(30)
            edit_btn.setProperty("art_id", a["id"])
            edit_btn.clicked.connect(self._bearbeite_artikel)

            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("btn_danger")
            del_btn.setFixedSize(30, 30)
            del_btn.setProperty("art_id", a["id"])
            del_btn.clicked.connect(self._loesche_artikel)

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 9, btn_widget)

    def _neuer_artikel(self):
        dlg = ArtikelDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            db.speichere_artikel(dlg.result_data)
            self.refresh()
            self.artikel_geaendert.emit()

    def _bearbeite_zeile(self, index):
        item = self.table.item(index.row(), 0)
        if item:
            a = db.get_artikel(item.data(Qt.ItemDataRole.UserRole))
            if a:
                dlg = ArtikelDialog(self, a)
                if dlg.exec() == QDialog.DialogCode.Accepted:
                    db.speichere_artikel(dlg.result_data)
                    self.refresh()
                    self.artikel_geaendert.emit()

    def _bearbeite_artikel(self):
        btn = self.sender()
        a = db.get_artikel(btn.property("art_id"))
        if a:
            dlg = ArtikelDialog(self, a)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                db.speichere_artikel(dlg.result_data)
                self.refresh()
                self.artikel_geaendert.emit()

    def _loesche_artikel(self):
        btn = self.sender()
        a = db.get_artikel(btn.property("art_id"))
        if not a:
            return
        reply = QMessageBox.question(
            self, "Artikel löschen",
            f"Soll <b>{a['bezeichnung']}</b> gelöscht werden?<br>"
            "<small style='color:gray'>Artikel in Bestellungen können nicht gelöscht werden.</small>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok = db.loesche_artikel(btn.property("art_id"))
            if ok:
                self.refresh()
                self.artikel_geaendert.emit()
            else:
                QMessageBox.warning(self, "Nicht möglich",
                    "Dieser Artikel ist in Bestellungen vorhanden und kann nicht gelöscht werden.")
