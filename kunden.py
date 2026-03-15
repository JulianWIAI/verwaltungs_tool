"""
Radsport Koch GmbH – Kundenverwaltung

Dieses Modul stellt die grafische Benutzeroberfläche (GUI) für die
Kundenverwaltung bereit. Es enthält zwei Klassen:

  - KundeDialog: Ein modales Dialogfenster zum Anlegen und Bearbeiten
    eines einzelnen Kunden.
  - KundenWidget: Das Haupt-Widget der Registerkarte "Kunden", das eine
    durchsuchbare Tabelle aller Kunden anzeigt und die Schaltflächen zum
    Anlegen, Bearbeiten und Löschen verwaltet.

Beide Klassen nutzen das Modul `database` (db) für alle
Datenbankoperationen sowie das Modul `styles` für einheitliche Farben.
"""

# --- Importe aus PyQt6 ---
# QWidget          – Basisklasse für alle GUI-Elemente
# QVBoxLayout      – Ordnet Widgets senkrecht (vertikal) an
# QHBoxLayout      – Ordnet Widgets waagerecht (horizontal) an
# QLabel           – Zeigt Text oder Bilder an (nicht editierbar)
# QPushButton      – Klickbare Schaltfläche
# QTableWidget     – Tabelle mit Zeilen und Spalten
# QTableWidgetItem – Eine einzelne Zelle innerhalb der Tabelle
# QHeaderView      – Kontrolliert das Verhalten der Spalten-/Zeilenköpfe
# QFrame           – Container-Widget mit optionalem Rahmen
# QLineEdit        – Einzeiliges Texteingabefeld
# QDialog          – Basisklasse für Dialogfenster (mit eigenem Event-Loop)
# QFormLayout      – Spezielles Layout für Label-/Eingabefeld-Paare
# QTextEdit        – Mehrzeiliges Texteingabefeld
# QComboBox        – Auswahlmenü (Dropdown)
# QMessageBox      – Vorgefertigte Nachrichtenboxen (Hinweis, Frage, Fehler)
# QSizePolicy      – Legt fest, wie ein Widget seinen Platz ausfüllt
# QDateEdit        – Eingabefeld speziell für Datumsangaben
# QAbstractItemView– Basisklasse für alle Ansichts-Widgets (definiert Konstanten)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QDialog, QFormLayout, QTextEdit, QComboBox,
    QMessageBox, QSizePolicy, QDateEdit, QAbstractItemView
)

# Qt        – Enthält globale Konstanten (z.B. Ausrichtungsflags)
# QDate     – Klasse für Datumsoperationen (ohne Uhrzeit)
# pyqtSignal– Ermöglicht das Definieren eigener Signale für die
#             Signal-Slot-Kommunikation zwischen Widgets
from PyQt6.QtCore import Qt, QDate, pyqtSignal

# QFont  – Schriftart und -größe festlegen
# QIcon  – Symbole für Schaltflächen oder Fenster
# QColor – Farben als RGB-Wert oder Farbnamen
from PyQt6.QtGui import QFont, QIcon, QColor

# Eigenes Datenbankmodul – enthält alle SQLite-Zugriffsfunktionen
import database as db

# Farbkonstanten aus dem zentralen Styles-Modul importieren,
# damit das gesamte Programm ein einheitliches Erscheinungsbild hat
from styles import (
    COLOR_PRIMARY,      # Hauptfarbe (z.B. Blau für Header und primäre Buttons)
    COLOR_SECONDARY,    # Sekundärfarbe
    COLOR_SUCCESS,      # Grün für Erfolgsmeldungen
    COLOR_DANGER,       # Rot für Fehlermeldungen und Löschen-Buttons
    COLOR_WHITE,        # Weißer Hintergrund
    COLOR_BG,           # Allgemeine Hintergrundfarbe der Anwendung
    COLOR_TEXT_LIGHT,   # Helle Textfarbe für Beschriftungen / Hinweise
    COLOR_BORDER,       # Farbe für Rahmen und Trennlinien
    COLOR_WARNING       # Gelb/Orange für Warnungen
)


# =============================================================================
# Klasse KundeDialog
# =============================================================================

