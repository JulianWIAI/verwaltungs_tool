"""
Radsport Koch GmbH – Bestellverwaltung
=======================================
Dieses Modul enthält alle grafischen Komponenten (Widgets und Dialoge),
die für die Verwaltung von Kundenbestellungen zuständig sind.

Aufbau des Moduls:
  - PositionenTabelle  : Wiederverwendbares Eingabe-Widget für einzelne
                         Bestellpositionen (Artikel + Menge + Preis) inkl.
                         Live-Berechnung der Zwischensumme.
  - BestellungDialog   : Modaler Dialog zum Anlegen und Bearbeiten einer
                         vollständigen Bestellung (Kopfdaten + Positionen).
  - BestellungDetailDialog : Nur-Lesen-Ansicht einer bestehenden Bestellung
                              mit Schnell-Update für Status und Zahlungsstatus.
  - BestellungenWidget : Haupt-Widget der Bestellübersicht – zeigt alle
                         Bestellungen in einer Tabelle mit Such-, Filter-
                         und CRUD-Funktionen (Erstellen, Lesen, Bearbeiten,
                         Löschen).

Alle Datenbankzugriffe laufen über das Modul ``database`` (importiert als
``db``). Die Farb- und Stilkonstanten kommen aus dem Modul ``styles``.
"""

# ---------------------------------------------------------------------------
# Importe aus PyQt6 – dem GUI-Framework
# QWidget, QDialog usw. sind Basisklassen für Fenster und Dialoge.
# QLayout-Klassen (QVBoxLayout, QHBoxLayout) ordnen Widgets vertikal/horizontal an.
# ---------------------------------------------------------------------------
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QDialog, QComboBox, QTextEdit, QDoubleSpinBox,
    QSpinBox, QMessageBox, QSizePolicy, QScrollArea, QAbstractItemView,
    QDateEdit, QSplitter, QFileDialog
)

# csv – Standardbibliothek zum Lesen und Schreiben von CSV-Dateien
import csv
# Qt enthält Konstanten (z. B. für Ausrichtung), pyqtSignal ermöglicht eigene
# Signale, QDate ist PyQt6s Klasse für Datumswerte.
from PyQt6.QtCore import Qt, pyqtSignal, QDate
# QFont für Schriftarten, QColor für Farbobjekte
from PyQt6.QtGui import QFont, QColor
# Eigenes Datenbankmodul – kapselt alle SQL-Abfragen
import database as db
# Farbkonstanten und Status-/Zahlungs-Farbmappings aus dem Stil-Modul
from styles import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_DANGER, COLOR_WHITE,
    COLOR_BG, COLOR_TEXT_LIGHT, COLOR_BORDER, COLOR_WARNING,
    COLOR_SUCCESS, STATUS_FARBEN, ZAHLUNG_FARBEN, COLOR_INFO
)


