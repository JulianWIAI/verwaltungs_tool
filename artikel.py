"""
Radsport Koch GmbH – Artikelverwaltung

Dieses Modul stellt die grafische Benutzeroberfläche (GUI) für die
Artikelverwaltung des Fahrradgeschäfts bereit. Es enthält zwei Klassen:

  - ArtikelDialog: Ein modales Dialogfenster zum Anlegen und Bearbeiten
    eines einzelnen Artikels (z.B. Fahrrad, Ersatzteil, Zubehör).
  - ArtikelWidget: Das Haupt-Widget der Registerkarte "Artikel", das eine
    durchsuchbare und nach Kategorien filterbare Tabelle aller Artikel
    anzeigt. Für jeden Artikel werden Preis, Lagerbestand und Status
    (Verfügbar / Nachbestellen / Inaktiv) angezeigt.

Beide Klassen verwenden das Modul `database` (db) für alle
Datenbankoperationen und das Modul `styles` für einheitliche Farben.
"""

# --- Importe aus PyQt6 ---
# QWidget          – Basisklasse für alle GUI-Elemente
# QVBoxLayout      – Ordnet Widgets senkrecht (vertikal) an
# QHBoxLayout      – Ordnet Widgets waagerecht (horizontal) an
# QLabel           – Zeigt Text (nicht editierbar)
# QPushButton      – Klickbare Schaltfläche
# QTableWidget     – Tabelle mit Zeilen und Spalten
# QTableWidgetItem – Einzelne Zelle in einer Tabelle
# QHeaderView      – Verhaltenssteuerung der Spaltenköpfe
# QFrame           – Container mit optionalem Rahmen
# QLineEdit        – Einzeiliges Texteingabefeld
# QDialog          – Basisklasse für modale Dialogfenster
# QTextEdit        – Mehrzeiliges Texteingabefeld
# QComboBox        – Dropdown-Auswahlmenü
# QSpinBox         – Ganzzahlen-Eingabefeld mit Hoch-/Runter-Pfeil
# QDoubleSpinBox   – Dezimalzahlen-Eingabefeld (für Preise)
# QMessageBox      – Vorgefertigte Meldungsfenster
# QCheckBox        – Ankreuzfeld (True/False)
# QAbstractItemView– Basisklasse mit Konstanten für Ansichten
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QDialog, QTextEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QMessageBox, QCheckBox, QAbstractItemView
)

# Qt        – Globale Konstanten (z.B. Ausrichtungsflags)
# pyqtSignal– Erstellt anwendungseigene Signale
from PyQt6.QtCore import Qt, pyqtSignal

# QFont  – Schriftart und -größe
# QColor – Farbe als RGB oder Farbname
from PyQt6.QtGui import QFont, QColor

# Eigenes Datenbankmodul für alle SQLite-Operationen
import database as db

# Zentrale Farbkonstanten für ein einheitliches Design der Anwendung
from styles import (
    COLOR_PRIMARY,      # Hauptfarbe (Primär-Buttons, Header)
    COLOR_SECONDARY,    # Sekundärfarbe
    COLOR_DANGER,       # Rot für Fehler und Löschen-Aktionen
    COLOR_WHITE,        # Weißer Hintergrund
    COLOR_TEXT_LIGHT,   # Helles Grau für Beschriftungen
    COLOR_BORDER,       # Rahmenfarbe
    COLOR_WARNING,      # Gelb/Orange für Warnungen (z.B. Nachbestellbedarf)
    COLOR_SUCCESS       # Grün für positive Status-Anzeigen
)


# =============================================================================
# Klasse ArtikelDialog
# =============================================================================