class KundeDialog(QDialog):
    """
    Modales Dialogfenster zum Anlegen eines neuen Kunden oder zum
    Bearbeiten eines bestehenden Kunden.

    Ein "modaler" Dialog blockiert alle anderen Fenster der Anwendung,
    solange er geöffnet ist – der Nutzer muss erst speichern oder
    abbrechen, bevor er weiterarbeiten kann.

    Parameter:
        parent (QWidget, optional): Das übergeordnete Eltern-Widget.
        kunde  (dict, optional):    Wörterbuch mit den vorhandenen
                                    Kundendaten. Ist None, wird ein
                                    leeres Formular für einen neuen
                                    Kunden geöffnet.

    Attribute:
        kunde       (dict):  Die übergeben Kundendaten (oder {}).
        result_data (dict):  Nach dem Speichern enthält dieses Attribut
                             alle Formulardaten als Wörterbuch.
    """

    def __init__(self, parent=None, kunde: dict = None):
        """
        Konstruktor des Dialogs.

        Ruft den Konstruktor der Elternklasse QDialog auf, speichert
        die Kundendaten, setzt Fenstertitel und Mindestbreite, und
        baut anschließend die Benutzeroberfläche auf.

        Args:
            parent (QWidget, optional): Übergeordnetes Widget.
            kunde  (dict, optional):    Bestehende Kundendaten zum
                                        Bearbeiten. None = neuer Kunde.
        """
        # Elternklasse initialisieren – das ist bei jeder Qt-Klasse Pflicht
        super().__init__(parent)

        # Kundendaten speichern; falls None übergeben wurde, leeres Dict verwenden
        # Der Ausdruck "kunde or {}" ergibt {}, wenn kunde den Wert None hat
        self.kunde = kunde or {}

        # Fenstertitel je nach Modus: Bearbeiten oder Neu anlegen
        self.setWindowTitle("Kunde bearbeiten" if kunde else "Neuen Kunden anlegen")

        # Mindestbreite des Fensters in Pixeln festlegen
        self.setMinimumWidth(520)

        # Dialog als modal markieren: blockiert das Elternfenster
        self.setModal(True)

        # Alle Eingabefelder und das Layout aufbauen
        self._setup_ui()

        # Wenn ein bestehender Kunde übergeben wurde, Felder mit seinen Daten füllen
        if kunde:
            self._fill_data()

    def _setup_ui(self):
        """
        Erstellt und konfiguriert alle Widgets des Dialogfensters.

        Der Dialog ist in drei Bereiche aufgeteilt:
          1. Header  – farbiger Titelbalken oben
          2. Formular – alle Eingabefelder (Name, Kontakt, Adresse, etc.)
          3. Buttons  – "Abbrechen" und "Speichern" am unteren Rand

        Diese Methode wird nur einmal beim Erstellen des Dialogs
        aufgerufen.
        """
        # Hintergrundfarbe des gesamten Dialogs auf Weiß setzen
        # Die geschweifte Klammer in f"QDialog {{ ... }}" muss verdoppelt werden,
        # damit Python sie nicht als Formatierungszeichen interpretiert
        self.setStyleSheet(f"QDialog {{ background: {COLOR_WHITE}; }}")

        # Haupt-Layout: alle drei Bereiche untereinander anordnen
        layout = QVBoxLayout(self)
        layout.setSpacing(0)          # Kein Abstand zwischen den Bereichen
        layout.setContentsMargins(0, 0, 0, 0)  # Kein Außenabstand

        # --- Bereich 1: Header ---
        header = QFrame()
        # Primärfarbe als Hintergrund; border-radius: 0 = keine abgerundeten Ecken
        header.setStyleSheet(f"background: {COLOR_PRIMARY}; border-radius: 0;")
        header.setFixedHeight(64)     # Feste Höhe von 64 Pixeln

        # Horizontales Layout innerhalb des Headers (für das Titel-Label)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)  # Links/Rechts je 24 px Abstand

        # Titeltext mit Emoji-Icon; Inhalt hängt davon ab, ob ein Kunde bearbeitet wird
        title = QLabel("👤  " + ("Kunde bearbeiten" if self.kunde else "Neuen Kunden anlegen"))
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))  # Schriftart und -größe
        title.setStyleSheet(f"color: {COLOR_WHITE};")             # Weißer Text
        h_layout.addWidget(title)

        # Header zum Haupt-Layout hinzufügen
        layout.addWidget(header)

        # --- Bereich 2: Formular ---
        form_widget = QWidget()
        form_widget.setObjectName("kunde_form")  # Name für CSS-Selektor (s.u.)
        # Nur das Widget mit diesem ObjectName bekommt weißen Hintergrund
        form_widget.setStyleSheet(f"QWidget#kunde_form {{ background: {COLOR_WHITE}; }}")

        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(24, 20, 24, 20)  # Innenabstand: oben/unten 20 px
        form_layout.setSpacing(14)                       # Abstand zwischen den Zeilen

        # --- Hilfsfunktion: eine Formularzeile erstellen ---
        def make_row(label_text, widget):
            """
            Erstellt eine vertikale Gruppe aus einem Beschriftungs-Label
            (klein, in Großbuchstaben) und dem dazugehörigen Eingabe-Widget.

            Args:
                label_text (str):    Text der Beschriftung.
                widget (QWidget):    Das Eingabe-Widget (z.B. QLineEdit).

            Returns:
                QVBoxLayout: Das fertige Layout mit Label + Widget.
            """
            row = QVBoxLayout()

            # Beschriftungs-Label (klein, fett, in Großbuchstaben)
            lbl = QLabel(label_text)
            lbl.setStyleSheet(
                f"font-size: 11px; font-weight: 600; color: {COLOR_TEXT_LIGHT}; "
                "text-transform: uppercase;"
            )
            row.addWidget(lbl)
            row.addWidget(widget)   # Eingabefeld darunter einfügen
            return row

        # --- Formularzeile: Vor- und Nachname ---
        # name_row ist ein horizontales Layout: Vorname links, Nachname rechts
        name_row = QHBoxLayout()
        name_row.setSpacing(12)   # 12 Pixel Abstand zwischen den beiden Feldern

        # Eingabefelder für Vor- und Nachname erstellen
        self.vorname_edit = QLineEdit()
        self.vorname_edit.setPlaceholderText("Vorname *")   # Grauer Hinweistext
        self.nachname_edit = QLineEdit()
        self.nachname_edit.setPlaceholderText("Nachname *")

        # Beide Felder mit Beschriftung als Spalten in die Zeile einfügen
        name_row.addLayout(make_row("Vorname *", self.vorname_edit))
        name_row.addLayout(make_row("Nachname *", self.nachname_edit))
        form_layout.addLayout(name_row)

        # --- Formularzeile: Kontaktdaten ---
        kontakt_row = QHBoxLayout()
        kontakt_row.setSpacing(12)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@beispiel.de")
        self.telefon_edit = QLineEdit()
        self.telefon_edit.setPlaceholderText("0911 123456")

        kontakt_row.addLayout(make_row("E-Mail", self.email_edit))
        kontakt_row.addLayout(make_row("Telefon", self.telefon_edit))
        form_layout.addLayout(kontakt_row)

        # --- Formularzeile: Straße ---
        # Straße bekommt eine eigene, volle Breite
        self.strasse_edit = QLineEdit()
        self.strasse_edit.setPlaceholderText("Straße und Hausnummer")
        form_layout.addLayout(make_row("Straße", self.strasse_edit))

        # --- Formularzeile: PLZ, Ort, Land ---
        adresse_row = QHBoxLayout()
        adresse_row.setSpacing(12)

        self.plz_edit = QLineEdit()
        self.plz_edit.setPlaceholderText("PLZ")
        self.plz_edit.setMaximumWidth(100)   # PLZ-Feld ist bewusst schmal

        self.ort_edit = QLineEdit()
        self.ort_edit.setPlaceholderText("Ort")

        # Dropdown für Länderauswahl
        self.land_combo = QComboBox()
        self.land_combo.addItems(["Deutschland", "Österreich", "Schweiz", "Anderes"])
        self.land_combo.setMaximumWidth(140)

        adresse_row.addLayout(make_row("PLZ", self.plz_edit))
        adresse_row.addLayout(make_row("Ort", self.ort_edit))
        adresse_row.addLayout(make_row("Land", self.land_combo))
        form_layout.addLayout(adresse_row)

        # --- Formularzeile: Geburtsdatum ---
        self.geb_edit = QDateEdit()
        self.geb_edit.setDisplayFormat("dd.MM.yyyy")  # Anzeige im deutschen Format
        self.geb_edit.setCalendarPopup(True)           # Kalender-Popup aktivieren
        self.geb_edit.setDate(QDate(1990, 1, 1))       # Standardwert: 01.01.1990
        self.geb_edit.setMaximumWidth(160)
        form_layout.addLayout(make_row("Geburtsdatum", self.geb_edit))

        # --- Formularzeile: Notizen ---
        # QTextEdit erlaubt mehrzeiligen Text (im Gegensatz zu QLineEdit)
        self.notizen_edit = QTextEdit()
        self.notizen_edit.setPlaceholderText("Interne Notizen zum Kunden...")
        self.notizen_edit.setMaximumHeight(80)  # Höhe begrenzen, damit der Dialog kompakt bleibt
        form_layout.addLayout(make_row("Notizen", self.notizen_edit))

        # Fertig aufgebautes Formular-Widget dem Haupt-Layout hinzufügen
        layout.addWidget(form_widget)

        # --- Bereich 3: Schaltflächen (Abbrechen / Speichern) ---
        btn_frame = QFrame()
        btn_frame.setObjectName("kunde_btn_frame")
        # Hellgrauer Hintergrund mit einer Trennlinie oben
        btn_frame.setStyleSheet(
            f"QFrame#kunde_btn_frame {{ background: #f8f9fa; border-top: 1px solid {COLOR_BORDER}; }}"
        )
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(24, 14, 24, 14)
        btn_layout.setSpacing(10)
        btn_layout.addStretch()   # Leerer Platzhalter schiebt Buttons nach rechts

        # "Abbrechen"-Button: schließt den Dialog ohne zu speichern (reject())
        abbruch_btn = QPushButton("Abbrechen")
        abbruch_btn.setObjectName("btn_icon")  # CSS-Klasse für das Styling
        abbruch_btn.setFixedHeight(38)
        # reject() ist eine eingebaute QDialog-Methode – setzt das Ergebnis auf "Rejected"
        abbruch_btn.clicked.connect(self.reject)

        # "Speichern"-Button: ruft die eigene Methode _speichern() auf
        speichern_btn = QPushButton("💾  Speichern")
        speichern_btn.setObjectName("btn_primary")
        speichern_btn.setFixedHeight(38)
        speichern_btn.clicked.connect(self._speichern)

        btn_layout.addWidget(abbruch_btn)
        btn_layout.addWidget(speichern_btn)
        layout.addWidget(btn_frame)

    def _fill_data(self):
        """
        Füllt alle Eingabefelder mit den Daten des zu bearbeitenden Kunden.

        Diese Methode wird nur aufgerufen, wenn beim Erstellen des Dialogs
        ein bestehendes Kunden-Wörterbuch übergeben wurde. Sie liest die
        Werte mit .get() aus dem Dict – .get() liefert "" statt einem
        Fehler, wenn ein Schlüssel fehlt.
        """
        # Textfelder direkt mit den gespeicherten Werten befüllen
        self.vorname_edit.setText(self.kunde.get("vorname", ""))
        self.nachname_edit.setText(self.kunde.get("nachname", ""))
        self.email_edit.setText(self.kunde.get("email", ""))
        self.telefon_edit.setText(self.kunde.get("telefon", ""))
        self.strasse_edit.setText(self.kunde.get("strasse", ""))
        self.plz_edit.setText(self.kunde.get("plz", ""))
        self.ort_edit.setText(self.kunde.get("ort", ""))

        # Land im Dropdown suchen und auswählen
        # findText() gibt den Index des Eintrags zurück, -1 wenn nicht gefunden
        idx = self.land_combo.findText(self.kunde.get("land", "Deutschland"))
        if idx >= 0:
            self.land_combo.setCurrentIndex(idx)  # Gefundenen Eintrag auswählen

        # Geburtsdatum aus dem Format "yyyy-MM-dd" (Datenbankformat) umwandeln
        geb = self.kunde.get("geburtsdatum", "")
        if geb:
            try:
                # QDate.fromString() wandelt den String in ein QDate-Objekt um
                d = QDate.fromString(geb, "yyyy-MM-dd")
                if d.isValid():   # Nur setzen, wenn das Datum gültig ist
                    self.geb_edit.setDate(d)
            except Exception:
                # Bei einem unerwarteten Fehler (z.B. korrupte Daten) einfach
                # das Standarddatum beibehalten, statt abzustürzen
                pass

        # Mehrzeiliges Notizfeld mit toPlainText setzen (kein HTML)
        self.notizen_edit.setPlainText(self.kunde.get("notizen", ""))

    def _speichern(self):
        """
        Liest alle Eingabefelder aus, prüft Pflichtfelder und speichert
        die Daten in self.result_data, bevor der Dialog mit accept()
        geschlossen wird.

        Pflichtfelder: Vorname und Nachname. Fehlen diese, erscheint eine
        Warnmeldung und der Dialog bleibt geöffnet.

        Nach dem Aufruf von accept() gibt dlg.exec() den Wert
        QDialog.DialogCode.Accepted zurück, sodass der aufrufende Code
        weiß, dass gespeichert wurde.
        """
        # Eingaben einlesen; .strip() entfernt führende/nachfolgende Leerzeichen
        vorname = self.vorname_edit.text().strip()
        nachname = self.nachname_edit.text().strip()

        # Pflichtfeldprüfung: beide Felder müssen einen Wert enthalten
        if not vorname or not nachname:
            # Warnfenster anzeigen und die Methode vorzeitig beenden (return)
            QMessageBox.warning(self, "Pflichtfelder", "Bitte Vor- und Nachname eingeben.")
            return  # Dialog bleibt offen, kein Speichern

        # Alle Formulardaten in einem Wörterbuch zusammenstellen
        # Dieses Dict wird anschließend an die Datenbankfunktion übergeben
        self.result_data = {
            "id":          self.kunde.get("id"),          # None bei neuem Kunden
            "vorname":     vorname,
            "nachname":    nachname,
            "email":       self.email_edit.text().strip(),
            "telefon":     self.telefon_edit.text().strip(),
            "strasse":     self.strasse_edit.text().strip(),
            "plz":         self.plz_edit.text().strip(),
            "ort":         self.ort_edit.text().strip(),
            "land":        self.land_combo.currentText(),  # Aktuell gewählter Eintrag
            # Datum zurück ins Datenbankformat "yyyy-MM-dd" umwandeln
            "geburtsdatum": self.geb_edit.date().toString("yyyy-MM-dd"),
            "notizen":     self.notizen_edit.toPlainText().strip(),
        }

        # Dialog erfolgreich schließen – signalisiert dem Aufrufer: "Speichern gedrückt"
        self.accept()