# ===========================================================================
# Klasse: PositionenTabelle
# ===========================================================================
class PositionenTabelle(QWidget):
    """
    Wiederverwendbares Widget für Bestellpositionen mit Live-Summe.

    Dieses Widget zeigt:
      1. Eine Dropdown-Liste aller aktiven Artikel zur Auswahl
      2. Eingabefelder für Menge und Einzelpreis
      3. Einen "Position hinzufügen"-Button
      4. Eine Tabelle mit allen bereits hinzugefügten Positionen
         (inkl. Löschen-Buttons pro Zeile)
      5. Eine Zeile mit der aktuellen Netto-Zwischensumme

    Das Widget sendet das Signal ``geaendert``, sobald sich die
    Positionsliste ändert, damit übergeordnete Dialoge (z. B.
    BestellungDialog) ihre Gesamtsummen-Anzeige aktualisieren können.
    """

    # Signal, das ausgelöst wird, wenn Positionen hinzugefügt oder entfernt
    # werden. Empfänger können darauf reagieren (z. B. Summe neu berechnen).
    geaendert = pyqtSignal()

    def __init__(self, parent=None):
        """
        Konstruktor – initialisiert das Widget.

        Lädt zunächst alle aktiven Artikel aus der Datenbank und baut
        danach die gesamte Benutzeroberfläche auf.

        Parameter:
            parent: Das übergeordnete Qt-Widget (oder None für eigenständig).
        """
        # Basisklassen-Konstruktor aufrufen – notwendig für alle Qt-Widgets
        super().__init__(parent)

        # Alle aktiven Artikel aus der Datenbank laden (nur aktive, damit
        # deaktivierte Artikel nicht mehr bestellt werden können)
        self.artikel_liste = db.get_alle_artikel(nur_aktiv=True)

        # Benutzeroberfläche aufbauen
        self._setup_ui()

    def _setup_ui(self):
        """
        Erstellt und konfiguriert alle UI-Elemente des Widgets.

        Aufbau (von oben nach unten):
          - Zeile 1: Artikel-Auswahl (Dropdown/ComboBox)
          - Zeile 2: Menge-Spinner + Preis-Spinner + "Hinzufügen"-Button
          - Tabelle:  Liste der hinzugefügten Positionen
          - Summe:    Anzeige der Netto-Zwischensumme
        """
        # Vertikales Hauptlayout für dieses Widget erstellen
        layout = QVBoxLayout(self)
        # Kein Außenabstand, da das Widget in einen Dialog eingebettet wird
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)  # 8 Pixel Abstand zwischen den Elementen

        # --- Zeile 1: Artikel-Dropdown ---
        # QComboBox = eine Klappliste zur Auswahl eines Eintrags
        self.art_combo = QComboBox()
        # Ersten Eintrag als Platzhalter hinzufügen; userData=None, damit wir
        # erkennen können, dass noch kein Artikel ausgewählt wurde
        self.art_combo.addItem("-- Artikel wählen --", None)

        # Für jeden Artikel aus der Datenbank einen Eintrag anlegen.
        # Als anzuzeigender Text: Artikelnummer | Bezeichnung (Preis)
        # Als userData wird das gesamte Artikel-Dict mitgegeben, damit wir
        # später bequem auf alle Felder zugreifen können.
        for a in self.artikel_liste:
            self.art_combo.addItem(
                f"{a['artikelnummer']}  |  {a['bezeichnung']}  (€ {a['verkaufspreis']:.2f})",
                a  # Das gesamte Artikel-Dictionary wird als Datenwert gespeichert
            )

        # Wenn ein anderer Artikel gewählt wird, soll der Preis automatisch
        # in das Preis-Eingabefeld übernommen werden.
        self.art_combo.currentIndexChanged.connect(self._art_selected)
        layout.addWidget(self.art_combo)

        # --- Zeile 2: Menge / Preis / Button ---
        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)

        # QSpinBox = Ganzzahl-Eingabefeld mit Pfeil-Buttons zum Hoch-/Runterblättern
        self.menge_spin = QSpinBox()
        self.menge_spin.setRange(1, 9999)   # Minimale Menge 1, maximale Menge 9999
        self.menge_spin.setValue(1)          # Standardwert: 1 Stück
        self.menge_spin.setFixedWidth(80)    # Feste Breite damit das Layout sauber bleibt

        # QDoubleSpinBox = Dezimalzahl-Eingabefeld (für Geldbeträge)
        self.einzelpreis_spin = QDoubleSpinBox()
        self.einzelpreis_spin.setRange(0, 99999.99)   # Preisbereich in Euro
        self.einzelpreis_spin.setDecimals(2)           # Zwei Nachkommastellen (Cent)
        self.einzelpreis_spin.setPrefix("€ ")          # Euro-Zeichen vor dem Wert
        self.einzelpreis_spin.setFixedWidth(120)

        # Button zum Hinzufügen der gewählten Position zur Liste
        add_btn = QPushButton("➕ Position hinzufügen")
        add_btn.setObjectName("btn_secondary")   # CSS-Klasse aus styles.py
        add_btn.setFixedHeight(36)
        # Verbindung: Klick auf den Button → _position_hinzufuegen aufrufen
        add_btn.clicked.connect(self._position_hinzufuegen)

        # Steuerelemente in die horizontale Zeile einbauen
        controls_row.addWidget(QLabel("Menge:"))
        controls_row.addWidget(self.menge_spin)
        controls_row.addWidget(QLabel("Preis:"))
        controls_row.addWidget(self.einzelpreis_spin)
        controls_row.addStretch()             # Leeraum, damit der Button rechts bleibt
        controls_row.addWidget(add_btn)
        layout.addLayout(controls_row)

        # --- Positions-Tabelle ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # 6 Spalten: Art.-Nr., Bezeichnung, Menge, Preis, Gesamt, Löschen
        self.table.setHorizontalHeaderLabels([
            "Art.-Nr.", "Bezeichnung", "Menge", "Einzelpreis", "Gesamt (Netto)", ""
        ])
        # Zeilennummern links ausblenden – sieht aufgeräumter aus
        self.table.verticalHeader().setVisible(False)
        # Benutzer darf keine Zellen direkt bearbeiten – nur über die Buttons
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # Kein Gitternetz – moderneres Erscheinungsbild
        self.table.setShowGrid(False)
        # Abwechselnde Zeilenhintergrundfarben für bessere Lesbarkeit
        self.table.setAlternatingRowColors(True)

        # Spaltenbreiten einstellen:
        # Stretch = Spalte dehnt sich aus, um den verfügbaren Platz zu füllen
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Spalten 2-4 passen sich dem Inhalt an (keine künstliche Dehnung)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        # Spalte 5 (Löschen-Button) bekommt eine feste, kleine Breite
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 40)

        # Minimale und maximale Höhe der Tabelle begrenzen
        self.table.setMinimumHeight(120)
        self.table.setMaximumHeight(280)
        layout.addWidget(self.table)

        # --- Summenzeile ---
        sum_row = QHBoxLayout()
        sum_row.addStretch()  # Leeraum links, damit die Summe rechts ausgerichtet ist
        self.summe_lbl = QLabel("Zwischensumme Netto: € 0,00")
        # Fette, etwas größere Schrift damit die Summe auffällt
        self.summe_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.summe_lbl.setStyleSheet(f"color: {COLOR_PRIMARY};")
        sum_row.addWidget(self.summe_lbl)
        layout.addLayout(sum_row)

        # Interne Liste, in der alle hinzugefügten Positionen als Dicts
        # gespeichert werden (z. B. {"artikel_id": 3, "menge": 2, ...})
        self.positionen = []

    def _art_selected(self, idx):
        """
        Slot: Wird aufgerufen, wenn der Benutzer einen anderen Artikel in der
        Dropdown-Liste auswählt.

        Liest den Verkaufspreis des gewählten Artikels aus und trägt ihn
        automatisch in das Preis-Eingabefeld ein.

        Parameter:
            idx (int): Der Index des neu gewählten Eintrags in der ComboBox
                       (wird hier nicht direkt benötigt, da wir currentData()
                       verwenden).
        """
        # currentData() liefert das Artikel-Dict zurück, das beim Befüllen
        # der ComboBox als userData mitgegeben wurde
        art = self.art_combo.currentData()
        if art:
            # Preis aus dem Artikel-Dict lesen und in den Spinner eintragen
            self.einzelpreis_spin.setValue(float(art.get("verkaufspreis", 0)))

    def _position_hinzufuegen(self):
        """
        Slot: Fügt eine neue Position zur internen Positionsliste hinzu
        und aktualisiert die Tabellenanzeige.

        Ablauf:
          1. Prüfen, ob ein Artikel gewählt wurde (sonst Abbruch).
          2. Menge und Preis aus den Eingabefeldern lesen.
          3. Falls der Artikel bereits in der Liste ist, wird nur die
             Menge erhöht (kein Duplikat).
          4. Ansonsten wird ein neues Positions-Dict angelegt.
          5. Tabelle neu rendern und Signal ``geaendert`` senden.
        """
        # Gewähltes Artikel-Dict aus der ComboBox holen
        art = self.art_combo.currentData()
        # Wenn kein Artikel gewählt (Platzhalter-Eintrag), nichts tun
        if not art:
            return

        # Eingegebene Menge aus dem Spinner lesen
        menge = self.menge_spin.value()

        # interpretText() erzwingt, dass der aktuell eingetippte Text
        # sofort in einen Zahlenwert umgewandelt wird (wichtig, wenn der
        # Benutzer gerade tippt und noch nicht bestätigt hat)
        self.einzelpreis_spin.interpretText()
        preis = self.einzelpreis_spin.value()

        # Prüfen, ob der Artikel bereits in der Liste vorhanden ist.
        # Falls ja, nur die Menge addieren statt einen zweiten Eintrag anzulegen.
        for p in self.positionen:
            if p["artikel_id"] == art["id"]:
                p["menge"] += menge        # Menge erhöhen
                self._render()             # Tabelle aktualisieren
                self.geaendert.emit()      # Übergeordnete Widgets informieren
                return                     # Funktion früh verlassen

        # Artikel noch nicht vorhanden → neues Positions-Dict anlegen
        self.positionen.append({
            "artikel_id":   art["id"],
            "artikelnummer": art.get("artikelnummer",""),
            "bezeichnung":  art.get("bezeichnung",""),
            "menge":        menge,
            "einzelpreis":  preis,
            # MwSt-Satz aus dem Artikel lesen; Fallback auf 19 % (dt. Regelsteuersatz)
            "mwst_satz":    float(art.get("mwst_satz", 19)),
        })
        # Tabelle neu zeichnen
        self._render()
        # Signal aussenden, damit z. B. der Dialog die Gesamtsumme aktualisiert
        self.geaendert.emit()

    def _render(self):
        """
        Zeichnet die Positionstabelle anhand der aktuellen ``self.positionen``-
        Liste neu und aktualisiert die Zwischensummen-Anzeige.

        Für jede Position werden fünf Text-Zellen befüllt sowie ein
        Löschen-Button in der sechsten Spalte platziert.
        Die Netto-Summe wird gleichzeitig aufsummiert und in der
        Summen-Zeile angezeigt.
        """
        # Tabellenzeilen-Anzahl an die Länge der Positionsliste anpassen
        self.table.setRowCount(len(self.positionen))

        gesamt_netto = 0.0  # Laufende Summe aller Positionsbeträge

        for row, p in enumerate(self.positionen):
            # Netto-Betrag dieser Position berechnen (Menge × Einzelpreis)
            netto = p["menge"] * p["einzelpreis"]
            gesamt_netto += netto   # Zur Gesamtsumme addieren

            # Tabellenzellen mit den Positionsdaten befüllen
            self.table.setItem(row, 0, QTableWidgetItem(p.get("artikelnummer","")))
            self.table.setItem(row, 1, QTableWidgetItem(p.get("bezeichnung","")))
            self.table.setItem(row, 2, QTableWidgetItem(str(p["menge"])))
            self.table.setItem(row, 3, QTableWidgetItem(f"€ {p['einzelpreis']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"€ {netto:.2f}"))

            # Löschen-Button für diese Zeile erstellen
            del_btn = QPushButton("✕")
            # Transparenter Hintergrund, nur rotes "✕" sichtbar
            del_btn.setStyleSheet(f"color: {COLOR_DANGER}; background: transparent; border: none; font-weight: bold;")
            # Den Index der Zeile als Widget-Property speichern, damit der
            # Slot _loesche_position weiß, welche Position gelöscht werden soll
            del_btn.setProperty("pos_idx", row)
            del_btn.clicked.connect(self._loesche_position)
            # Widget (Button) direkt in die Tabellenzelle einsetzen
            self.table.setCellWidget(row, 5, del_btn)

        # Summen-Label mit der berechneten Netto-Gesamtsumme aktualisieren.
        # Der Formatierungsbezeichner :,.2f sorgt für Tausendertrennzeichen
        # und genau zwei Nachkommastellen.
        self.summe_lbl.setText(f"Zwischensumme Netto: € {gesamt_netto:,.2f}")

    def _loesche_position(self):
        """
        Slot: Entfernt eine Position aus der Liste.

        Der zugehörige Zeilenindex wurde beim Erstellen des Buttons als
        Property ``pos_idx`` gespeichert. Über ``self.sender()`` holen
        wir uns den Button, der den Klick ausgelöst hat, und lesen dann
        die Property aus.
        """
        # sender() gibt das Objekt zurück, das das Signal ausgelöst hat
        # – in diesem Fall den geklickten Löschen-Button
        idx = self.sender().property("pos_idx")

        # Sicherheitscheck: Index muss im gültigen Bereich liegen
        if 0 <= idx < len(self.positionen):
            self.positionen.pop(idx)   # Position aus der Liste entfernen
            self._render()             # Tabelle neu zeichnen
            self.geaendert.emit()      # Übergeordnete Widgets informieren

    def set_positionen(self, positionen: list):
        """
        Lädt eine externe Positionsliste in das Widget (z. B. beim
        Bearbeiten einer vorhandenen Bestellung).

        Die interne Liste wird dabei vollständig ersetzt und die Tabelle
        neu gerendert.

        Parameter:
            positionen (list): Liste von Positions-Dicts aus der Datenbank.
                               Jedes Dict muss mindestens die Schlüssel
                               ``artikel_id``, ``menge`` und ``einzelpreis``
                               enthalten.
        """
        # Interne Liste leeren, bevor neue Daten eingefügt werden
        self.positionen = []
        for p in positionen:
            # Jede Position in ein einheitliches internes Format umwandeln,
            # fehlende Felder werden mit Standardwerten aufgefüllt
            self.positionen.append({
                "artikel_id":    p["artikel_id"],
                "artikelnummer": p.get("artikelnummer",""),
                "bezeichnung":   p.get("bezeichnung",""),
                "menge":         p["menge"],
                "einzelpreis":   p["einzelpreis"],
                "mwst_satz":     p.get("mwst_satz", 19),  # Fallback: 19 %
            })
        # Tabelle mit den geladenen Daten neu aufbauen
        self._render()

    def get_positionen(self) -> list:
        """
        Gibt die aktuelle Positionsliste zurück.

        Rückgabe:
            list: Liste der Positions-Dicts, wie sie intern gespeichert sind.
        """
        return self.positionen

    def get_netto(self) -> float:
        """
        Berechnet und gibt den Netto-Gesamtbetrag aller Positionen zurück.

        Verwendet einen Generator-Ausdruck, der für jede Position
        Menge × Einzelpreis berechnet und alle Werte aufaddiert.

        Rückgabe:
            float: Summe aller (Menge × Einzelpreis)-Werte in Euro.
        """
        # sum() mit einem Generator: für jede Position p wird
        # p["menge"] * p["einzelpreis"] berechnet und alles summiert
        return sum(p["menge"] * p["einzelpreis"] for p in self.positionen)


# ===========================================================================
# Klasse: BestellungDialog
# ===========================================================================
class BestellungDialog(QDialog):
    """
    Modaler Dialog zum Anlegen einer neuen Bestellung oder zum Bearbeiten
    einer vorhandenen Bestellung.

    Wird kein ``bestellung``-Dict übergeben, öffnet sich der Dialog im
    "Neu"-Modus. Wird ein bestehendes Bestellungs-Dict übergeben, werden
    alle Felder vorausgefüllt ("Bearbeiten"-Modus).

    Nach erfolgreichem Speichern stehen die Ergebnisdaten in:
        self.result_data       – Kopfdaten der Bestellung (Dict)
        self.result_positionen – Liste der Bestellpositionen
    """

    def __init__(self, parent=None, bestellung: dict = None):
        """
        Konstruktor des Bestelldialogs.

        Parameter:
            parent     : Übergeordnetes Widget (oder None).
            bestellung : Dict mit den Daten einer vorhandenen Bestellung
                         zum Bearbeiten, oder None für eine neue Bestellung.
        """
        # Qt-Basiskonstruktor aufrufen
        super().__init__(parent)

        # Bestellungsdaten speichern; leeres Dict wenn keine übergeben wurden
        self.bestellung = bestellung or {}

        # Fenstertitel je nach Modus setzen
        self.setWindowTitle("Bestellung bearbeiten" if bestellung else "Neue Bestellung anlegen")

        # Mindestgröße des Dialogs festlegen
        self.setMinimumWidth(720)
        self.setMinimumHeight(700)

        # Modal = Der Dialog blockiert die Interaktion mit dem Hauptfenster,
        # bis er geschlossen wird
        self.setModal(True)

        # UI-Elemente aufbauen
        self._setup_ui()

        # Falls Bearbeitungsmodus: Felder mit vorhandenen Daten füllen
        if bestellung:
            self._fill_data()

        # Summe einmal initial berechnen und anzeigen
        self._update_summe()

    def _setup_ui(self):
        """
        Erstellt die vollständige Benutzeroberfläche des Dialogs.

        Struktur (von oben nach unten):
          1. Farbiger Header mit Dialogtitel
          2. Scrollbarer Inhaltsbereich:
             a. Kundenwahl + Lieferadresse
             b. Bestellstatus, Zahlungsart, Zahlungsstatus, Lieferdatum
             c. PositionenTabelle-Widget
             d. Rabatt + Versandkosten
             e. Summenkasten (Netto / MwSt / Brutto)
             f. Notizfeld
          3. Fußleiste mit Abbrechen- und Speichern-Button
        """
        # Hintergrundfarbe des Dialogs auf Weiß setzen
        self.setStyleSheet(f"QDialog {{ background: {COLOR_WHITE}; }}")

        # Haupt-Layout ohne Abstände – Header und Footer sollen bündig am Rand liegen
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Header-Bereich ---
        header = QFrame()
        header.setObjectName("bestellung_header")
        # Primärfarbe als Hintergrund für den Header-Balken
        header.setStyleSheet(f"QFrame#bestellung_header {{ background: {COLOR_PRIMARY}; }}")
        header.setFixedHeight(64)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        # Titel: "Bestellung bearbeiten" oder "Neue Bestellung"
        title_lbl = QLabel("📦  " + ("Bestellung bearbeiten" if self.bestellung else "Neue Bestellung"))
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLOR_WHITE};")
        h_layout.addWidget(title_lbl)
        layout.addWidget(header)

        # --- Scrollbarer Inhaltsbereich ---
        # QScrollArea ermöglicht das Scrollen, wenn der Inhalt größer als
        # das Fenster ist – wichtig für kleine Bildschirme
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)    # Widget passt sich der Größe an
        scroll.setFrameShape(QFrame.Shape.NoFrame)  # Keinen Rahmen um den Scroll-Bereich
        content = QWidget()               # Inhalts-Widget, das in die ScrollArea kommt
        scroll.setWidget(content)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(16)

        # --- Hilfsfunktionen für einheitliches Layout ---

        def section(text):
            """
            Erstellt eine Abschnitts-Überschrift mit Trennlinie.

            Parameter:
                text (str): Anzuzeigender Überschriftstext.
            Rückgabe:
                QLabel mit passendem Stil.
            """
            lbl = QLabel(text)
            lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            lbl.setStyleSheet(f"""
                color: {COLOR_PRIMARY};
                border-bottom: 2px solid {COLOR_SECONDARY};
                padding-bottom: 4px;
            """)
            return lbl

        def lbl(text):
            """
            Erstellt ein kleines Beschriftungs-Label für Formularfelder.

            Parameter:
                text (str): Feldbeschriftung.
            Rückgabe:
                QLabel mit kleiner, grauer Schrift.
            """
            l = QLabel(text)
            l.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {COLOR_TEXT_LIGHT};")
            return l

        # ── Abschnitt: Kunde ────────────────────────────────────────────────
        content_layout.addWidget(section("👤 Kunde"))
        kunde_row = QHBoxLayout()

        # Alle Kunden aus der Datenbank laden
        self.kunden = db.get_alle_kunden()
        self.kunde_combo = QComboBox()
        self.kunde_combo.addItem("-- Kunden wählen --", None)  # Platzhalter

        # Für jeden Kunden einen Eintrag anlegen (Kundennummer | Name (Ort))
        for k in self.kunden:
            self.kunde_combo.addItem(
                f"{k['kundennummer']}  |  {k['vorname']} {k['nachname']}  ({k.get('ort','')})",
                k["id"]   # Kunden-ID als userData speichern
            )

        # Wenn ein Kunde ausgewählt wird, die Lieferadresse automatisch befüllen
        self.kunde_combo.currentIndexChanged.connect(self._update_lieferadresse)

        # Kundenwahl-Spalte (Gewichtung 2 = doppelt so breit wie andere)
        col_k = QVBoxLayout(); col_k.setSpacing(4)
        col_k.addWidget(lbl("Kunde *")); col_k.addWidget(self.kunde_combo)
        kunde_row.addLayout(col_k, 2)

        # Lieferadresse – wird automatisch befüllt, kann aber auch manuell
        # geändert werden (z. B. abweichende Lieferadresse)
        self.liefer_edit = QLineEdit()
        self.liefer_edit.setPlaceholderText("Wird automatisch befüllt oder manuell eingeben")
        col_l = QVBoxLayout(); col_l.setSpacing(4)
        col_l.addWidget(lbl("Lieferadresse"))
        col_l.addWidget(self.liefer_edit)
        kunde_row.addLayout(col_l, 2)
        content_layout.addLayout(kunde_row)

        # ── Abschnitt: Status & Zahlung ─────────────────────────────────────
        content_layout.addWidget(section("📋 Status & Zahlung"))
        status_row = QHBoxLayout(); status_row.setSpacing(12)

        # Dropdown für den Bestellstatus
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Neu","In Bearbeitung","Versendet","Geliefert","Storniert","Zurückgegeben"])

        # Dropdown für die Zahlungsart
        self.zahlung_combo = QComboBox()
        self.zahlung_combo.addItems(["Bar","EC-Karte","Kreditkarte","Überweisung","Rechnung","PayPal"])

        # Dropdown für den Zahlungsstatus
        self.zahlstatus_combo = QComboBox()
        self.zahlstatus_combo.addItems(["Offen","Teilbezahlt","Bezahlt","Erstattet"])

        # Datumseingabe mit Kalender-Popup für das gewünschte Lieferdatum
        self.liefer_datum = QDateEdit()
        self.liefer_datum.setDisplayFormat("dd.MM.yyyy")   # Deutsches Datumsformat
        self.liefer_datum.setCalendarPopup(True)            # Kleiner Kalender aufklappbar
        # Standardmäßig 7 Tage ab heute vorschlagen
        self.liefer_datum.setDate(QDate.currentDate().addDays(7))

        # Alle vier Steuerelemente einheitlich in Spalten anordnen
        for lbl_t, widget in [("Bestellstatus", self.status_combo),
                                ("Zahlungsart", self.zahlung_combo),
                                ("Zahlungsstatus", self.zahlstatus_combo),
                                ("Lieferdatum", self.liefer_datum)]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(lbl(lbl_t)); col.addWidget(widget)
            status_row.addLayout(col)
        content_layout.addLayout(status_row)

        # ── Abschnitt: Bestellpositionen ────────────────────────────────────
        content_layout.addWidget(section("🛒 Bestellpositionen"))
        # Das wiederverwendbare PositionenTabelle-Widget einbinden
        self.positionen_widget = PositionenTabelle(self)
        # Wenn sich Positionen ändern, Gesamtsumme im Dialog aktualisieren
        self.positionen_widget.geaendert.connect(self._update_summe)
        content_layout.addWidget(self.positionen_widget)

        # ── Konditionen: Rabatt und Versandkosten ───────────────────────────
        cond_row = QHBoxLayout(); cond_row.setSpacing(12)

        # Rabatt in Prozent (0–100 %, eine Nachkommastelle)
        self.rabatt_spin = QDoubleSpinBox()
        self.rabatt_spin.setRange(0, 100)
        self.rabatt_spin.setSuffix(" %")     # Einheit hinter dem Wert anzeigen
        self.rabatt_spin.setDecimals(1)
        # Bei Änderung sofort die Summe neu berechnen
        self.rabatt_spin.valueChanged.connect(self._update_summe)

        # Versandkosten in Euro
        self.versand_spin = QDoubleSpinBox()
        self.versand_spin.setRange(0, 999.99)
        self.versand_spin.setPrefix("€ ")
        self.versand_spin.setDecimals(2)
        # Bei Änderung sofort die Summe neu berechnen
        self.versand_spin.valueChanged.connect(self._update_summe)

        # Beide Felder einheitlich nebeneinander anordnen
        for lbl_t, widget in [("Gesamtrabatt (%)", self.rabatt_spin),
                                ("Versandkosten", self.versand_spin)]:
            col = QVBoxLayout(); col.setSpacing(4)
            col.addWidget(lbl(lbl_t)); col.addWidget(widget)
            cond_row.addLayout(col)
        cond_row.addStretch()   # Restlichen Platz leer lassen
        content_layout.addLayout(cond_row)

        # ── Summenkasten ────────────────────────────────────────────────────
        # Rahmen mit leichtem Farbhintergrund für optische Hervorhebung
        summe_frame = QFrame()
        summe_frame.setStyleSheet(f"""
            background: {COLOR_PRIMARY}18;
            border: 1px solid {COLOR_PRIMARY}30;
            border-radius: 10px;
            padding: 14px;
        """)
        # Hinweis: "18" und "30" am Ende sind Hexadezimalwerte für die
        # Alpha-Transparenz (18hex = ~9%, 30hex = ~19% Deckkraft)
        summe_layout = QHBoxLayout(summe_frame)
        summe_layout.addStretch()

        # Drei Labels für die aufgeteilte Summenanzeige
        self.gesamt_netto_lbl = QLabel("Netto: € 0,00")
        self.gesamt_netto_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")

        self.gesamt_mwst_lbl  = QLabel("MwSt.: € 0,00")
        self.gesamt_mwst_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")

        # Bruttobetrag hervorgehoben (größer, fett, Primärfarbe)
        self.gesamt_brutto_lbl = QLabel("Gesamt Brutto: € 0,00")
        self.gesamt_brutto_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.gesamt_brutto_lbl.setStyleSheet(f"color: {COLOR_PRIMARY};")

        # Labels mit kleinen Abständen nebeneinander
        summe_layout.addWidget(self.gesamt_netto_lbl)
        summe_layout.addSpacing(20)
        summe_layout.addWidget(self.gesamt_mwst_lbl)
        summe_layout.addSpacing(20)
        summe_layout.addWidget(self.gesamt_brutto_lbl)
        content_layout.addWidget(summe_frame)

        # ── Notizen ─────────────────────────────────────────────────────────
        # Mehrzeiliges Textfeld für Anmerkungen zur Bestellung
        self.notizen_edit = QTextEdit()
        self.notizen_edit.setPlaceholderText("Anmerkungen zur Bestellung...")
        self.notizen_edit.setMaximumHeight(70)  # Kompakt halten
        col_n = QVBoxLayout(); col_n.setSpacing(4)
        col_n.addWidget(lbl("Notizen")); col_n.addWidget(self.notizen_edit)
        content_layout.addLayout(col_n)
        # Flexiblen Leerraum am Ende für optisches "Atmen"
        content_layout.addStretch()

        # Den scrollbaren Bereich dem Hauptlayout hinzufügen
        layout.addWidget(scroll)

        # --- Fußleiste mit Buttons ---
        btn_frame = QFrame()
        btn_frame.setObjectName("bestellung_btn_frame")
        # Heller Hintergrund und Trennlinie nach oben
        btn_frame.setStyleSheet(f"QFrame#bestellung_btn_frame {{ background: #f8f9fa; border-top: 1px solid {COLOR_BORDER}; }}")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(24, 14, 24, 14)
        btn_layout.addStretch()   # Buttons nach rechts schieben

        # "Abbrechen"-Button – schließt den Dialog ohne zu speichern
        abbruch_btn = QPushButton("Abbrechen")
        abbruch_btn.setObjectName("btn_icon")
        abbruch_btn.setFixedHeight(38)
        # reject() schließt den Dialog mit dem Ergebnis-Code "Rejected"
        abbruch_btn.clicked.connect(self.reject)

        # "Speichern"-Button – validiert und speichert die Bestellung
        speichern_btn = QPushButton("💾  Bestellung speichern")
        speichern_btn.setObjectName("btn_primary")
        speichern_btn.setFixedHeight(38)
        speichern_btn.clicked.connect(self._speichern)

        btn_layout.addWidget(abbruch_btn)
        btn_layout.addWidget(speichern_btn)
        layout.addWidget(btn_frame)

    def _update_lieferadresse(self):
        """
        Slot: Befüllt das Lieferadressfeld automatisch mit der Adresse
        des gerade ausgewählten Kunden.

        Durchsucht die lokale Kundenliste nach dem Kunden, dessen ID in
        der ComboBox ausgewählt wurde, und setzt die Adresse als
        "Straße, PLZ, Ort"-String in das Textfeld.
        """
        # Kunden-ID aus der ComboBox lesen (wurde als userData gespeichert)
        kid = self.kunde_combo.currentData()

        for k in self.kunden:
            if k["id"] == kid:
                # Adressbestandteile zusammenbauen; leere Teile werden
                # durch den List-Comprehension-Filter ausgefiltert
                teile = [k.get("strasse",""), k.get("plz",""), k.get("ort","")]
                addr = ", ".join(t for t in teile if t)  # Nur nicht-leere Teile verbinden
                self.liefer_edit.setText(addr)
                break   # Schleife beenden, da Kunde gefunden

    def _update_summe(self):
        """
        Berechnet die Gesamtsummen (Netto, MwSt., Brutto) und aktualisiert
        die drei Summen-Labels im Dialog.

        Berechnungsreihenfolge:
          1. Netto-Zwischensumme aus den Positionen holen
          2. Rabatt abziehen
          3. Versandkosten addieren
          4. MwSt. mit pauschal 19 % berechnen
          5. Brutto = Netto × 1,19
        """
        # Netto-Zwischensumme aller Positionen aus dem PositionenTabelle-Widget
        netto = self.positionen_widget.get_netto()

        # Rabatt als Dezimalzahl (z. B. 10 % → 0.10)
        rabatt = self.rabatt_spin.value() / 100
        versand = self.versand_spin.value()

        # Netto nach Abzug des Rabatts + Versandkosten
        netto_nach_rabatt = netto * (1 - rabatt) + versand

        # Approximierte MwSt (19 %) – vereinfachte Berechnung, da im echten
        # Betrieb verschiedene Steuersätze je Artikel gelten können
        mwst = netto_nach_rabatt * 0.19
        brutto = netto_nach_rabatt * 1.19  # Brutto = Netto + 19 % MwSt

        # Labels aktualisieren; :,.2f → Tausendertrennzeichen + 2 Dezimalstellen
        self.gesamt_netto_lbl.setText(f"Netto: € {netto_nach_rabatt:,.2f}")
        self.gesamt_mwst_lbl.setText(f"MwSt. (19%): € {mwst:,.2f}")
        self.gesamt_brutto_lbl.setText(f"Gesamt Brutto: € {brutto:,.2f}")

    def _fill_data(self):
        """
        Befüllt alle Formularfelder mit den Daten einer bestehenden
        Bestellung (wird nur im Bearbeitungs-Modus aufgerufen).

        Liest aus ``self.bestellung`` (dem übergeben Dict) alle relevanten
        Werte aus und setzt sie in die entsprechenden Eingabefelder.
        Lädt außerdem die Positionen der Bestellung aus der Datenbank.
        """
        b = self.bestellung   # Kürzel für bessere Lesbarkeit

        # Kunden in der ComboBox anhand der gespeicherten ID suchen und auswählen
        idx = self.kunde_combo.findData(b.get("kunden_id"))
        if idx >= 0:
            # findData() gibt -1 zurück, wenn nichts gefunden wurde;
            # daher nur setzen, wenn ein gültiger Index vorliegt
            self.kunde_combo.setCurrentIndex(idx)

        # Textfelder und ComboBoxen mit den Bestellungsdaten befüllen
        self.liefer_edit.setText(b.get("lieferadresse","") or "")
        self.status_combo.setCurrentText(b.get("status","Neu"))
        self.zahlung_combo.setCurrentText(b.get("zahlungsart","Rechnung"))
        self.zahlstatus_combo.setCurrentText(b.get("zahlungsstatus","Offen"))

        # Lieferdatum aus dem ISO-Format "YYYY-MM-DD" in ein QDate umwandeln
        d = b.get("lieferdatum","")
        if d:
            # str(d)[:10] extrahiert die ersten 10 Zeichen (nur das Datum,
            # ohne eventuelle Uhrzeit-Angaben)
            qd = QDate.fromString(str(d)[:10], "yyyy-MM-dd")
            if qd.isValid():   # Nur setzen, wenn das Datum korrekt geparst wurde
                self.liefer_datum.setDate(qd)

        # Numerische Felder; "or 0" fängt None-Werte aus der Datenbank ab
        self.rabatt_spin.setValue(float(b.get("rabatt_prozent",0) or 0))
        self.versand_spin.setValue(float(b.get("versandkosten",0) or 0))
        self.notizen_edit.setPlainText(b.get("notizen","") or "")

        # Positionen aus der Datenbank laden und in das Positions-Widget eintragen
        positionen = db.get_bestellpositionen(b["id"])
        self.positionen_widget.set_positionen(positionen)

        # Summe nach dem Laden der Positionen neu berechnen
        self._update_summe()

    def _speichern(self):
        """
        Validiert die Eingaben und speichert die Bestellung.

        Pflichtfeldprüfungen:
          - Es muss ein Kunde ausgewählt sein.
          - Es muss mindestens eine Bestellposition vorhanden sein.

        Bei bestandener Validierung werden die Ergebnisdaten in den
        Attributen ``result_data`` und ``result_positionen`` abgelegt
        und der Dialog mit ``accept()`` geschlossen. Der aufrufende
        Code kann dann per ``dlg.exec() == QDialog.DialogCode.Accepted``
        prüfen, ob gespeichert wurde.
        """
        # Kunden-ID aus der ComboBox lesen
        kid = self.kunde_combo.currentData()

        # Pflichtfeld: Kunde muss gewählt sein
        if not kid:
            QMessageBox.warning(self, "Pflichtfeld", "Bitte einen Kunden auswählen.")
            return   # Speichern abbrechen

        # Pflichtfeld: Mindestens eine Position muss vorhanden sein
        positionen = self.positionen_widget.get_positionen()
        if not positionen:
            QMessageBox.warning(self, "Keine Positionen",
                "Bitte mindestens einen Artikel zur Bestellung hinzufügen.")
            return   # Speichern abbrechen

        # Ergebnisdaten in einem Dict zusammenstellen, das an die Datenbank
        # übergeben wird. Bei neuen Bestellungen ist "id" None.
        self.result_data = {
            "id":             self.bestellung.get("id"),   # None bei neuer Bestellung
            "kunden_id":      kid,
            "lieferadresse":  self.liefer_edit.text().strip(),
            "status":         self.status_combo.currentText(),
            "zahlungsart":    self.zahlung_combo.currentText(),
            "zahlungsstatus": self.zahlstatus_combo.currentText(),
            # Datum im ISO-Format für die Datenbank speichern
            "lieferdatum":    self.liefer_datum.date().toString("yyyy-MM-dd"),
            "rabatt_prozent": self.rabatt_spin.value(),
            "versandkosten":  self.versand_spin.value(),
            "notizen":        self.notizen_edit.toPlainText().strip(),
        }
        # Positionen separat speichern
        self.result_positionen = positionen

        # Dialog erfolgreich schließen – signalisiert dem Aufrufer: "Speichern war OK"
        self.accept()


