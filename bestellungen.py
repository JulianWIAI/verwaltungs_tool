"""
Radsport Koch GmbH – Bestellverwaltung
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QDialog, QComboBox, QTextEdit, QDoubleSpinBox,
    QSpinBox, QMessageBox, QSizePolicy, QScrollArea, QAbstractItemView,
    QDateEdit, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor
import database as db
from styles import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_DANGER, COLOR_WHITE,
    COLOR_BG, COLOR_TEXT_LIGHT, COLOR_BORDER, COLOR_WARNING,
    COLOR_SUCCESS, STATUS_FARBEN, ZAHLUNG_FARBEN, COLOR_INFO
)


class PositionenTabelle(QWidget):
    """Wiederverwendbares Widget für Bestellpositionen mit Live-Summe."""

    geaendert = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.artikel_liste = db.get_alle_artikel(nur_aktiv=True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Artikel hinzufügen
        add_row = QHBoxLayout()
        add_row.setSpacing(8)

        self.art_combo = QComboBox()
        self.art_combo.setMinimumWidth(280)
        self.art_combo.addItem("-- Artikel wählen --", None)
        for a in self.artikel_liste:
            self.art_combo.addItem(
                f"{a['artikelnummer']}  |  {a['bezeichnung']}  (€ {a['verkaufspreis']:.2f})",
                a
            )

        self.menge_spin = QSpinBox()
        self.menge_spin.setRange(1, 9999)
        self.menge_spin.setValue(1)
        self.menge_spin.setFixedWidth(80)

        self.einzelpreis_spin = QDoubleSpinBox()
        self.einzelpreis_spin.setRange(0, 99999.99)
        self.einzelpreis_spin.setDecimals(2)
        self.einzelpreis_spin.setPrefix("€ ")
        self.einzelpreis_spin.setFixedWidth(120)

        self.art_combo.currentIndexChanged.connect(self._art_selected)

        add_btn = QPushButton("➕ Position hinzufügen")
        add_btn.setObjectName("btn_secondary")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._position_hinzufuegen)

        add_row.addWidget(self.art_combo, 2)
        add_row.addWidget(QLabel("Menge:"))
        add_row.addWidget(self.menge_spin)
        add_row.addWidget(QLabel("Preis:"))
        add_row.addWidget(self.einzelpreis_spin)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        # Tabelle
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Art.-Nr.", "Bezeichnung", "Menge", "Einzelpreis", "Gesamt (Netto)", ""
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 40)
        self.table.setMaximumHeight(220)
        layout.addWidget(self.table)

        # Summenzeile
        sum_row = QHBoxLayout()
        sum_row.addStretch()
        self.summe_lbl = QLabel("Zwischensumme Netto: € 0,00")
        self.summe_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.summe_lbl.setStyleSheet(f"color: {COLOR_PRIMARY};")
        sum_row.addWidget(self.summe_lbl)
        layout.addLayout(sum_row)

        self.positionen = []  # interne Liste

    def _art_selected(self, idx):
        art = self.art_combo.currentData()
        if art:
            self.einzelpreis_spin.setValue(float(art.get("verkaufspreis", 0)))

    def _position_hinzufuegen(self):
        art = self.art_combo.currentData()
        if not art:
            return
        menge = self.menge_spin.value()
        preis = self.einzelpreis_spin.value()

        # Prüfen ob bereits vorhanden
        for p in self.positionen:
            if p["artikel_id"] == art["id"]:
                p["menge"] += menge
                self._render()
                self.geaendert.emit()
                return

        self.positionen.append({
            "artikel_id":   art["id"],
            "artikelnummer": art.get("artikelnummer",""),
            "bezeichnung":  art.get("bezeichnung",""),
            "menge":        menge,
            "einzelpreis":  preis,
            "mwst_satz":    float(art.get("mwst_satz", 19)),
        })
        self._render()
        self.geaendert.emit()

    def _render(self):
        self.table.setRowCount(len(self.positionen))
        gesamt_netto = 0.0
        for row, p in enumerate(self.positionen):
            netto = p["menge"] * p["einzelpreis"]
            gesamt_netto += netto
            self.table.setItem(row, 0, QTableWidgetItem(p.get("artikelnummer","")))
            self.table.setItem(row, 1, QTableWidgetItem(p.get("bezeichnung","")))
            self.table.setItem(row, 2, QTableWidgetItem(str(p["menge"])))
            self.table.setItem(row, 3, QTableWidgetItem(f"€ {p['einzelpreis']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"€ {netto:.2f}"))

            del_btn = QPushButton("✕")
            del_btn.setStyleSheet(f"color: {COLOR_DANGER}; background: transparent; border: none; font-weight: bold;")
            del_btn.setProperty("pos_idx", row)
            del_btn.clicked.connect(self._loesche_position)
            self.table.setCellWidget(row, 5, del_btn)

        self.summe_lbl.setText(f"Zwischensumme Netto: € {gesamt_netto:,.2f}")

    def _loesche_position(self):
        idx = self.sender().property("pos_idx")
        if 0 <= idx < len(self.positionen):
            self.positionen.pop(idx)
            self._render()
            self.geaendert.emit()

    def set_positionen(self, positionen: list):
        self.positionen = []
        for p in positionen:
            self.positionen.append({
                "artikel_id":    p["artikel_id"],
                "artikelnummer": p.get("artikelnummer",""),
                "bezeichnung":   p.get("bezeichnung",""),
                "menge":         p["menge"],
                "einzelpreis":   p["einzelpreis"],
                "mwst_satz":     p.get("mwst_satz", 19),
            })
        self._render()

    def get_positionen(self) -> list:
        return self.positionen

    def get_netto(self) -> float:
        return sum(p["menge"] * p["einzelpreis"] for p in self.positionen)


class BestellungDialog(QDialog):
    def __init__(self, parent=None, bestellung: dict = None):
        super().__init__(parent)
        self.bestellung = bestellung or {}
        self.setWindowTitle("Bestellung bearbeiten" if bestellung else "Neue Bestellung anlegen")
        self.setMinimumWidth(720)
        self.setMinimumHeight(700)
        self.setModal(True)
        self._setup_ui()
        if bestellung:
            self._fill_data()
        self._update_summe()

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
        title_lbl = QLabel("📦  " + ("Bestellung bearbeiten" if self.bestellung else "Neue Bestellung"))
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLOR_WHITE};")
        h_layout.addWidget(title_lbl)
        layout.addWidget(header)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(16)

        def section(text):
            lbl = QLabel(text)
            lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            lbl.setStyleSheet(f"""
                color: {COLOR_PRIMARY};
                border-bottom: 2px solid {COLOR_SECONDARY};
                padding-bottom: 4px;
            """)
            return lbl

        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {COLOR_TEXT_LIGHT};")
            return l

        # ── Kunde
        content_layout.addWidget(section("👤 Kunde"))
        kunde_row = QHBoxLayout()
        self.kunden = db.get_alle_kunden()
        self.kunde_combo = QComboBox()
        self.kunde_combo.addItem("-- Kunden wählen --", None)
        for k in self.kunden:
            self.kunde_combo.addItem(
                f"{k['kundennummer']}  |  {k['vorname']} {k['nachname']}  ({k.get('ort','')})",
                k["id"]
            )
        self.kunde_combo.currentIndexChanged.connect(self._update_lieferadresse)
        col_k = QVBoxLayout(); col_k.setSpacing(4)
        col_k.addWidget(lbl("Kunde *")); col_k.addWidget(self.kunde_combo)
        kunde_row.addLayout(col_k, 2)

        self.liefer_edit = QLineEdit()
        self.liefer_edit.setPlaceholderText("Wird automatisch befüllt oder manuell eingeben")
        col_l = QVBoxLayout(); col_l.setSpacing(4)
        col_l.addWidget(lbl("Lieferadresse"))
        col_l.addWidget(self.liefer_edit)
        kunde_row.addLayout(col_l, 2)
        content_layout.addLayout(kunde_row)

        # ── Status & Zahlung
        content_layout.addWidget(section("📋 Status & Zahlung"))
        status_row = QHBoxLayout(); status_row.setSpacing(12)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Neu","In Bearbeitung","Versendet","Geliefert","Storniert","Zurückgegeben"])

        self.zahlung_combo = QComboBox()
        self.zahlung_combo.addItems(["Bar","EC-Karte","Kreditkarte","Überweisung","Rechnung","PayPal"])

        self.zahlstatus_combo = QComboBox()
        self.zahlstatus_combo.addItems(["Offen","Teilbezahlt","Bezahlt","Erstattet"])

        self.liefer_datum = QDateEdit()
        self.liefer_datum.setDisplayFormat("dd.MM.yyyy")
        self.liefer_datum.setCalendarPopup(True)
        self.liefer_datum.setDate(QDate.currentDate().addDays(7))

        for lbl_t, widget in [("Bestellstatus", self.status_combo),
                                ("Zahlungsart", self.zahlung_combo),
                                ("Zahlungsstatus", self.zahlstatus_combo),
                                ("Lieferdatum", self.liefer_datum)]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(lbl(lbl_t)); col.addWidget(widget)
            status_row.addLayout(col)
        content_layout.addLayout(status_row)

        # ── Artikel / Positionen
        content_layout.addWidget(section("🛒 Bestellpositionen"))
        self.positionen_widget = PositionenTabelle(self)
        self.positionen_widget.geaendert.connect(self._update_summe)
        content_layout.addWidget(self.positionen_widget)

        # ── Konditionen
        cond_row = QHBoxLayout(); cond_row.setSpacing(12)

        self.rabatt_spin = QDoubleSpinBox()
        self.rabatt_spin.setRange(0, 100)
        self.rabatt_spin.setSuffix(" %")
        self.rabatt_spin.setDecimals(1)
        self.rabatt_spin.valueChanged.connect(self._update_summe)

        self.versand_spin = QDoubleSpinBox()
        self.versand_spin.setRange(0, 999.99)
        self.versand_spin.setPrefix("€ ")
        self.versand_spin.setDecimals(2)
        self.versand_spin.valueChanged.connect(self._update_summe)

        for lbl_t, widget in [("Gesamtrabatt (%)", self.rabatt_spin),
                                ("Versandkosten", self.versand_spin)]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(lbl(lbl_t)); col.addWidget(widget)
            cond_row.addLayout(col)
        cond_row.addStretch()
        content_layout.addLayout(cond_row)

        # ── Summe
        summe_frame = QFrame()
        summe_frame.setStyleSheet(f"""
            background: {COLOR_PRIMARY}18;
            border: 1px solid {COLOR_PRIMARY}30;
            border-radius: 10px;
            padding: 14px;
        """)
        summe_layout = QHBoxLayout(summe_frame)
        summe_layout.addStretch()
        self.gesamt_netto_lbl = QLabel("Netto: € 0,00")
        self.gesamt_netto_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        self.gesamt_mwst_lbl  = QLabel("MwSt.: € 0,00")
        self.gesamt_mwst_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        self.gesamt_brutto_lbl = QLabel("Gesamt Brutto: € 0,00")
        self.gesamt_brutto_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.gesamt_brutto_lbl.setStyleSheet(f"color: {COLOR_PRIMARY};")

        summe_layout.addWidget(self.gesamt_netto_lbl)
        summe_layout.addSpacing(20)
        summe_layout.addWidget(self.gesamt_mwst_lbl)
        summe_layout.addSpacing(20)
        summe_layout.addWidget(self.gesamt_brutto_lbl)
        content_layout.addWidget(summe_frame)

        # ── Notizen
        self.notizen_edit = QTextEdit()
        self.notizen_edit.setPlaceholderText("Anmerkungen zur Bestellung...")
        self.notizen_edit.setMaximumHeight(70)
        col_n = QVBoxLayout(); col_n.setSpacing(4)
        col_n.addWidget(lbl("Notizen")); col_n.addWidget(self.notizen_edit)
        content_layout.addLayout(col_n)
        content_layout.addStretch()

        layout.addWidget(scroll)

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

        speichern_btn = QPushButton("💾  Bestellung speichern")
        speichern_btn.setObjectName("btn_primary")
        speichern_btn.setFixedHeight(38)
        speichern_btn.clicked.connect(self._speichern)

        btn_layout.addWidget(abbruch_btn)
        btn_layout.addWidget(speichern_btn)
        layout.addWidget(btn_frame)

    def _update_lieferadresse(self):
        kid = self.kunde_combo.currentData()
        for k in self.kunden:
            if k["id"] == kid:
                teile = [k.get("strasse",""), k.get("plz",""), k.get("ort","")]
                addr = ", ".join(t for t in teile if t)
                self.liefer_edit.setText(addr)
                break

    def _update_summe(self):
        netto = self.positionen_widget.get_netto()
        rabatt = self.rabatt_spin.value() / 100
        versand = self.versand_spin.value()
        netto_nach_rabatt = netto * (1 - rabatt) + versand

        # Approximierte MwSt (19%)
        mwst = netto_nach_rabatt * 0.19
        brutto = netto_nach_rabatt * 1.19

        self.gesamt_netto_lbl.setText(f"Netto: € {netto_nach_rabatt:,.2f}")
        self.gesamt_mwst_lbl.setText(f"MwSt. (19%): € {mwst:,.2f}")
        self.gesamt_brutto_lbl.setText(f"Gesamt Brutto: € {brutto:,.2f}")

    def _fill_data(self):
        b = self.bestellung
        idx = self.kunde_combo.findData(b.get("kunden_id"))
        if idx >= 0:
            self.kunde_combo.setCurrentIndex(idx)
        self.liefer_edit.setText(b.get("lieferadresse","") or "")
        self.status_combo.setCurrentText(b.get("status","Neu"))
        self.zahlung_combo.setCurrentText(b.get("zahlungsart","Rechnung"))
        self.zahlstatus_combo.setCurrentText(b.get("zahlungsstatus","Offen"))
        d = b.get("lieferdatum","")
        if d:
            qd = QDate.fromString(str(d)[:10], "yyyy-MM-dd")
            if qd.isValid():
                self.liefer_datum.setDate(qd)
        self.rabatt_spin.setValue(float(b.get("rabatt_prozent",0) or 0))
        self.versand_spin.setValue(float(b.get("versandkosten",0) or 0))
        self.notizen_edit.setPlainText(b.get("notizen","") or "")
        # Positionen laden
        positionen = db.get_bestellpositionen(b["id"])
        self.positionen_widget.set_positionen(positionen)
        self._update_summe()

    def _speichern(self):
        kid = self.kunde_combo.currentData()
        if not kid:
            QMessageBox.warning(self, "Pflichtfeld", "Bitte einen Kunden auswählen.")
            return
        positionen = self.positionen_widget.get_positionen()
        if not positionen:
            QMessageBox.warning(self, "Keine Positionen",
                "Bitte mindestens einen Artikel zur Bestellung hinzufügen.")
            return
        self.result_data = {
            "id":             self.bestellung.get("id"),
            "kunden_id":      kid,
            "lieferadresse":  self.liefer_edit.text().strip(),
            "status":         self.status_combo.currentText(),
            "zahlungsart":    self.zahlung_combo.currentText(),
            "zahlungsstatus": self.zahlstatus_combo.currentText(),
            "lieferdatum":    self.liefer_datum.date().toString("yyyy-MM-dd"),
            "rabatt_prozent": self.rabatt_spin.value(),
            "versandkosten":  self.versand_spin.value(),
            "notizen":        self.notizen_edit.toPlainText().strip(),
        }
        self.result_positionen = positionen
        self.accept()


class BestellungDetailDialog(QDialog):
    """Nur-Lesen-Ansicht einer Bestellung mit Status-Update."""
    status_geaendert = pyqtSignal()

    def __init__(self, parent, bestell_id: int):
        super().__init__(parent)
        self.bestell_id = bestell_id
        self.setWindowTitle("Bestelldetails")
        self.setMinimumWidth(640)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        b = db.get_bestellung(self.bestell_id)
        pos = db.get_bestellpositionen(self.bestell_id)
        if not b:
            return

        self.setStyleSheet(f"background: {COLOR_WHITE};")
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        status_farbe = STATUS_FARBEN.get(b["status"], "#666")
        header = QFrame()
        header.setStyleSheet(f"background: {COLOR_PRIMARY};")
        header.setFixedHeight(70)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)
        title = QLabel(f"📦  Bestellung {b['bestellnummer']}")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_WHITE};")
        status_badge = QLabel(b["status"])
        status_badge.setStyleSheet(f"""
            background: {status_farbe}; color: white;
            border-radius: 10px; padding: 4px 14px;
            font-size: 12px; font-weight: 600;
        """)
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(status_badge)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(24, 20, 24, 20)
        c_layout.setSpacing(14)

        # Info-Karten
        info_row = QHBoxLayout()
        info_row.setSpacing(12)

        def info_card(titel, wert, farbe="#fff"):
            f = QFrame()
            f.setStyleSheet(f"""
                background: {farbe};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 10px 14px;
            """)
            fl = QVBoxLayout(f)
            fl.setSpacing(2)
            t = QLabel(titel)
            t.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_LIGHT}; font-weight: 600;")
            v = QLabel(str(wert))
            v.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            v.setStyleSheet(f"color: {COLOR_PRIMARY};")
            fl.addWidget(t); fl.addWidget(v)
            return f

        z_farbe = ZAHLUNG_FARBEN.get(b["zahlungsstatus"], "#666")
        info_row.addWidget(info_card("Kunde", b["kunde_name"]))
        info_row.addWidget(info_card("Datum", str(b["bestelldatum"])[:10]))
        info_row.addWidget(info_card("Zahlungsart", b["zahlungsart"]))
        info_row.addWidget(info_card("Gesamtbetrag", f"€ {b.get('gesamtbetrag_brutto', 0):.2f}"))
        c_layout.addLayout(info_row)

        # Positionen
        pos_title = QLabel("Bestellpositionen")
        pos_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        pos_title.setStyleSheet(f"color: {COLOR_PRIMARY};")
        c_layout.addWidget(pos_title)

        pos_table = QTableWidget(len(pos), 5)
        pos_table.setHorizontalHeaderLabels(["Art.-Nr.", "Bezeichnung", "Menge", "Einzelpreis", "Gesamt Netto"])
        pos_table.verticalHeader().setVisible(False)
        pos_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        pos_table.setShowGrid(False)
        pos_table.setAlternatingRowColors(True)
        pos_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for row, p in enumerate(pos):
            pos_table.setItem(row, 0, QTableWidgetItem(p.get("artikelnummer","")))
            pos_table.setItem(row, 1, QTableWidgetItem(p.get("bezeichnung","")))
            pos_table.setItem(row, 2, QTableWidgetItem(f"{p['menge']} {p.get('einheit','')}"))
            pos_table.setItem(row, 3, QTableWidgetItem(f"€ {p['einzelpreis']:.2f}"))
            pos_table.setItem(row, 4, QTableWidgetItem(f"€ {p['menge']*p['einzelpreis']:.2f}"))
        pos_table.setMaximumHeight(len(pos) * 46 + 40)
        c_layout.addWidget(pos_table)

        # Status schnell ändern
        sq_frame = QFrame()
        sq_frame.setStyleSheet(f"background: #f8f9fa; border-radius: 8px;")
        sq_layout = QHBoxLayout(sq_frame)
        sq_layout.setContentsMargins(16, 10, 16, 10)
        sq_layout.addWidget(QLabel("Status ändern:"))
        self.new_status_combo = QComboBox()
        self.new_status_combo.addItems(["Neu","In Bearbeitung","Versendet","Geliefert","Storniert","Zurückgegeben"])
        self.new_status_combo.setCurrentText(b["status"])
        sq_layout.addWidget(self.new_status_combo)
        sq_layout.addWidget(QLabel("Zahlung:"))
        self.new_zahl_combo = QComboBox()
        self.new_zahl_combo.addItems(["Offen","Teilbezahlt","Bezahlt","Erstattet"])
        self.new_zahl_combo.setCurrentText(b["zahlungsstatus"])
        sq_layout.addWidget(self.new_zahl_combo)
        upd_btn = QPushButton("✓ Aktualisieren")
        upd_btn.setObjectName("btn_secondary")
        upd_btn.setFixedHeight(34)
        upd_btn.clicked.connect(self._update_status)
        sq_layout.addWidget(upd_btn)
        sq_layout.addStretch()
        c_layout.addWidget(sq_frame)

        if b.get("notizen"):
            notiz_lbl = QLabel(f"📝 {b['notizen']}")
            notiz_lbl.setWordWrap(True)
            notiz_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px; font-style: italic;")
            c_layout.addWidget(notiz_lbl)

        c_layout.addStretch()
        layout.addWidget(scroll)

        # Schließen
        btn_frame = QFrame()
        btn_frame.setStyleSheet(f"background: #f8f9fa; border-top: 1px solid {COLOR_BORDER};")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(24, 12, 24, 12)
        btn_layout.addStretch()
        close_btn = QPushButton("Schließen")
        close_btn.setObjectName("btn_icon")
        close_btn.setFixedHeight(38)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addWidget(btn_frame)

    def _update_status(self):
        db.update_bestellstatus(
            self.bestell_id,
            self.new_status_combo.currentText(),
            self.new_zahl_combo.currentText()
        )
        self.status_geaendert.emit()
        QMessageBox.information(self, "Aktualisiert", "Status wurde erfolgreich aktualisiert.")


class BestellungenWidget(QWidget):
    bestellungen_geaendert = pyqtSignal()

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
        self.search_edit.setPlaceholderText("Bestellungen suchen (Nummer, Kunde...)")
        self.search_edit.setFrame(False)
        self.search_edit.setStyleSheet("background: transparent; border: none; font-size: 13px;")
        self.search_edit.textChanged.connect(self.refresh)
        search_layout.addWidget(self.search_edit)
        toolbar.addWidget(search_frame, stretch=1)

        self.status_filter = QComboBox()
        self.status_filter.setFixedHeight(40)
        self.status_filter.addItem("Alle Status", "")
        for s in ["Neu","In Bearbeitung","Versendet","Geliefert","Storniert","Zurückgegeben"]:
            self.status_filter.addItem(s, s)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.status_filter)

        neu_btn = QPushButton("➕  Neue Bestellung")
        neu_btn.setObjectName("btn_primary")
        neu_btn.setFixedHeight(40)
        neu_btn.clicked.connect(self._neue_bestellung)
        toolbar.addWidget(neu_btn)

        layout.addLayout(toolbar)

        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        layout.addWidget(self.info_lbl)

        # Tabelle
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Best.-Nr.", "Datum", "Kunde", "Positionen",
            "Netto", "Brutto", "Status", "Zahlung", "Zahlstatus", "Aktionen"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(9, 200)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.doubleClicked.connect(self._detail_zeile)
        layout.addWidget(self.table)

    def refresh(self):
        suche = self.search_edit.text().strip()
        status = self.status_filter.currentData()
        bestellungen = db.get_alle_bestellungen(suche, status)

        gesamt = sum(b.get("gesamtbetrag_brutto") or 0 for b in bestellungen)
        self.info_lbl.setText(
            f"{len(bestellungen)} Bestellung(en) · Gesamtumsatz: € {gesamt:,.2f}"
        )

        self.table.setRowCount(len(bestellungen))
        for row, b in enumerate(bestellungen):
            items = [
                b.get("bestellnummer",""),
                str(b.get("bestelldatum",""))[:10],
                b.get("kunde_name",""),
                str(b.get("anzahl_positionen",0)),
                f"€ {b.get('gesamtbetrag_netto', 0):.2f}",
                f"€ {b.get('gesamtbetrag_brutto', 0):.2f}",
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text or "")
                item.setData(Qt.ItemDataRole.UserRole, b["id"])
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, col, item)

            # Status Badge
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
            self.table.setCellWidget(row, 6, status_lbl)

            # Zahlungsart
            za_lbl = QLabel(b.get("zahlungsart",""))
            za_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            za_lbl.setStyleSheet("font-size: 12px; color: " + COLOR_TEXT_LIGHT + "; margin: 6px 4px;")
            self.table.setCellWidget(row, 7, za_lbl)

            # Zahlstatus Badge
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

            # Aktionen
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            detail_btn = QPushButton("🔍 Details")
            detail_btn.setObjectName("btn_icon")
            detail_btn.setFixedHeight(30)
            detail_btn.setProperty("bid", b["id"])
            detail_btn.clicked.connect(self._zeige_detail)

            edit_btn = QPushButton("✏️")
            edit_btn.setObjectName("btn_icon")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setProperty("bid", b["id"])
            edit_btn.clicked.connect(self._bearbeite_bestellung)

            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("btn_danger")
            del_btn.setFixedSize(30, 30)
            del_btn.setProperty("bid", b["id"])
            del_btn.clicked.connect(self._loesche_bestellung)

            btn_layout.addWidget(detail_btn)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 9, btn_widget)

    def _neue_bestellung(self):
        dlg = BestellungDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            db.speichere_bestellung(dlg.result_data, dlg.result_positionen)
            self.refresh()
            self.bestellungen_geaendert.emit()

    def _detail_zeile(self, index):
        item = self.table.item(index.row(), 0)
        if item:
            bid = item.data(Qt.ItemDataRole.UserRole)
            dlg = BestellungDetailDialog(self, bid)
            dlg.status_geaendert.connect(self.refresh)
            dlg.exec()

    def _zeige_detail(self):
        bid = self.sender().property("bid")
        dlg = BestellungDetailDialog(self, bid)
        dlg.status_geaendert.connect(self.refresh)
        dlg.status_geaendert.connect(self.bestellungen_geaendert)
        dlg.exec()

    def _bearbeite_bestellung(self):
        bid = self.sender().property("bid")
        b = db.get_bestellung(bid)
        if b:
            dlg = BestellungDialog(self, b)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                db.speichere_bestellung(dlg.result_data, dlg.result_positionen)
                self.refresh()
                self.bestellungen_geaendert.emit()

    def _loesche_bestellung(self):
        bid = self.sender().property("bid")
        b = db.get_bestellung(bid)
        if not b:
            return
        reply = QMessageBox.question(
            self, "Bestellung löschen",
            f"Bestellung <b>{b['bestellnummer']}</b> von <b>{b['kunde_name']}</b> löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.loesche_bestellung(bid)
            self.refresh()
            self.bestellungen_geaendert.emit()