class ArtikelDialog(QDialog):
    """
    Modales Dialogfenster zum Anlegen eines neuen Artikels oder zum
    Bearbeiten eines bestehenden Artikels.

    "Modal" bedeutet: Das Dialogfenster blockiert alle anderen Fenster
    der Anwendung, bis der Nutzer speichert oder abbricht.

    Parameter:
        parent  (QWidget, optional): Das übergeordnete Eltern-Widget.
        artikel (dict, optional):    Wörterbuch mit den vorhandenen
                                     Artikeldaten. None = neuer Artikel.

    Attribute:
        artikel     (dict): Die übergeben Artikeldaten (oder {}).
        kategorien  (list): Liste aller Kategorien aus der Datenbank.
        result_data (dict): Nach dem Speichern: alle Formulardaten als Dict.
    """

    def __init__(self, parent=None, artikel: dict = None):
        """
        Konstruktor des Dialogs.

        Ruft den Konstruktor der Elternklasse QDialog auf, speichert
        die Artikeldaten, setzt den Fenstertitel und baut die
        Benutzeroberfläche auf.

        Args:
            parent  (QWidget, optional): Übergeordnetes Widget.
            artikel (dict, optional):    Bestehende Artikeldaten oder None.
        """
        # Elternklasse initialisieren – bei jeder Qt-Klasse Pflicht
        super().__init__(parent)

        # Artikeldaten speichern; "artikel or {}" ergibt {}, falls None übergeben wurde
        self.artikel = artikel or {}

        # Fenstertitel hängt davon ab, ob ein Artikel bearbeitet oder neu angelegt wird
        self.setWindowTitle("Artikel bearbeiten" if artikel else "Neuen Artikel anlegen")

        # Mindestbreite des Fensters in Pixeln
        self.setMinimumWidth(580)

        # Dialog blockiert das übergeordnete Fenster
        self.setModal(True)

        # Alle Widgets und das Layout aufbauen
        self._setup_ui()

        # Wenn ein bestehender Artikel übergeben wurde, Felder mit seinen Daten füllen
        if artikel:
            self._fill_data()

    def _setup_ui(self):
        """
        Erstellt und konfiguriert alle Widgets des Artikeldialogs.

        Der Dialog ist in drei Bereiche aufgeteilt:
          1. Header   – farbiger Titelbalken oben mit Fahrrad-Icon
          2. Formular – Eingabefelder (Bezeichnung, Kategorie, Preise,
                        Lager, Beschreibung, Aktiv-Checkbox)
          3. Buttons  – "Abbrechen" und "Speichern" am unteren Rand
        """
        # Hintergrund des gesamten Dialogs auf Weiß setzen
        self.setStyleSheet(f"QDialog {{ background: {COLOR_WHITE}; }}")

        # Haupt-Layout: alle drei Bereiche senkrecht anordnen
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Bereich 1: Header ---
        header = QFrame()
        header.setStyleSheet(f"background: {COLOR_PRIMARY};")
        header.setFixedHeight(64)

        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        # Titeltext mit Fahrrad-Emoji; Inhalt je nach Modus
        title_lbl = QLabel("🚲  " + ("Artikel bearbeiten" if self.artikel else "Neuen Artikel anlegen"))
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLOR_WHITE};")
        h_layout.addWidget(title_lbl)
        layout.addWidget(header)

        # --- Bereich 2: Formular ---
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(24, 20, 24, 20)
        form_layout.setSpacing(12)

        # --- Hilfsfunktion: Beschriftungs-Label erstellen ---
        def lbl(text):
            """
            Erstellt ein kleines, fettes Beschriftungs-Label in der
            Farbe COLOR_TEXT_LIGHT. Wird über jedem Eingabefeld verwendet.

            Args:
                text (str): Beschriftungstext (z.B. "Bezeichnung *").

            Returns:
                QLabel: Das fertige Beschriftungs-Label.
            """
            l = QLabel(text)
            l.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {COLOR_TEXT_LIGHT};")
            return l

        # --- Hilfsfunktion: Horizontale Zeile aus mehreren Widgets ---
        def row(*widgets):
            """
            Erstellt ein horizontales Layout aus einer beliebigen Anzahl
            von Widgets. Ganzzahlen werden als fester Leerabstand
            eingefügt (addSpacing), alles andere als Widget.

            Args:
                *widgets: Beliebig viele QWidget-Objekte oder int-Abstände.

            Returns:
                QHBoxLayout: Das fertige horizontale Layout.
            """
            r = QHBoxLayout()
            r.setSpacing(12)
            for w in widgets:
                # Prüfen ob w eine Ganzzahl ist (Abstand) oder ein Widget
                r.addWidget(w) if not isinstance(w, int) else r.addSpacing(w)
            return r

        # --- Formularzeile 1: Bezeichnung + Kategorie ---
        # Bezeichnungsfeld (Pflichtfeld, nimmt 2/3 der Breite ein)
        self.bez_edit = QLineEdit()
        self.bez_edit.setPlaceholderText("Artikelbezeichnung *")

        # Kategorien-Dropdown: zuerst alle Kategorien aus der DB laden
        self.kat_combo = QComboBox()
        self.kategorien = db.get_kategorien()   # Liste von Dicts: [{id, name}, ...]
        self.kat_combo.addItem("-- Kategorie wählen --", None)   # Leerer Standardeintrag

        # Jede Kategorie mit ihrem Namen (angezeigt) und ID (als Datenwert) einfügen
        for k in self.kategorien:
            self.kat_combo.addItem(k["name"], k["id"])

        # Zwei Spalten nebeneinander: Bezeichnung nimmt Streckungsfaktor 2, Kategorie 1
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
        r1.addLayout(col1, 2)   # Streckungsfaktor 2 = doppelt so breit wie col2
        r1.addLayout(col2, 1)   # Streckungsfaktor 1
        form_layout.addLayout(r1)

        # --- Formularzeile 2: Hersteller + Lieferant ---
        self.hersteller_edit = QLineEdit()
        self.hersteller_edit.setPlaceholderText("z.B. Shimano, Trek, Cube")
        self.lieferant_edit = QLineEdit()
        self.lieferant_edit.setPlaceholderText("Lieferantenname")

        r2 = QHBoxLayout()
        r2.setSpacing(12)
        # Kurzschreibweise: col3/col4 inline erstellen und befüllen
        col3 = QVBoxLayout(); col3.setSpacing(4)
        col3.addWidget(lbl("Hersteller")); col3.addWidget(self.hersteller_edit)
        col4 = QVBoxLayout(); col4.setSpacing(4)
        col4.addWidget(lbl("Lieferant")); col4.addWidget(self.lieferant_edit)
        r2.addLayout(col3)
        r2.addLayout(col4)
        form_layout.addLayout(r2)

        # --- Formularzeile 3: Preise (EK, VK, MwSt.) ---
        # Einkaufspreis: QDoubleSpinBox erlaubt Dezimalzahlen (z.B. 12.50)
        self.ek_spin = QDoubleSpinBox()
        self.ek_spin.setRange(0, 99999.99)      # Wertebereich: 0 bis 99.999,99 €
        self.ek_spin.setDecimals(2)              # Immer 2 Nachkommastellen
        self.ek_spin.setPrefix("€ ")             # "€ " wird vor dem Wert angezeigt
        self.ek_spin.setSingleStep(0.50)         # Klick auf Pfeil ändert Wert um 0,50 €

        # Verkaufspreis (Netto, ohne Mehrwertsteuer)
        self.vk_spin = QDoubleSpinBox()
        self.vk_spin.setRange(0, 99999.99)
        self.vk_spin.setDecimals(2)
        self.vk_spin.setPrefix("€ ")
        self.vk_spin.setSingleStep(0.50)

        # Mehrwertsteuersatz als Dropdown (Deutschland: 19% Standard, 7% ermäßigt)
        self.mwst_combo = QComboBox()
        self.mwst_combo.addItems(["19.0", "7.0", "0.0"])
        self.mwst_combo.setFixedWidth(80)

        # Alle drei Felder in einer Zeile anordnen (mit einer Schleife)
        r3 = QHBoxLayout(); r3.setSpacing(12)
        for lbl_t, widget in [("Einkaufspreis", self.ek_spin),
                                ("Verkaufspreis *", self.vk_spin),
                                ("MwSt. %", self.mwst_combo)]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(lbl(lbl_t)); col.addWidget(widget)
            r3.addLayout(col)
        form_layout.addLayout(r3)

        # --- Formularzeile 4: Lagerdaten ---
        # Lagerbestand: QSpinBox für Ganzzahlen (keine Nachkommastellen)
        self.bestand_spin = QSpinBox()
        self.bestand_spin.setRange(0, 99999)   # 0 bis 99.999 Stück

        # Mindestbestand: fällt der Bestand darunter, wird "Nachbestellen" angezeigt
        self.mindest_spin = QSpinBox()
        self.mindest_spin.setRange(0, 9999)

        # Einheit: Dropdown für verschiedene Maßeinheiten
        self.einheit_combo = QComboBox()
        self.einheit_combo.addItems(["Stück", "Paar", "Satz", "Meter", "Liter", "kg"])

        # Wieder per Schleife in einer Zeile anordnen
        r4 = QHBoxLayout(); r4.setSpacing(12)
        for lbl_t, widget in [("Lagerbestand", self.bestand_spin),
                                ("Mindestbestand", self.mindest_spin),
                                ("Einheit", self.einheit_combo)]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(lbl(lbl_t)); col.addWidget(widget)
            r4.addLayout(col)
        form_layout.addLayout(r4)

        # --- Formularzeile 5: Artikelbeschreibung ---
        # QTextEdit erlaubt mehrzeiligen Text (im Gegensatz zu QLineEdit)
        self.beschr_edit = QTextEdit()
        self.beschr_edit.setPlaceholderText("Artikelbeschreibung, technische Details...")
        self.beschr_edit.setMaximumHeight(80)  # Höhe begrenzen für kompaktes Layout
        col_d = QVBoxLayout(); col_d.setSpacing(4)
        col_d.addWidget(lbl("Beschreibung")); col_d.addWidget(self.beschr_edit)
        form_layout.addLayout(col_d)

        # --- Aktiv-Checkbox ---
        # Inaktive Artikel werden in der Liste angezeigt, aber nicht zum Verkauf angeboten
        self.aktiv_check = QCheckBox("Artikel ist aktiv / verkäuflich")
        self.aktiv_check.setChecked(True)   # Standardmäßig aktiviert (neuer Artikel)
        form_layout.addWidget(self.aktiv_check)

        # Fertig aufgebautes Formular zum Haupt-Layout hinzufügen
        layout.addWidget(form_widget)

        # --- Bereich 3: Schaltflächen ---
        btn_frame = QFrame()
        btn_frame.setObjectName("artikel_btn_frame")
        # Hellgrauer Hintergrund mit Trennlinie oben
        btn_frame.setStyleSheet(
            f"QFrame#artikel_btn_frame {{ background: #f8f9fa; border-top: 1px solid {COLOR_BORDER}; }}"
        )
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(24, 14, 24, 14)
        btn_layout.addStretch()   # Schiebt die Buttons nach rechts

        # "Abbrechen"-Button: schließt Dialog ohne Speichern
        abbruch_btn = QPushButton("Abbrechen")
        abbruch_btn.setObjectName("btn_icon")
        abbruch_btn.setFixedHeight(38)
        # reject() ist eine eingebaute QDialog-Methode (Ergebnis = "Rejected")
        abbruch_btn.clicked.connect(self.reject)

        # "Speichern"-Button: ruft die Validierung und Speicherlogik auf
        speichern_btn = QPushButton("💾  Speichern")
        speichern_btn.setObjectName("btn_primary")
        speichern_btn.setFixedHeight(38)
        speichern_btn.clicked.connect(self._speichern)

        btn_layout.addWidget(abbruch_btn)
        btn_layout.addWidget(speichern_btn)
        layout.addWidget(btn_frame)

    def _fill_data(self):
        """
        Füllt alle Eingabefelder mit den Daten des zu bearbeitenden Artikels.

        Wird nur aufgerufen, wenn beim Erstellen des Dialogs ein bestehendes
        Artikel-Wörterbuch übergeben wurde.

        Besondere Behandlung:
          - Kategorie: wird über ihre ID im Dropdown gefunden (findData)
          - MwSt.: wird über ihren Text-Wert gefunden (findText)
          - Einheit: wird über ihren Text-Wert gefunden (findText)
          - Aktiv: boolescher Wert (0/1 in der DB) wird in True/False umgewandelt
        """
        # Kurzreferenz auf self.artikel für kompakteren Code
        a = self.artikel

        # Bezeichnungsfeld befüllen
        self.bez_edit.setText(a.get("bezeichnung", ""))

        # Kategorie im Dropdown über die gespeicherte Daten-ID suchen
        # findData() sucht nicht nach dem angezeigten Text, sondern nach dem
        # Datenwert (der ID), der beim Befüllen des Dropdowns mit addItem() gesetzt wurde
        idx = self.kat_combo.findData(a.get("kategorie_id"))
        if idx >= 0:
            self.kat_combo.setCurrentIndex(idx)

        # Hersteller und Lieferant; "or ''" fängt None-Werte aus der Datenbank ab
        self.hersteller_edit.setText(a.get("hersteller", "") or "")
        self.lieferant_edit.setText(a.get("lieferant", "") or "")

        # Preise: float() wandelt den DB-Wert sicher in eine Dezimalzahl um
        # "or 0" verhindert Fehler, wenn der Wert None ist
        self.ek_spin.setValue(float(a.get("einkaufspreis", 0) or 0))
        self.vk_spin.setValue(float(a.get("verkaufspreis", 0) or 0))

        # MwSt.-Satz als Text im Dropdown suchen (z.B. "19.0")
        mwst_idx = self.mwst_combo.findText(str(a.get("mwst_satz", 19.0)))
        if mwst_idx >= 0:
            self.mwst_combo.setCurrentIndex(mwst_idx)

        # Lagerbestand und Mindestbestand als Ganzzahlen setzen
        self.bestand_spin.setValue(int(a.get("lagerbestand", 0) or 0))
        self.mindest_spin.setValue(int(a.get("mindestbestand", 5) or 5))

        # Einheit im Dropdown suchen (z.B. "Stück")
        einheit_idx = self.einheit_combo.findText(a.get("einheit", "Stück"))
        if einheit_idx >= 0:
            self.einheit_combo.setCurrentIndex(einheit_idx)

        # Beschreibung als reinen Text setzen (kein HTML)
        self.beschr_edit.setPlainText(a.get("beschreibung", "") or "")

        # Aktiv-Status: bool() wandelt 1 in True und 0 in False um
        self.aktiv_check.setChecked(bool(a.get("aktiv", 1)))

    def _speichern(self):
        """
        Liest alle Eingabefelder aus, prüft Pflichtfelder und speichert
        die Daten in self.result_data, bevor der Dialog geschlossen wird.

        Pflichtfeld: Bezeichnung (muss ausgefüllt sein).

        Nach accept() gibt dlg.exec() den Wert Accepted zurück, sodass
        der aufrufende Code die Daten in der Datenbank speichern kann.
        """
        # Artikelbezeichnung einlesen (.strip() entfernt Leerzeichen am Rand)
        bez = self.bez_edit.text().strip()
        # Verkaufspreis einlesen (Dezimalzahl)
        vk = self.vk_spin.value()

        # Pflichtfeldprüfung: Bezeichnung muss vorhanden sein
        if not bez:
            QMessageBox.warning(self, "Pflichtfeld", "Bitte eine Artikelbezeichnung eingeben.")
            return  # Methode vorzeitig beenden – Dialog bleibt geöffnet

        # Alle Formulardaten in einem Wörterbuch zusammenstellen
        self.result_data = {
            "id":            self.artikel.get("id"),          # None bei neuem Artikel
            "bezeichnung":   bez,
            # currentData() liefert den mit addItem() gespeicherten Datenwert (die ID)
            "kategorie_id":  self.kat_combo.currentData(),
            "hersteller":    self.hersteller_edit.text().strip(),
            "lieferant":     self.lieferant_edit.text().strip(),
            "einkaufspreis": self.ek_spin.value(),
            "verkaufspreis": vk,
            # MwSt. aus dem Dropdown-Text in eine Dezimalzahl umwandeln
            "mwst_satz":     float(self.mwst_combo.currentText()),
            "lagerbestand":  self.bestand_spin.value(),
            "mindestbestand": self.mindest_spin.value(),
            "einheit":       self.einheit_combo.currentText(),
            "beschreibung":  self.beschr_edit.toPlainText().strip(),
            # int() wandelt True/False der Checkbox in 1/0 um (für die Datenbank)
            "aktiv":         int(self.aktiv_check.isChecked()),
        }

        # Dialog erfolgreich schließen
        self.accept()