# ===========================================================================
# Klasse: BestellungDetailDialog
# ===========================================================================
class BestellungDetailDialog(QDialog):
    """
    Nur-Lesen-Ansicht einer vorhandenen Bestellung mit der Möglichkeit,
    Bestell- und Zahlungsstatus schnell zu aktualisieren.

    Das Signal ``status_geaendert`` wird ausgelöst, wenn der Benutzer
    den Status über den Dialog ändert – so kann die Übersichtsliste
    automatisch aktualisiert werden.
    """

    # Signal, das ausgelöst wird, wenn der Status der Bestellung geändert wurde
    status_geaendert = pyqtSignal()

    def __init__(self, parent, bestell_id: int):
        """
        Konstruktor des Detaildialogs.

        Parameter:
            parent      : Übergeordnetes Widget.
            bestell_id  : Datenbankschlüssel (ID) der anzuzeigenden Bestellung.
        """
        super().__init__(parent)
        # Die Bestellungs-ID für spätere Datenbankzugriffe merken
        self.bestell_id = bestell_id
        self.setWindowTitle("Bestelldetails")
        self.setMinimumWidth(640)
        self.setModal(True)   # Blockiert Interaktion mit dem Elternfenster
        self._setup_ui()

    def _setup_ui(self):
        """
        Erstellt die Detailansicht der Bestellung.

        Lädt zunächst alle nötigen Daten aus der Datenbank und baut dann
        folgende Struktur auf:
          1. Farbiger Header mit Bestellnummer und Status-Badge
          2. Scrollbarer Inhaltsbereich:
             a. Info-Kacheln (Kunde, Datum, Zahlungsart, Gesamtbetrag)
             b. Tabelle mit allen Bestellpositionen
             c. Schnell-Update-Leiste für Status und Zahlung
             d. Notizen (falls vorhanden)
          3. Fußleiste mit "Schließen"-Button
        """
        # Bestelldaten + Positionen aus der Datenbank laden
        b = db.get_bestellung(self.bestell_id)
        pos = db.get_bestellpositionen(self.bestell_id)

        # Sicherheitscheck: Bestellung könnte zwischenzeitlich gelöscht worden sein
        if not b:
            return

        self.setStyleSheet(f"QDialog {{ background: {COLOR_WHITE}; }}")
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Header mit Bestellnummer und farbigem Status-Badge ---
        # Statusfarbe aus dem Mapping in styles.py holen (Fallback: Grau)
        status_farbe = STATUS_FARBEN.get(b["status"], "#666")
        header = QFrame()
        header.setObjectName("detail_header")
        header.setStyleSheet(f"QFrame#detail_header {{ background: {COLOR_PRIMARY}; }}")
        header.setFixedHeight(70)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        # Titel: Bestellnummer
        title = QLabel(f"📦  Bestellung {b['bestellnummer']}")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_WHITE};")

        # Status-Badge: Kleines farbiges Label mit dem aktuellen Status
        status_badge = QLabel(b["status"])
        status_badge.setStyleSheet(f"""
            background: {status_farbe}; color: white;
            border-radius: 10px; padding: 4px 14px;
            font-size: 12px; font-weight: 600;
        """)

        h_layout.addWidget(title)
        h_layout.addStretch()       # Leeraum zwischen Titel und Badge
        h_layout.addWidget(status_badge)
        layout.addWidget(header)

        # --- Scrollbarer Inhaltsbereich ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(24, 20, 24, 20)
        c_layout.setSpacing(14)

        # --- Info-Kacheln als horizontale Leiste ---
        info_row = QHBoxLayout()
        info_row.setSpacing(12)

        def info_card(titel, wert, farbe="#fff"):
            """
            Erstellt eine Info-Kachel mit Titel und Wert.

            Parameter:
                titel (str): Überschrift der Kachel (klein, grau).
                wert  (str): Anzuzeigender Wert (groß, fett).
                farbe (str): Hintergrundfarbe als Hex-String (Standard: Weiß).
            Rückgabe:
                QFrame-Widget, das direkt ins Layout eingefügt werden kann.
            """
            f = QFrame()
            f.setStyleSheet(f"""
                background: {farbe};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 10px 14px;
            """)
            fl = QVBoxLayout(f)
            fl.setSpacing(2)
            # Kleines Titel-Label
            t = QLabel(titel)
            t.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_LIGHT}; font-weight: 600;")
            # Großes Wert-Label
            v = QLabel(str(wert))
            v.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            v.setStyleSheet(f"color: {COLOR_PRIMARY};")
            fl.addWidget(t); fl.addWidget(v)
            return f

        # Zahlungsstatus-Farbe aus dem Mapping holen
        z_farbe = ZAHLUNG_FARBEN.get(b["zahlungsstatus"], "#666")

        # Vier Info-Kacheln nebeneinander
        info_row.addWidget(info_card("Kunde", b["kunde_name"]))
        info_row.addWidget(info_card("Datum", str(b["bestelldatum"])[:10]))  # Nur das Datum, keine Uhrzeit
        info_row.addWidget(info_card("Zahlungsart", b["zahlungsart"]))
        info_row.addWidget(info_card("Gesamtbetrag", f"€ {b.get('gesamtbetrag_brutto', 0):.2f}"))
        c_layout.addLayout(info_row)

        # --- Positionstabelle ---
        pos_title = QLabel("Bestellpositionen")
        pos_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        pos_title.setStyleSheet(f"color: {COLOR_PRIMARY};")
        c_layout.addWidget(pos_title)

        # Tabelle direkt mit der Anzahl der Positionen anlegen (len(pos) Zeilen, 5 Spalten)
        pos_table = QTableWidget(len(pos), 5)
        pos_table.setHorizontalHeaderLabels(["Art.-Nr.", "Bezeichnung", "Menge", "Einzelpreis", "Gesamt Netto"])
        pos_table.verticalHeader().setVisible(False)
        pos_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Nur-Lesen
        pos_table.setShowGrid(False)
        pos_table.setAlternatingRowColors(True)
        pos_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Positionen in die Tabelle eintragen
        for row, p in enumerate(pos):
            pos_table.setItem(row, 0, QTableWidgetItem(p.get("artikelnummer","")))
            pos_table.setItem(row, 1, QTableWidgetItem(p.get("bezeichnung","")))
            # Menge + Einheit (z. B. "2 Stk.") zusammensetzen
            pos_table.setItem(row, 2, QTableWidgetItem(f"{p['menge']} {p.get('einheit','')}"))
            pos_table.setItem(row, 3, QTableWidgetItem(f"€ {p['einzelpreis']:.2f}"))
            # Zeilenbetrag = Menge × Einzelpreis
            pos_table.setItem(row, 4, QTableWidgetItem(f"€ {p['menge']*p['einzelpreis']:.2f}"))

        # Tabellenhöhe exakt an den Inhalt anpassen (46px pro Zeile + 40px Header)
        pos_table.setMaximumHeight(len(pos) * 46 + 40)
        c_layout.addWidget(pos_table)

        # --- Schnell-Update-Leiste für Status und Zahlung ---
        sq_frame = QFrame()
        sq_frame.setObjectName("sq_frame")
        sq_frame.setStyleSheet(f"QFrame#sq_frame {{ background: #f8f9fa; border-radius: 8px; }}")
        sq_layout = QHBoxLayout(sq_frame)
        sq_layout.setContentsMargins(16, 10, 16, 10)

        sq_layout.addWidget(QLabel("Status ändern:"))
        # ComboBox für den neuen Bestellstatus, vorausgewählt mit dem aktuellen Status
        self.new_status_combo = QComboBox()
        self.new_status_combo.addItems(["Neu","In Bearbeitung","Versendet","Geliefert","Storniert","Zurückgegeben"])
        self.new_status_combo.setCurrentText(b["status"])   # Aktuellen Status vorwählen
        sq_layout.addWidget(self.new_status_combo)

        sq_layout.addWidget(QLabel("Zahlung:"))
        # ComboBox für den neuen Zahlungsstatus
        self.new_zahl_combo = QComboBox()
        self.new_zahl_combo.addItems(["Offen","Teilbezahlt","Bezahlt","Erstattet"])
        self.new_zahl_combo.setCurrentText(b["zahlungsstatus"])   # Aktuellen Wert vorwählen
        sq_layout.addWidget(self.new_zahl_combo)

        # Button zum sofortigen Speichern der Statusänderung
        upd_btn = QPushButton("✓ Aktualisieren")
        upd_btn.setObjectName("btn_secondary")
        upd_btn.setFixedHeight(34)
        upd_btn.clicked.connect(self._update_status)
        sq_layout.addWidget(upd_btn)
        sq_layout.addStretch()
        c_layout.addWidget(sq_frame)

        # --- Notizen anzeigen (nur wenn vorhanden) ---
        if b.get("notizen"):
            notiz_lbl = QLabel(f"📝 {b['notizen']}")
            notiz_lbl.setWordWrap(True)   # Langer Text bricht automatisch um
            notiz_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px; font-style: italic;")
            c_layout.addWidget(notiz_lbl)

        c_layout.addStretch()   # Leeraum am Ende des Inhalts
        layout.addWidget(scroll)

        # --- Fußleiste mit "Schließen"-Button ---
        btn_frame = QFrame()
        btn_frame.setObjectName("detail_btn_frame")
        btn_frame.setStyleSheet(f"QFrame#detail_btn_frame {{ background: #f8f9fa; border-top: 1px solid {COLOR_BORDER}; }}")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(24, 12, 24, 12)
        btn_layout.addStretch()

        # "Schließen"-Button – accept() schließt den Dialog normal
        close_btn = QPushButton("Schließen")
        close_btn.setObjectName("btn_icon")
        close_btn.setFixedHeight(38)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addWidget(btn_frame)

    def _update_status(self):
        """
        Slot: Speichert den geänderten Bestell- und Zahlungsstatus in der
        Datenbank und informiert alle verbundenen Empfänger über das Signal.

        Liest die aktuell gewählten Werte aus den Status-ComboBoxen und
        übergibt sie an die Datenbankfunktion ``update_bestellstatus``.
        Anschließend wird eine kurze Erfolgsmeldung angezeigt.
        """
        # Datenbankfunktion aufrufen, die den Status der Bestellung aktualisiert
        db.update_bestellstatus(
            self.bestell_id,                       # Welche Bestellung?
            self.new_status_combo.currentText(),   # Neuer Bestellstatus
            self.new_zahl_combo.currentText()      # Neuer Zahlungsstatus
        )
        # Signal aussenden, damit z. B. die Bestellübersicht ihre Tabelle
        # aktualisiert und den neuen Status anzeigt
        self.status_geaendert.emit()

        # Bestätigungsdialog anzeigen
        QMessageBox.information(self, "Aktualisiert", "Status wurde erfolgreich aktualisiert.")


