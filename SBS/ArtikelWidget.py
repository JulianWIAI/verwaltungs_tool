"""
ArtikelWidget – Shopping-style article display (the "Articles" tab).

Part of the Radsport Koch GmbH management system.

Responsibilities:
  - Display articles as product cards in a responsive grid (like a shop).
  - Search bar and category filter at the top.
  - Allow creating, editing and deleting articles via toolbar / card buttons.
  - Export the currently visible list to a CSV file.
  - Emit the artikel_geaendert signal after any data change.
"""

import csv
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QDialog, QComboBox, QMessageBox,
    QFileDialog, QScrollArea, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import database as db
from styles import (
    COLOR_TEXT_LIGHT, COLOR_BORDER, COLOR_DANGER, COLOR_WARNING,
    COLOR_SUCCESS, COLOR_PRIMARY, COLOR_SECONDARY, COLOR_BG, COLOR_TEXT
)
from SBS.ArtikelDialog import ArtikelDialog


class ArtikelWidget(QWidget):
    """
    Shopping-style widget for the "Articles" tab.

    Articles are displayed as product cards in a grid – similar to an online shop.
    The toolbar at the top provides search, category filter, and management actions.

    Signals:
        artikel_geaendert: Emitted after an article is created, edited or deleted.
    """

    artikel_geaendert = pyqtSignal()

    # Number of card columns in the grid.
    _COLS = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    # ──────────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        """Build toolbar + info row + scrollable card grid."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Search bar (pill style).
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
        self.search_edit.setPlaceholderText("Artikel suchen (Bezeichnung, Hersteller, Kategorie…)")
        self.search_edit.setFrame(False)
        self.search_edit.setStyleSheet("background: transparent; border: none; font-size: 13px;")
        self.search_edit.textChanged.connect(self.refresh)
        search_layout.addWidget(self.search_edit)
        toolbar.addWidget(search_frame, stretch=1)

        # Category filter dropdown.
        self.filter_combo = QComboBox()
        self.filter_combo.setFixedHeight(40)
        self.filter_combo.addItem("Alle Kategorien", "")
        for k in db.get_kategorien():
            self.filter_combo.addItem(k["name"], k["id"])
        self.filter_combo.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.filter_combo)

        # "New article" button.
        neu_btn = QPushButton("➕  Neuer Artikel")
        neu_btn.setObjectName("btn_primary")
        neu_btn.setFixedHeight(40)
        neu_btn.clicked.connect(self._neuer_artikel)
        toolbar.addWidget(neu_btn)

        # "Export CSV" button.
        csv_btn = QPushButton("📥  CSV exportieren")
        csv_btn.setObjectName("btn_icon")
        csv_btn.setFixedHeight(40)
        csv_btn.clicked.connect(self._exportiere_csv)
        toolbar.addWidget(csv_btn)

        layout.addLayout(toolbar)

        # ── Info row ─────────────────────────────────────────────────────────
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        layout.addWidget(self.info_lbl)

        # ── Scrollable card grid ──────────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet(f"background: {COLOR_BG};")

        # Container widget that holds the grid layout.
        self.cards_container = QWidget()
        self.cards_container.setStyleSheet(f"background: {COLOR_BG};")

        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(18)
        self.cards_layout.setContentsMargins(4, 4, 4, 4)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.scroll.setWidget(self.cards_container)
        layout.addWidget(self.scroll)

    # ──────────────────────────────────────────────────────────────────────────
    # Data loading & display
    # ──────────────────────────────────────────────────────────────────────────

    def refresh(self):
        """Reload articles from the database and rebuild the card grid."""
        suche = self.search_edit.text().strip()
        artikel = db.get_alle_artikel(suche)

        # Client-side category filter.
        kat_filter = self.filter_combo.currentData()
        if kat_filter:
            kat_name = self.filter_combo.currentText()
            artikel = [a for a in artikel if a.get("kategorie") == kat_name]

        nachbestellen = sum(1 for a in artikel if a.get("nachbestellen"))
        info = f"{len(artikel)} Artikel gefunden"
        if nachbestellen:
            info += f"  ·  ⚠️ {nachbestellen} unter Mindestbestand"
        self.info_lbl.setText(info)

        # Remove all existing cards.
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Insert new cards.
        for i, a in enumerate(artikel):
            card = self._build_card(a)
            row, col = divmod(i, self._COLS)
            self.cards_layout.addWidget(card, row, col)

        # Fill remaining columns in last row with spacers so cards don't stretch.
        count = len(artikel)
        if count % self._COLS:
            used = count % self._COLS
            for col in range(used, self._COLS):
                spacer = QWidget()
                spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                self.cards_layout.addWidget(spacer, count // self._COLS, col)

    @staticmethod
    def _get_emoji(a: dict) -> str:
        """Return a category/name-appropriate emoji for the article."""
        name = (a.get("bezeichnung") or "").lower()
        kat  = (a.get("kategorie")  or "").lower()

        # Name-based (highest priority)
        if "helm"        in name:                         return "⛑️"
        if "schloss"     in name or "lock" in name:       return "🔒"
        if "pumpe"       in name:                         return "🫧"
        if "computer"    in name or "garmin" in name or "gps" in name: return "🗺️"
        if "hose"        in name or "trikot" in name or "jacke" in name: return "👕"
        if "brems"       in name:                         return "🛑"
        if "kette"       in name:                         return "⛓️"
        if "reifen"      in name or "schlauch" in name:  return "🔄"
        if "licht"       in name or "lampe" in name:     return "💡"
        if "sattel"      in name:                         return "🪑"
        if "pedal"       in name:                         return "🦶"
        if "werkzeug"    in name or "schrauben" in name: return "🔧"
        if "tasche"      in name or "rucksack" in name:  return "🎒"
        if "flasche"     in name:                         return "🍶"
        if "schuhe"      in name or "schuh" in name:     return "👟"
        if "handschuh"   in name:                         return "🧤"

        # Category-based (fallback)
        if "helm"        in kat:  return "⛑️"
        if "e-bike"      in kat:  return "⚡"
        if "bekleidung"  in kat:  return "👕"
        if "werkzeug"    in kat:  return "🔧"
        if "ersatzteil"  in kat:  return "⚙️"
        if "zubehör"     in kat:  return "🔩"
        if "fahrrad"     in kat:  return "🚲"

        return "🚲"

    def _build_card(self, a: dict) -> QFrame:
        """
        Create a single product card for the given article dict.

        The card layout (top → bottom):
          1. Image placeholder area
          2. Article number (small, muted)
          3. Product name (bold)
          4. Category / Manufacturer (muted)
          5. Gross price (large, coloured)
          6. Status badge
          7. Action buttons (Edit / Delete)
        """
        card = QFrame()
        card.setFixedWidth(230)
        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border: 1.5px solid {COLOR_PRIMARY};
            }}
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 12)
        card_layout.setSpacing(6)

        # ── 1. Image placeholder ──────────────────────────────────────────────
        img_frame = QFrame()
        img_frame.setFixedHeight(140)
        img_frame.setStyleSheet(f"""
            background: {COLOR_BG};
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
        """)
        img_layout = QVBoxLayout(img_frame)
        img_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bike_lbl = QLabel(self._get_emoji(a))
        bike_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bike_lbl.setStyleSheet("font-size: 52px; border: none; background: transparent;")
        img_layout.addWidget(bike_lbl)

        card_layout.addWidget(img_frame)

        # ── Inner padding container ───────────────────────────────────────────
        inner = QWidget()
        inner.setStyleSheet("background: transparent; border: none;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(12, 6, 12, 0)
        inner_layout.setSpacing(4)

        # ── 2. Article number ─────────────────────────────────────────────────
        art_nr = QLabel(a.get("artikelnummer", ""))
        art_nr.setStyleSheet(f"font-size: 10px; color: {COLOR_TEXT_LIGHT}; font-weight: 500; border: none;")
        inner_layout.addWidget(art_nr)

        # ── 3. Product name ───────────────────────────────────────────────────
        name = QLabel(a.get("bezeichnung", ""))
        name.setWordWrap(True)
        name.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {COLOR_TEXT}; border: none;")
        name.setMaximumWidth(206)
        inner_layout.addWidget(name)

        # ── 4. Category & Manufacturer ────────────────────────────────────────
        cat_mfr_parts = []
        if a.get("kategorie"):
            cat_mfr_parts.append(a["kategorie"])
        if a.get("hersteller"):
            cat_mfr_parts.append(a["hersteller"])
        meta_lbl = QLabel("  ·  ".join(cat_mfr_parts) if cat_mfr_parts else "")
        meta_lbl.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_LIGHT}; border: none;")
        meta_lbl.setWordWrap(True)
        inner_layout.addWidget(meta_lbl)

        inner_layout.addSpacing(4)

        # ── 5. Gross price ────────────────────────────────────────────────────
        vk_brutto = a.get("verkaufspreis", 0) * (1 + a.get("mwst_satz", 19) / 100)
        price_lbl = QLabel(f"€ {vk_brutto:.2f}")
        price_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLOR_SECONDARY}; border: none;")
        inner_layout.addWidget(price_lbl)

        # ── 6. Status badge ───────────────────────────────────────────────────
        if not a.get("aktiv", 1):
            badge_text, badge_style = "Inaktiv", (
                "background:#f0f2f5; color:#6c757d; border-radius:8px; "
                "padding:2px 8px; font-size:10px; font-weight:600;"
            )
        elif a.get("nachbestellen"):
            badge_text = "⚠ Nachbestellen"
            badge_style = (
                f"background:{COLOR_WARNING}22; color:{COLOR_WARNING}; "
                "border-radius:8px; padding:2px 8px; font-size:10px; font-weight:600;"
            )
        else:
            badge_text = "✓ Verfügbar"
            badge_style = (
                f"background:{COLOR_SUCCESS}22; color:{COLOR_SUCCESS}; "
                "border-radius:8px; padding:2px 8px; font-size:10px; font-weight:600;"
            )

        badge = QLabel(badge_text)
        badge.setStyleSheet(badge_style)
        badge.setFixedHeight(22)
        inner_layout.addWidget(badge)

        inner_layout.addSpacing(4)

        # ── 7. Action buttons ─────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        edit_btn = QPushButton("✏️ Bearbeiten")
        edit_btn.setObjectName("btn_icon")
        edit_btn.setFixedHeight(30)
        edit_btn.setProperty("art_id", a["id"])
        edit_btn.clicked.connect(self._bearbeite_artikel)
        btn_row.addWidget(edit_btn)

        del_btn = QPushButton("🗑️")
        del_btn.setObjectName("btn_danger")
        del_btn.setFixedSize(30, 30)
        del_btn.setProperty("art_id", a["id"])
        del_btn.clicked.connect(self._loesche_artikel)
        btn_row.addWidget(del_btn)

        inner_layout.addLayout(btn_row)

        card_layout.addWidget(inner)

        return card

    # ──────────────────────────────────────────────────────────────────────────
    # Slots – article management
    # ──────────────────────────────────────────────────────────────────────────

    def _neuer_artikel(self):
        dlg = ArtikelDialog(self)
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

    # ──────────────────────────────────────────────────────────────────────────
    # CSV export
    # ──────────────────────────────────────────────────────────────────────────

    def _exportiere_csv(self):
        pfad, _ = QFileDialog.getSaveFileName(
            self, "Artikel exportieren", "artikel_export.csv", "CSV-Dateien (*.csv)"
        )
        if not pfad:
            return

        suche = self.search_edit.text().strip()
        artikel = db.get_alle_artikel(suche)

        kat_filter = self.filter_combo.currentData()
        if kat_filter:
            kat_name = self.filter_combo.currentText()
            artikel = [a for a in artikel if a.get("kategorie") == kat_name]

        try:
            with open(pfad, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow([
                    "Artikelnummer", "Bezeichnung", "Kategorie", "Hersteller",
                    "Lieferant", "EK (€)", "VK Netto (€)", "VK Brutto (€)",
                    "MwSt. (%)", "Lagerbestand", "Mindestbestand", "Einheit", "Status"
                ])
                for a in artikel:
                    vk_brutto = a.get("verkaufspreis", 0) * (1 + a.get("mwst_satz", 19) / 100)
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
                        f"{a.get('einkaufspreis', 0):.2f}",
                        f"{a.get('verkaufspreis', 0):.2f}",
                        f"{vk_brutto:.2f}",
                        a.get("mwst_satz", 19),
                        a.get("lagerbestand", 0),
                        a.get("mindestbestand", 0),
                        a.get("einheit", ""),
                        status,
                    ])
            QMessageBox.information(
                self, "Export erfolgreich",
                f"{len(artikel)} Artikel wurden exportiert nach:\n{pfad}"
            )
        except Exception as fehler:
            QMessageBox.warning(self, "Fehler beim Export", str(fehler))