# =============================================================================
# Klasse ArtikelWidget
# =============================================================================

class ArtikelWidget(QWidget):
    """
    Haupt-Widget der Registerkarte "Artikel".

    Zeigt eine durchsuchbare und nach Kategorien filterbare Tabelle
    aller Artikel an. Für jeden Artikel wird neben den Stammdaten auch
    der Brutto-Verkaufspreis (inkl. MwSt.) und ein farbiger Status-Badge
    (Verfügbar / Nachbestellen / Inaktiv) angezeigt.

    Signale:
        artikel_geaendert: Wird ausgelöst, nachdem ein Artikel angelegt,
                           bearbeitet oder gelöscht wurde. Andere Teile
                           der Anwendung können dieses Signal empfangen
                           und sich aktualisieren (z.B. die Bestellmaske).
    """

    # Signal ohne Parameter: signalisiert nur, dass sich etwas geändert hat
    artikel_geaendert = pyqtSignal()

    def __init__(self, parent=None):
        """
        Konstruktor des ArtikelWidget.

        Baut die Oberfläche auf und lädt beim Start alle vorhandenen
        Artikel aus der Datenbank.

        Args:
            parent (QWidget, optional): Übergeordnetes Widget.
        """
        # Elternklasse QWidget initialisieren
        super().__init__(parent)

        # Benutzeroberfläche aufbauen
        self._setup_ui()

        # Tabelle sofort mit den aktuellen Datenbankdaten befüllen
        self.refresh()

    def _setup_ui(self):
        """
        Erstellt das Layout des ArtikelWidget:

          1. Toolbar   – Suchleiste + Kategorie-Filter-Dropdown + "Neuer Artikel"-Button
          2. Info-Zeile – zeigt Anzahl der Treffer und Nachbestellwarnungen
          3. Tabelle   – zeigt alle Artikel mit Statusbadge und Aktionsbuttons
        """
        # Haupt-Layout: Bereiche senkrecht anordnen
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # --- Toolbar ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Suchleiste im abgerundeten "Pill"-Stil
        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            background: white;
            border: 1.5px solid {COLOR_BORDER};
            border-radius: 20px;
        """)
        search_frame.setFixedHeight(40)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(14, 0, 14, 0)
        # Lupe als Dekoration (kein echtes Icon-Widget)
        search_layout.addWidget(QLabel("🔍"))

        # Texteingabe für Suchbegriff
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Artikel suchen (Bezeichnung, Hersteller, Kategorie...)")
        self.search_edit.setFrame(False)
        self.search_edit.setStyleSheet("background: transparent; border: none; font-size: 13px;")
        # Bei jeder Eingabe sofort die Tabelle aktualisieren
        self.search_edit.textChanged.connect(self.refresh)
        search_layout.addWidget(self.search_edit)
        # stretch=1: Suchleiste bekommt den gesamten freien Platz in der Toolbar
        toolbar.addWidget(search_frame, stretch=1)

        # Kategorie-Filter-Dropdown neben der Suchleiste
        self.filter_combo = QComboBox()
        self.filter_combo.setFixedHeight(40)
        self.filter_combo.addItem("Alle Kategorien", "")   # Leerer Eintrag = kein Filter
        # Alle Kategorien aus der DB laden und als Einträge hinzufügen
        for k in db.get_kategorien():
            self.filter_combo.addItem(k["name"], k["id"])
        # Bei Änderung der Auswahl die Tabelle sofort aktualisieren
        self.filter_combo.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.filter_combo)

        # "Neuer Artikel"-Button
        neu_btn = QPushButton("➕  Neuer Artikel")
        neu_btn.setObjectName("btn_primary")
        neu_btn.setFixedHeight(40)
        neu_btn.clicked.connect(self._neuer_artikel)
        toolbar.addWidget(neu_btn)

        layout.addLayout(toolbar)

        # --- Info-Zeile ---
        # Zeigt z.B. "24 Artikel gefunden  ·  ⚠️ 3 unter Mindestbestand"
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        layout.addWidget(self.info_lbl)

        # --- Tabelle ---
        self.table = QTableWidget()
        self.table.setColumnCount(10)   # 10 Spalten: 8 Daten + 1 Status + 1 Aktionen

        # Spaltenköpfe der Tabelle setzen
        self.table.setHorizontalHeaderLabels([
            "Art.-Nr.", "Bezeichnung", "Kategorie", "Hersteller",
            "EK", "VK (Brutto)", "Bestand", "Mind.", "Status", "Aktionen"
        ])

        # Zebramuster: jede zweite Zeile hat einen anderen Hintergrund
        self.table.setAlternatingRowColors(True)

        # Klick markiert die gesamte Zeile, nicht nur eine Zelle
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # Zellen können nicht direkt in der Tabelle bearbeitet werden
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Zeilennummern am linken Rand ausblenden
        self.table.verticalHeader().setVisible(False)

        # Gitternetz ausblenden für modernes Aussehen
        self.table.setShowGrid(False)

        # Alle Spalten strecken sich gleichmäßig – danach einzelne anpassen
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Spalten mit kurzen Inhalten: passen sich dem Inhalt an (ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Art.-Nr.
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # EK
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # VK
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Bestand
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Mindest
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Status
        # Aktionsspalte: feste Breite
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(9, 160)

        # Standard-Zeilenhöhe für alle Zeilen
        self.table.verticalHeader().setDefaultSectionSize(46)

        # Doppelklick öffnet den Bearbeiten-Dialog für die angeklickte Zeile
        self.table.doubleClicked.connect(self._bearbeite_zeile)

        layout.addWidget(self.table)

    def refresh(self):
        """
        Lädt alle Artikel aus der Datenbank und befüllt die Tabelle neu.

        Berücksichtigt dabei:
          - Den Suchbegriff aus dem Textfeld (Volltextsuche in der DB)
          - Den gewählten Kategorie-Filter (clientseitige Filterung)

        In der Info-Zeile wird die Anzahl der Treffer und, falls vorhanden,
        eine Warnung bei Artikeln unter dem Mindestbestand angezeigt.

        Wird aufgerufen:
          - Beim ersten Laden (im Konstruktor),
          - Bei Texteingabe in die Suchleiste,
          - Bei Änderung des Kategorie-Filters,
          - Nach dem Anlegen, Bearbeiten oder Löschen eines Artikels.
        """
        # Suchbegriff aus dem Eingabefeld holen
        suche = self.search_edit.text().strip()

        # Alle Artikel laden, die zum Suchbegriff passen (DB-seitige Suche)
        artikel = db.get_alle_artikel(suche)

        # --- Kategorie-Filter (clientseitig) ---
        # currentData() liefert den Datenwert des gewählten Eintrags
        # "" bedeutet "Alle Kategorien" (kein Filter aktiv)
        kat_filter = self.filter_combo.currentData()
        if kat_filter:
            # Aktuell gewählten Kategorienamen auslesen
            kat_name = self.filter_combo.currentText()
            # Liste filtern: nur Artikel behalten, deren Kategorie übereinstimmt
            # Dies ist ein List Comprehension – kurzform einer for-Schleife mit if
            artikel = [a for a in artikel if a.get("kategorie") == kat_name]

        # Anzahl der Artikel, die unter dem Mindestbestand liegen (Nachbestellen-Flag)
        nachbestellen = sum(1 for a in artikel if a.get("nachbestellen"))

        # Info-Text aufbauen
        info = f"{len(artikel)} Artikel gefunden"
        if nachbestellen:
            # Warnhinweis anhängen, wenn mindestens ein Artikel nachbestellt werden muss
            info += f"  ·  ⚠️ {nachbestellen} unter Mindestbestand"
        self.info_lbl.setText(info)

        # Anzahl der Tabellenzeilen anpassen
        self.table.setRowCount(len(artikel))

        # Jede Zeile mit den Artikeldaten befüllen
        for row, a in enumerate(artikel):
            # Brutto-Verkaufspreis berechnen: Netto * (1 + MwSt./100)
            # Beispiel: 100 € * (1 + 19/100) = 100 € * 1,19 = 119 €
            vk_brutto = a.get("verkaufspreis", 0) * (1 + a.get("mwst_satz", 19) / 100)

            # Die 8 anzuzeigenden Datenwerte als Liste
            items = [
                a.get("artikelnummer", ""),
                a.get("bezeichnung", ""),
                a.get("kategorie") or "–",       # "–" wenn kein Wert vorhanden
                a.get("hersteller") or "–",
                f"€ {a.get('einkaufspreis', 0):.2f}",  # Formatiert auf 2 Nachkommastellen
                f"€ {vk_brutto:.2f}",
                str(a.get("lagerbestand", 0)),
                str(a.get("mindestbestand", 0)),
            ]

            # Spalten 0–7 mit den Datenwerten befüllen
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)

                # Unsichtbare Artikel-ID in der Zelle speichern (für spätere Zugriffe)
                item.setData(Qt.ItemDataRole.UserRole, a["id"])

                # Text linksbündig und vertikal zentriert ausrichten
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

                # Sonderbehandlung für die Bestandsspalte (Spalte 6):
                # Wenn der Artikel nachbestellt werden muss, Text rot und fett darstellen
                if col == 6 and a.get("nachbestellen"):
                    item.setForeground(QColor(COLOR_DANGER))   # Rote Textfarbe
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

                self.table.setItem(row, col, item)

            # --- Status-Badge (Spalte 8) ---
            # Da ein farbiges Label kein normales Tabellen-Item ist, brauchen
            # wir ein eigenes Widget als Container (setCellWidget)
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(6, 4, 6, 4)

            # Passendes Badge je nach Artikelstatus erstellen
            if not a.get("aktiv", 1):
                # Artikel ist deaktiviert (z.B. ausgelaufenes Modell)
                badge = QLabel("Inaktiv")
                badge.setStyleSheet(
                    "background:#f0f2f5; color:#6c757d; border-radius:8px; "
                    "padding:3px 8px; font-size:11px; font-weight:600;"
                )
            elif a.get("nachbestellen"):
                # Bestand liegt unter dem Mindestbestand – Warnung anzeigen
                badge = QLabel("⚠ Nachbestellen")
                # "22" am Ende der Farbe = Hexadezimaler Alphawert (ca. 13% Deckkraft)
                # Ergibt einen sehr transparenten Hintergrund in der Warnfarbe
                badge.setStyleSheet(
                    f"background:{COLOR_WARNING}22; color:{COLOR_WARNING}; "
                    "border-radius:8px; padding:3px 8px; font-size:11px; font-weight:600;"
                )
            else:
                # Alles in Ordnung: Artikel ist aktiv und ausreichend vorrätig
                badge = QLabel("✓ Verfügbar")
                badge.setStyleSheet(
                    f"background:{COLOR_SUCCESS}22; color:{COLOR_SUCCESS}; "
                    "border-radius:8px; padding:3px 8px; font-size:11px; font-weight:600;"
                )

            status_layout.addWidget(badge)
            # Badge-Widget in Spalte 8 der aktuellen Zeile einfügen
            self.table.setCellWidget(row, 8, status_widget)

            # --- Aktions-Buttons (Spalte 9) ---
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(6, 4, 6, 4)
            btn_layout.setSpacing(6)

            # "Bearbeiten"-Button mit gespeicherter Artikel-ID
            edit_btn = QPushButton("✏️ Bearbeiten")
            edit_btn.setObjectName("btn_icon")
            edit_btn.setFixedHeight(30)
            # Artikel-ID als Property speichern, damit der Slot weiß, welcher Artikel gemeint ist
            edit_btn.setProperty("art_id", a["id"])
            edit_btn.clicked.connect(self._bearbeite_artikel)

            # "Löschen"-Button (nur Mülleimer-Icon, quadratisch)
            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("btn_danger")
            del_btn.setFixedSize(30, 30)
            del_btn.setProperty("art_id", a["id"])
            del_btn.clicked.connect(self._loesche_artikel)

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)

            # Button-Widget in die Aktionsspalte der aktuellen Zeile einfügen
            self.table.setCellWidget(row, 9, btn_widget)

    def _neuer_artikel(self):
        """
        Öffnet den ArtikelDialog zum Anlegen eines neuen Artikels.

        Nach dem Speichern wird der Artikel in der Datenbank gespeichert,
        die Tabelle aktualisiert und das Signal artikel_geaendert ausgelöst.
        """
        # Dialog ohne vorhandene Artikeldaten öffnen (neuer Artikel)
        dlg = ArtikelDialog(self)

        # exec() blockiert bis der Dialog geschlossen wird
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Formulardaten aus dem Dialog in die Datenbank schreiben
            db.speichere_artikel(dlg.result_data)
            # Tabelle aktualisieren, damit der neue Artikel erscheint
            self.refresh()
            # Andere Widgets (z.B. Bestellmaske) über Änderung informieren
            self.artikel_geaendert.emit()

    def _bearbeite_zeile(self, index):
        """
        Wird beim Doppelklick auf eine Tabellenzeile aufgerufen.
        Öffnet den ArtikelDialog für den Artikel in der angeklickten Zeile.

        Args:
            index (QModelIndex): Position der angeklickten Zelle
                                 (enthält Zeile und Spalte).
        """
        # Zelle in Spalte 0 der geklickten Zeile abrufen
        item = self.table.item(index.row(), 0)
        if item:
            # Versteckte Artikel-ID aus der Zelle lesen und Artikeldaten laden
            a = db.get_artikel(item.data(Qt.ItemDataRole.UserRole))
            if a:
                dlg = ArtikelDialog(self, a)
                if dlg.exec() == QDialog.DialogCode.Accepted:
                    db.speichere_artikel(dlg.result_data)
                    self.refresh()
                    self.artikel_geaendert.emit()

    def _bearbeite_artikel(self):
        """
        Slot für den "Bearbeiten"-Button in der Aktionsspalte.

        self.sender() gibt den Button zurück, der das Signal ausgelöst hat.
        Über die gespeicherte Property "art_id" wird der korrekte Artikel
        aus der Datenbank geladen.
        """
        # Button, der den Klick ausgelöst hat
        btn = self.sender()

        # Artikeldaten über die im Button gespeicherte ID laden
        a = db.get_artikel(btn.property("art_id"))
        if a:
            dlg = ArtikelDialog(self, a)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                db.speichere_artikel(dlg.result_data)
                self.refresh()
                self.artikel_geaendert.emit()

    def _loesche_artikel(self):
        """
        Slot für den "Löschen"-Button in der Aktionsspalte.

        Zeigt zuerst eine Sicherheitsabfrage an. Wenn der Nutzer bestätigt,
        wird der Artikel gelöscht. Artikel, die in Bestellungen verwendet
        werden, können nicht gelöscht werden – dann erscheint eine
        Fehlermeldung.
        """
        # Button und zugehörige Artikel-ID ermitteln
        btn = self.sender()
        a = db.get_artikel(btn.property("art_id"))
        if not a:
            return  # Artikel existiert nicht mehr – nichts zu tun

        # Sicherheitsabfrage anzeigen; Standardantwort ist "Nein"
        reply = QMessageBox.question(
            self, "Artikel löschen",
            f"Soll <b>{a['bezeichnung']}</b> gelöscht werden?<br>"
            "<small style='color:gray'>Artikel in Bestellungen können nicht gelöscht werden.</small>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No   # Sicherer Standard: Nein
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Löschen versuchen; gibt True zurück wenn erfolgreich
            ok = db.loesche_artikel(btn.property("art_id"))
            if ok:
                # Tabelle aktualisieren und andere Widgets informieren
                self.refresh()
                self.artikel_geaendert.emit()
            else:
                # Artikel ist in Bestellungen referenziert und kann nicht gelöscht werden
                QMessageBox.warning(self, "Nicht möglich",
                    "Dieser Artikel ist in Bestellungen vorhanden und kann nicht gelöscht werden.")