# ===========================================================================
# Klasse: BestellungenWidget
# ===========================================================================
class BestellungenWidget(QWidget):
    """
    Haupt-Widget der Bestellübersicht.

    Zeigt alle Bestellungen in einer Tabelle mit Such- und Filterfunktionen.
    Über die Aktions-Buttons in der letzten Spalte kann jede Bestellung
    angezeigt, bearbeitet oder gelöscht werden. Neue Bestellungen können
    über den "➕ Neue Bestellung"-Button angelegt werden.

    Das Signal ``bestellungen_geaendert`` wird ausgelöst, wenn sich der
    Datenbestand ändert (z. B. für Dashboard-Aktualisierungen).
    """

    # Signal für übergeordnete Widgets (z. B. Dashboard), die über
    # Änderungen an den Bestellungsdaten informiert werden müssen
    bestellungen_geaendert = pyqtSignal()

    def __init__(self, parent=None):
        """
        Konstruktor: Baut die UI auf und lädt sofort die aktuellen
        Bestellungsdaten aus der Datenbank.

        Parameter:
            parent: Übergeordnetes Widget (oder None).
        """
        super().__init__(parent)
        self._setup_ui()    # Oberfläche aufbauen
        self.refresh()      # Daten laden und Tabelle befüllen

    def _setup_ui(self):
        """
        Erstellt die Benutzeroberfläche des Bestellungs-Hauptwidgets.

        Aufbau:
          1. Toolbar: Suchfeld + Statusfilter + "Neue Bestellung"-Button
          2. Info-Zeile: Anzahl der Bestellungen + Gesamtumsatz
          3. Tabelle: Alle gefilterten Bestellungen mit Aktions-Buttons
        """
        # Hauptlayout mit Abständen zum Rand
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # --- Toolbar ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Suchfeld in einem gerundeten Rahmen
        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            background: white;
            border: 1.5px solid {COLOR_BORDER};
            border-radius: 20px;
        """)
        search_frame.setFixedHeight(40)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(14, 0, 14, 0)
        search_layout.addWidget(QLabel("🔍"))   # Lupen-Emoji als visuelles Icon

        # Einzeiliges Texteingabefeld für die Suche
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Bestellungen suchen (Nummer, Kunde...)")
        self.search_edit.setFrame(False)
        self.search_edit.setStyleSheet("background: transparent; border: none; font-size: 13px;")
        # Jede Texteingabe löst sofort eine Aktualisierung der Tabelle aus
        self.search_edit.textChanged.connect(self.refresh)
        search_layout.addWidget(self.search_edit)
        # Das Suchfeld soll den meisten Platz einnehmen (stretch=1)
        toolbar.addWidget(search_frame, stretch=1)

        # Status-Filterfeld: Zeigt nur Bestellungen mit dem gewählten Status
        self.status_filter = QComboBox()
        self.status_filter.setFixedHeight(40)
        self.status_filter.addItem("Alle Status", "")   # Kein Filter
        for s in ["Neu","In Bearbeitung","Versendet","Geliefert","Storniert","Zurückgegeben"]:
            # userData = der Status-String, der an die DB-Abfrage übergeben wird
            self.status_filter.addItem(s, s)
        # Filterwechsel → Tabelle neu laden
        self.status_filter.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.status_filter)

        # Button für neue Bestellung
        neu_btn = QPushButton("➕  Neue Bestellung")
        neu_btn.setObjectName("btn_primary")
        neu_btn.setFixedHeight(40)
        neu_btn.clicked.connect(self._neue_bestellung)
        toolbar.addWidget(neu_btn)

        # "CSV exportieren"-Button: speichert die aktuell gefilterte Bestellliste als CSV
        csv_btn = QPushButton("📥  CSV exportieren")
        csv_btn.setObjectName("btn_icon")  # Sekundäres Styling
        csv_btn.setFixedHeight(40)
        csv_btn.clicked.connect(self._exportiere_csv)
        toolbar.addWidget(csv_btn)

        layout.addLayout(toolbar)

        # --- Info-Zeile: zeigt Anzahl und Gesamtumsatz der gefilterten Bestellungen ---
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        layout.addWidget(self.info_lbl)

        # --- Haupttabelle ---
        self.table = QTableWidget()
        self.table.setColumnCount(10)   # 10 Spalten insgesamt
        self.table.setHorizontalHeaderLabels([
            "Best.-Nr.", "Datum", "Kunde", "Positionen",
            "Netto", "Brutto", "Status", "Zahlung", "Zahlstatus", "Aktionen"
        ])
        self.table.setAlternatingRowColors(True)
        # Ganze Zeile wird bei Klick markiert (nicht nur eine Zelle)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        # Benutzer darf keine Zellen direkt bearbeiten
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # Spaltenbreiten: Standard = gedehnt (Stretch)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Einzelne Spalten an den Inhalt anpassen
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        # Aktionsspalte (Index 9) bekommt eine feste Breite für die drei Buttons
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(9, 200)

        # Einheitliche Zeilenhöhe von 46 Pixeln
        self.table.verticalHeader().setDefaultSectionSize(46)

        # Doppelklick auf eine Zeile öffnet den Detaildialog
        self.table.doubleClicked.connect(self._detail_zeile)
        layout.addWidget(self.table)

    def refresh(self):
        """
        Lädt alle Bestellungen aus der Datenbank (gefiltert nach Suchtext
        und Statusfilter) und füllt die Tabelle neu.

        Wird aufgerufen:
          - Beim ersten Laden des Widgets
          - Nach jeder Änderung am Suchtext oder am Statusfilter
          - Nach dem Speichern, Bearbeiten oder Löschen einer Bestellung
        """
        # Aktuellen Suchtext und gewählten Statusfilter lesen
        suche = self.search_edit.text().strip()
        status = self.status_filter.currentData()

        # Bestellungen aus der Datenbank laden (DB-Funktion übernimmt die Filterung)
        bestellungen = db.get_alle_bestellungen(suche, status)

        # Gesamtumsatz aller angezeigten Bestellungen berechnen.
        # "or 0" verhindert Fehler, falls der Wert None ist (NULL in der DB).
        gesamt = sum(b.get("gesamtbetrag_brutto") or 0 for b in bestellungen)
        self.info_lbl.setText(
            f"{len(bestellungen)} Bestellung(en) · Gesamtumsatz: € {gesamt:,.2f}"
        )

        # Tabelle auf die richtige Zeilenanzahl setzen
        self.table.setRowCount(len(bestellungen))

        for row, b in enumerate(bestellungen):
            # --- Textspalten (0–5) ---
            items = [
                b.get("bestellnummer",""),
                str(b.get("bestelldatum",""))[:10],    # Nur Datum, keine Uhrzeit
                b.get("kunde_name",""),
                str(b.get("anzahl_positionen",0)),     # Anzahl der Positionen
                f"€ {b.get('gesamtbetrag_netto', 0):.2f}",
                f"€ {b.get('gesamtbetrag_brutto', 0):.2f}",
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text or "")
                # Die Bestellungs-ID als unsichtbares "UserRole"-Datum mitspeichern,
                # damit wir bei Klick auf die Zeile wissen, welche Bestellung gemeint ist
                item.setData(Qt.ItemDataRole.UserRole, b["id"])
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, col, item)

            # --- Spalte 6: Status-Badge ---
            # Statusfarbe aus dem Mapping holen (Fallback: Grau)
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
            # "22" am Ende des Farbcodes = Hex-Wert für ~13% Alpha-Transparenz
            # (halbtransparenter Hintergrund in der Statusfarbe)
            self.table.setCellWidget(row, 6, status_lbl)

            # --- Spalte 7: Zahlungsart ---
            za_lbl = QLabel(b.get("zahlungsart",""))
            za_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            za_lbl.setStyleSheet("font-size: 12px; color: " + COLOR_TEXT_LIGHT + "; margin: 6px 4px;")
            self.table.setCellWidget(row, 7, za_lbl)

            # --- Spalte 8: Zahlungsstatus-Badge ---
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

            # --- Spalte 9: Aktions-Buttons ---
            # Ein Container-Widget mit drei Buttons nebeneinander
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            # "Details"-Button öffnet den Detaildialog
            detail_btn = QPushButton("🔍 Details")
            detail_btn.setObjectName("btn_icon")
            detail_btn.setFixedHeight(30)
            # Bestellungs-ID als Property speichern, damit der Slot weiß,
            # welche Bestellung gemeint ist
            detail_btn.setProperty("bid", b["id"])
            detail_btn.clicked.connect(self._zeige_detail)

            # "Bearbeiten"-Button öffnet den Bearbeitungsdialog
            edit_btn = QPushButton("✏️")
            edit_btn.setObjectName("btn_icon")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setProperty("bid", b["id"])
            edit_btn.clicked.connect(self._bearbeite_bestellung)

            # "Löschen"-Button mit roter Hervorhebung (btn_danger)
            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("btn_danger")
            del_btn.setFixedSize(30, 30)
            del_btn.setProperty("bid", b["id"])
            del_btn.clicked.connect(self._loesche_bestellung)

            btn_layout.addWidget(detail_btn)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            # Den Button-Container als Widget in die Tabellenzelle einsetzen
            self.table.setCellWidget(row, 9, btn_widget)

    def _neue_bestellung(self):
        """
        Slot: Öffnet den BestellungDialog im "Neu"-Modus.

        Wenn der Benutzer den Dialog mit "Speichern" bestätigt
        (Rückgabe Accepted), wird die Bestellung in der Datenbank
        angelegt, die Tabelle aktualisiert und das Signal
        ``bestellungen_geaendert`` ausgelöst.
        """
        # Dialog ohne Bestellungs-Dict öffnen → Neu-Modus
        dlg = BestellungDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Bestellung mit Kopfdaten + Positionen in der Datenbank speichern
            db.speichere_bestellung(dlg.result_data, dlg.result_positionen)
            self.refresh()                      # Tabelle neu laden
            self.bestellungen_geaendert.emit()  # Dashboard informieren

    def _detail_zeile(self, index):
        """
        Slot: Wird ausgelöst, wenn der Benutzer per Doppelklick auf eine
        Tabellenzeile klickt.

        Liest die Bestellungs-ID aus der angeklickten Zelle (UserRole-Datum)
        und öffnet den Detaildialog für diese Bestellung.

        Parameter:
            index: QModelIndex – gibt Zeile und Spalte des Doppelklicks an.
        """
        # Zelle in Spalte 0 der angeklickten Zeile lesen
        item = self.table.item(index.row(), 0)
        if item:
            # Gespeicherte Bestellungs-ID aus dem UserRole-Datum holen
            bid = item.data(Qt.ItemDataRole.UserRole)
            dlg = BestellungDetailDialog(self, bid)
            # Wenn der Status im Dialog geändert wird, Tabelle aktualisieren
            dlg.status_geaendert.connect(self.refresh)
            dlg.exec()

    def _zeige_detail(self):
        """
        Slot: Wird aufgerufen, wenn der "Details"-Button einer Zeile
        geklickt wird.

        Liest die Bestellungs-ID aus der "bid"-Property des Buttons und
        öffnet den Detaildialog.
        """
        # Den Button, der das Signal ausgelöst hat, abrufen und seine Property lesen
        bid = self.sender().property("bid")
        dlg = BestellungDetailDialog(self, bid)
        # Statusänderung im Dialog → Tabelle UND Dashboard aktualisieren
        dlg.status_geaendert.connect(self.refresh)
        dlg.status_geaendert.connect(self.bestellungen_geaendert)
        dlg.exec()

    def _bearbeite_bestellung(self):
        """
        Slot: Öffnet den BestellungDialog im "Bearbeiten"-Modus für die
        Bestellung, deren "Bearbeiten"-Button geklickt wurde.

        Lädt zunächst die vollständigen Bestellungsdaten aus der Datenbank
        und übergibt sie an den Dialog. Bei Bestätigung werden die
        geänderten Daten gespeichert.
        """
        # Bestellungs-ID aus der Button-Property lesen
        bid = self.sender().property("bid")
        # Vollständige Bestellungsdaten aus der Datenbank holen
        b = db.get_bestellung(bid)
        if b:
            # Dialog im Bearbeitungs-Modus öffnen (mit vorausgefüllten Daten)
            dlg = BestellungDialog(self, b)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                # Geänderte Daten in der Datenbank aktualisieren
                db.speichere_bestellung(dlg.result_data, dlg.result_positionen)
                self.refresh()
                self.bestellungen_geaendert.emit()

    def _loesche_bestellung(self):
        """
        Slot: Löscht eine Bestellung nach Bestätigung durch den Benutzer.

        Zeigt zunächst einen Bestätigungsdialog mit dem Namen der Bestellung
        an. Nur wenn der Benutzer mit "Ja" bestätigt, wird die Bestellung
        tatsächlich aus der Datenbank gelöscht.
        """
        # Bestellungs-ID aus der Button-Property lesen
        bid = self.sender().property("bid")
        # Bestellungsdaten laden, um im Dialog den Namen anzeigen zu können
        b = db.get_bestellung(bid)
        if not b:
            return   # Bestellung existiert nicht mehr – nichts tun

        # Bestätigungsdialog mit "Ja"/"Nein"-Auswahl
        reply = QMessageBox.question(
            self, "Bestellung löschen",
            f"Bestellung <b>{b['bestellnummer']}</b> von <b>{b['kunde_name']}</b> löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No   # Standard-Auswahl: Nein (Sicherheit)
        )

        # Nur löschen, wenn der Benutzer explizit "Ja" geklickt hat
        if reply == QMessageBox.StandardButton.Yes:
            db.loesche_bestellung(bid)          # Datenbankzeile entfernen
            self.refresh()                       # Tabelle neu laden
            self.bestellungen_geaendert.emit()   # Dashboard informieren

    def _exportiere_csv(self):
        """
        Exportiert alle aktuell angezeigten Bestellungen als CSV-Datei.

        Berücksichtigt werden der aktuelle Suchtext und der gewählte
        Statusfilter – es werden genau die Bestellungen exportiert, die
        gerade in der Tabelle sichtbar sind.

        Die Datei wird mit Semikolon als Trennzeichen und UTF-8-BOM
        kodiert gespeichert, damit Excel Umlaute korrekt darstellt.
        """
        # Datei-Speicherdialog öffnen
        pfad, _ = QFileDialog.getSaveFileName(
            self,
            "Bestellungen exportieren",
            "bestellungen_export.csv",
            "CSV-Dateien (*.csv)"
        )
        if not pfad:
            return  # Abbrechen gedrückt – nichts tun

        # Aktuelle Filter aus der Toolbar lesen (gleiche Logik wie in refresh())
        suche = self.search_edit.text().strip()
        status = self.status_filter.currentData()

        # Bestellungen mit denselben Filtern wie in der Tabelle laden
        bestellungen = db.get_alle_bestellungen(suche, status)

        try:
            with open(pfad, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")

                # Kopfzeile mit allen Spaltennamen schreiben
                writer.writerow([
                    "Bestellnummer", "Datum", "Kunde", "Anzahl Positionen",
                    "Netto (€)", "Brutto (€)", "Status",
                    "Zahlungsart", "Zahlungsstatus"
                ])

                # Eine Zeile pro Bestellung schreiben
                for b in bestellungen:
                    writer.writerow([
                        b.get("bestellnummer", ""),
                        # Datum auf die ersten 10 Zeichen kürzen (ohne Uhrzeit)
                        str(b.get("bestelldatum", ""))[:10],
                        b.get("kunde_name", ""),
                        b.get("anzahl_positionen", 0),
                        f"{b.get('gesamtbetrag_netto', 0):.2f}",
                        f"{b.get('gesamtbetrag_brutto', 0):.2f}",
                        b.get("status", ""),
                        b.get("zahlungsart", ""),
                        b.get("zahlungsstatus", ""),
                    ])

            # Erfolgsmeldung mit Anzahl der exportierten Datensätze anzeigen
            QMessageBox.information(
                self, "Export erfolgreich",
                f"{len(bestellungen)} Bestellung(en) wurden exportiert nach:\n{pfad}"
            )

        except Exception as fehler:
            # Fehlermeldung bei Schreibproblemen (z. B. fehlende Berechtigungen)
            QMessageBox.warning(self, "Fehler beim Export", str(fehler))