# =============================================================================
# Klasse KundenWidget
# =============================================================================

class KundenWidget(QWidget):
    """
    Haupt-Widget der Registerkarte "Kunden".

    Zeigt eine durchsuchbare und filterbare Tabelle aller Kunden an.
    Ermöglicht das Anlegen neuer Kunden sowie das Bearbeiten und Löschen
    bestehender Kunden über Aktionsschaltflächen in der letzten Spalte.

    Signale:
        kunden_geaendert: Wird ausgelöst, nachdem ein Kunde angelegt,
                          bearbeitet oder gelöscht wurde. Andere Teile
                          der Anwendung (z.B. die Bestellübersicht) können
                          dieses Signal empfangen und sich aktualisieren.
    """

    # Signal definieren: kein Rückgabewert (leere Klammer)
    # pyqtSignal() erstellt ein neues, anwendungsspezifisches Signal
    kunden_geaendert = pyqtSignal()

    def __init__(self, parent=None):
        """
        Konstruktor des KundenWidget.

        Baut die Oberfläche auf und lädt beim Start sofort alle
        vorhandenen Kunden aus der Datenbank.

        Args:
            parent (QWidget, optional): Übergeordnetes Widget.
        """
        # Elternklasse QWidget initialisieren
        super().__init__(parent)

        # Benutzeroberfläche aufbauen
        self._setup_ui()

        # Tabelle mit aktuellen Daten aus der Datenbank befüllen
        self.refresh()

    def _setup_ui(self):
        """
        Erstellt das Layout des KundenWidget:

          1. Toolbar  – Suchleiste + "Neuer Kunde"-Button
          2. Info-Zeile – zeigt die Anzahl der gefundenen Kunden an
          3. Tabelle  – zeigt alle Kunden mit Aktionsbuttons
        """
        # Haupt-Layout: alle drei Bereiche senkrecht anordnen
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)  # Außenabstand (links, oben, rechts, unten)
        layout.setSpacing(16)                       # Abstand zwischen den Bereichen

        # --- Toolbar ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Suchleiste in einem abgerundeten Rahmen ("Pill-Design")
        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            background: white;
            border: 1.5px solid {COLOR_BORDER};
            border-radius: 20px;
        """)
        search_frame.setFixedHeight(40)

        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(14, 0, 14, 0)

        # Lupe als dekorativer Text-Label (kein echtes Icon)
        search_icon = QLabel("🔍")

        # Einzeiliges Texteingabefeld für den Suchbegriff
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Kunden suchen (Name, E-Mail, Ort...)")
        self.search_edit.setFrame(False)   # Keinen eigenen Rahmen zeichnen
        self.search_edit.setStyleSheet("background: transparent; border: none; font-size: 13px;")
        # Signal: bei jeder Texteingabe (auch einzelnen Buchstaben) sofort suchen
        # textChanged ist ein Qt-Signal, refresh() ist der verbundene Slot
        self.search_edit.textChanged.connect(self.refresh)

        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_edit)
        # stretch=1: Suchleiste nimmt den gesamten verfügbaren horizontalen Platz ein
        toolbar.addWidget(search_frame, stretch=1)

        # "Neuer Kunde"-Button
        self.neu_btn = QPushButton("➕  Neuer Kunde")
        self.neu_btn.setObjectName("btn_primary")  # CSS-Klasse für grüne/blaue Primärfarbe
        self.neu_btn.setFixedHeight(40)
        self.neu_btn.clicked.connect(self._neuer_kunde)
        toolbar.addWidget(self.neu_btn)

        layout.addLayout(toolbar)

        # --- Info-Zeile ---
        # Zeigt z.B. "12 Kunde(n) gefunden" an und wird in refresh() aktualisiert
        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
        layout.addWidget(self.info_lbl)

        # --- Tabelle ---
        self.table = QTableWidget()
        self.table.setColumnCount(9)   # 9 Spalten: 8 Datenspalten + 1 Aktionsspalte

        # Spaltenköpfe festlegen
        self.table.setHorizontalHeaderLabels([
            "Nr.", "Vorname", "Nachname", "E-Mail", "Telefon",
            "PLZ", "Ort", "Erstellt", "Aktionen"
        ])

        # Jede zweite Zeile bekommt eine leicht andere Hintergrundfarbe (Zebramuster)
        self.table.setAlternatingRowColors(True)

        # Beim Klicken wird immer die gesamte Zeile markiert, nicht nur eine Zelle
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # Tabellenzellen können nicht direkt bearbeitet werden (nur über den Dialog)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Zeilennummern am linken Rand ausblenden (wirkt aufgeräumter)
        self.table.verticalHeader().setVisible(False)

        # Gitternetzlinien ausblenden für ein modernes Erscheinungsbild
        self.table.setShowGrid(False)

        # Alle Spalten strecken sich gleichmäßig auf die verfügbare Breite
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Spalte 0 (Nr.) passt sich dem Inhalt an statt sich zu strecken
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        # Spalte 8 (Aktionen) bekommt eine feste Breite
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 160)

        # Zeilenhöhe festlegen: erste Zeile 48 px, alle weiteren 46 px
        self.table.setRowHeight(0, 48)
        self.table.verticalHeader().setDefaultSectionSize(46)

        # Doppelklick auf eine Zeile öffnet den Bearbeiten-Dialog
        self.table.doubleClicked.connect(self._bearbeite_zeile)

        layout.addWidget(self.table)

    def refresh(self):
        """
        Lädt alle Kunden aus der Datenbank und befüllt die Tabelle neu.

        Berücksichtigt dabei den aktuellen Text im Suchfeld – die
        Datenbankfunktion get_alle_kunden() filtert serverseitig nach
        Name, E-Mail und Ort.

        Diese Methode wird aufgerufen:
          - beim ersten Laden des Widgets (im Konstruktor),
          - bei jeder Texteingabe in die Suchleiste (Signal textChanged),
          - nach dem Anlegen, Bearbeiten oder Löschen eines Kunden.
        """
        # Aktuellen Suchbegriff aus dem Eingabefeld holen
        suche = self.search_edit.text().strip()

        # Alle passenden Kunden aus der Datenbank abrufen
        # Die Funktion gibt eine Liste von Wörterbüchern zurück
        kunden = db.get_alle_kunden(suche)

        # Anzahl der Ergebnisse in der Info-Zeile anzeigen
        self.info_lbl.setText(f"{len(kunden)} Kunde(n) gefunden")

        # Anzahl der Tabellenzeilen an die Anzahl der gefundenen Kunden anpassen
        self.table.setRowCount(len(kunden))

        # Jede Zeile mit den Kundendaten befüllen
        for row, k in enumerate(kunden):
            # Die 8 anzuzeigenden Datenwerte als Liste vorbereiten
            items = [
                k.get("kundennummer", ""),
                k.get("vorname", ""),
                k.get("nachname", ""),
                k.get("email", ""),
                k.get("telefon", ""),
                k.get("plz", ""),
                k.get("ort", ""),
                # Datum auf die ersten 10 Zeichen kürzen ("2024-01-15T..." -> "2024-01-15")
                (k.get("erstellt_am", "") or "")[:10],
            ]

            # Jede Spalte in der aktuellen Zeile befüllen
            for col, text in enumerate(items):
                item = QTableWidgetItem(text or "")

                # Die Datenbank-ID unsichtbar in der Zelle speichern (UserRole)
                # Dadurch kann man später die ID aus einer Zelle auslesen,
                # ohne die ID als sichtbaren Text in der Tabelle anzeigen zu müssen
                item.setData(Qt.ItemDataRole.UserRole, k["id"])

                # Text vertikal zentriert und links ausgerichtet
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, col, item)

            # --- Aktions-Buttons in der letzten Spalte ---
            # Da Schaltflächen keine normalen Tabellenzellen sind, brauchen
            # wir ein eigenes Widget als Container (setCellWidget)
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(6, 4, 6, 4)
            btn_layout.setSpacing(6)

            # "Bearbeiten"-Button
            edit_btn = QPushButton("✏️ Bearbeiten")
            edit_btn.setObjectName("btn_icon")
            edit_btn.setFixedHeight(30)
            # Kunden-ID als Property am Button speichern, damit der Slot
            # (_bearbeite_kunde) weiß, welchen Kunden er bearbeiten soll
            edit_btn.setProperty("kunde_id", k["id"])
            edit_btn.clicked.connect(self._bearbeite_kunde)

            # "Löschen"-Button (nur das Mülleimer-Icon, quadratisch)
            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("btn_danger")  # Rote Farbe aus dem CSS
            del_btn.setFixedSize(30, 30)          # Quadratisch: 30 x 30 Pixel
            del_btn.setProperty("kunde_id", k["id"])
            del_btn.clicked.connect(self._loesche_kunde)

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)

            # Das Button-Widget in Spalte 8 (Aktionen) der aktuellen Zeile einfügen
            self.table.setCellWidget(row, 8, btn_widget)

    def _neuer_kunde(self):
        """
        Öffnet den KundeDialog zum Anlegen eines neuen Kunden.

        Wenn der Dialog mit "Speichern" bestätigt wird (Accepted),
        werden die Formulardaten in der Datenbank gespeichert, die Tabelle
        wird aktualisiert und das Signal kunden_geaendert wird ausgelöst.
        """
        # Neuen Dialog ohne vorhandene Kundendaten öffnen
        dlg = KundeDialog(self)

        # exec() öffnet den Dialog und blockiert, bis er geschlossen wird.
        # Der Rückgabewert zeigt an, ob "Speichern" oder "Abbrechen" gedrückt wurde.
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Daten aus dem Dialog in die Datenbank schreiben
            db.speichere_kunde(dlg.result_data)
            # Tabelle neu laden, damit der neue Kunde erscheint
            self.refresh()
            # Andere Widgets über die Änderung informieren
            self.kunden_geaendert.emit()

    def _bearbeite_zeile(self, index):
        """
        Wird aufgerufen, wenn der Nutzer auf eine Tabellenzeile
        doppelklickt. Öffnet den KundeDialog für den Kunden in der
        angeklickten Zeile.

        Args:
            index (QModelIndex): Position der angeklickten Zelle
                                 (enthält Zeile und Spalte).
        """
        # Zelle in Spalte 0 der angeklickten Zeile abrufen
        item = self.table.item(index.row(), 0)
        if item:
            # Versteckte Kunden-ID aus der Zelle lesen (wurde in refresh() gesetzt)
            k = db.get_kunde(item.data(Qt.ItemDataRole.UserRole))
            if k:
                # Dialog mit vorhandenen Kundendaten öffnen
                dlg = KundeDialog(self, k)
                if dlg.exec() == QDialog.DialogCode.Accepted:
                    db.speichere_kunde(dlg.result_data)
                    self.refresh()
                    self.kunden_geaendert.emit()

    def _bearbeite_kunde(self):
        """
        Slot für den "Bearbeiten"-Button in der Aktionsspalte.

        self.sender() gibt das Widget zurück, das das Signal ausgelöst hat
        – in diesem Fall der geklickte Bearbeiten-Button. Über die
        gespeicherte Property "kunde_id" wird der richtige Kunde geladen.
        """
        # Das Widget ermitteln, das den Klick ausgelöst hat (den Button selbst)
        btn = self.sender()

        # Kunden-ID aus der Property des Buttons lesen
        kid = btn.property("kunde_id")

        # Vollständige Kundendaten aus der Datenbank laden
        k = db.get_kunde(kid)
        if k:
            dlg = KundeDialog(self, k)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                db.speichere_kunde(dlg.result_data)
                self.refresh()
                self.kunden_geaendert.emit()

    def _loesche_kunde(self):
        """
        Slot für den "Löschen"-Button in der Aktionsspalte.

        Zeigt zuerst eine Sicherheitsabfrage an, bevor der Kunde
        tatsächlich gelöscht wird. Kunden mit vorhandenen Bestellungen
        können nicht gelöscht werden – in diesem Fall erscheint eine
        Fehlermeldung.
        """
        # Button, der den Klick ausgelöst hat, und die zugehörige Kunden-ID
        btn = self.sender()
        kid = btn.property("kunde_id")

        # Kundendaten laden, um den Namen in der Sicherheitsabfrage anzuzeigen
        k = db.get_kunde(kid)
        if not k:
            return  # Kunde existiert nicht mehr – nichts zu tun

        # Sicherheitsabfrage mit "Ja" und "Nein" anzeigen
        # Der Standardwert ist "Nein", um versehentliches Löschen zu verhindern
        reply = QMessageBox.question(
            self, "Kunden löschen",
            f"Soll <b>{k['vorname']} {k['nachname']}</b> wirklich gelöscht werden?<br>"
            "<small style='color:gray'>Kunden mit Bestellungen können nicht gelöscht werden.</small>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No   # Standardmäßig vorausgewählte Antwort
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Löschen in der Datenbank versuchen; gibt True zurück wenn erfolgreich
            ok = db.loesche_kunde(kid)
            if ok:
                # Tabelle aktualisieren und andere Widgets benachrichtigen
                self.refresh()
                self.kunden_geaendert.emit()
            else:
                # Löschen nicht möglich, weil der Kunde noch Bestellungen hat
                QMessageBox.warning(
                    self, "Nicht möglich",
                    "Dieser Kunde hat noch Bestellungen und kann nicht gelöscht werden."
                )
