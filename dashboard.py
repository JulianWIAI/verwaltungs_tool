"""
Radsport Koch GmbH – Dashboard
================================
Dieses Modul enthält alle Widgets, die auf der Dashboard-Seite der Anwendung
angezeigt werden. Das Dashboard bietet eine visuelle Übersicht über die
wichtigsten Kennzahlen des Fahrradgeschäfts:

- StatCard:               Einzelne Kennzahl-Karte (z. B. Anzahl Kunden)
- MiniChart:              Einfaches Balkendiagramm für den Umsatzverlauf
- TopArtikelWidget:       Rangliste der umsatzstärksten Artikel
- StatusVerteilungWidget: Aufschlüsselung aller Bestellungen nach Status
- DashboardWidget:        Haupt-Widget, das alle obigen Elemente zusammenfasst
                          und sich alle 60 Sekunden automatisch aktualisiert

Alle Diagramme werden ohne externe Bibliotheken (kein matplotlib o. Ä.)
nur mit PyQt6-Widgets realisiert.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer   # Qt: Ausrichtungs-Flags; QTimer: periodischer Aufruf
from PyQt6.QtGui import QFont         # Schriftarten
import database as db                 # Eigenes Datenbankmodul für alle SQL-Abfragen
from styles import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_SUCCESS, COLOR_WARNING,
    COLOR_DANGER, COLOR_WHITE, COLOR_BG, COLOR_TEXT_LIGHT,
    COLOR_INFO, COLOR_CARD, COLOR_BORDER, STATUS_FARBEN
)
# STATUS_FARBEN: Dictionary, das jedem Bestellstatus eine Farbe zuordnet


def _farbe_badge(text: str, farbe: str) -> QLabel:
    """
    Erstellt ein farbiges Badge-Label (abgerundetes Etikett mit Text).

    Wird verwendet, um Status-Angaben optisch hervorzuheben.

    :param text:  Anzuzeigender Text im Badge (z. B. "Offen")
    :param farbe: Hex-Farbcode der Akzentfarbe (z. B. "#e63946")
    :return:      Fertig gestyltes QLabel
    """
    lbl = QLabel(text)
    # Die Farbe wird mit "22" als Hex-Alpha-Wert angehängt → ~13% Deckkraft als Hintergrund.
    # So wirkt das Badge transparent-farbig statt vollständig gefüllt.
    lbl.setStyleSheet(f"""
        background-color: {farbe}22;
        color: {farbe};
        border-radius: 10px;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: 600;
    """)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Text horizontal und vertikal zentrieren
    return lbl


class StatCard(QFrame):
    """
    Kennzahl-Karte für das Dashboard.

    Jede Karte zeigt ein Emoji-Icon, einen großen Zahlenwert und
    einen Beschriftungstext. Die linke Kante ist farbig eingefärbt,
    um die Karten visuell voneinander zu unterscheiden.

    Beispiel: "👥  342  Kunden"
    """

    def __init__(self, titel: str, wert: str, icon: str, farbe: str, parent=None):
        """
        Erstellt eine neue StatCard.

        :param titel:  Beschriftung unterhalb des Wertes (z. B. "Kunden")
        :param wert:   Angezeigter Zahlenwert als Zeichenkette (z. B. "342")
        :param icon:   Emoji-Zeichen links in der Karte (z. B. "👥")
        :param farbe:  Akzentfarbe der Karte als Hex-Code (z. B. "#0066cc")
        :param parent: Optionales Eltern-Widget
        """
        super().__init__(parent)

        # Objekt-Name ermöglicht gezieltes Ansprechen im Stylesheet
        self.setObjectName("stat_card")

        # Inline-Stylesheet: weißer Hintergrund, abgerundete Ecken, farbige linke Kante
        self.setStyleSheet(f"""
            #stat_card {{
                background: {COLOR_WHITE};
                border-radius: 12px;
                border-left: 5px solid {farbe};
                padding: 16px 20px;
            }}
        """)

        # Horizontales Layout: Icon links, Text (Wert + Titel) rechts
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Icon-Label ────────────────────────────────────────────────────────
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 28))  # Große Emoji-Darstellung
        icon_lbl.setFixedSize(56, 56)                  # Quadratischer Container
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Hintergrund mit sehr geringer Deckkraft (18 Hex ≈ 9%) in der Akzentfarbe
        icon_lbl.setStyleSheet(f"""
            background: {farbe}18;
            border-radius: 12px;
        """)

        # ── Text-Layout (Wert oben, Titel unten) ─────────────────────────────
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        # Großer, farbiger Zahlenwert (wird später per update_wert() aktualisiert)
        self.wert_lbl = QLabel(wert)
        self.wert_lbl.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        self.wert_lbl.setStyleSheet(f"color: {farbe};")

        # Beschriftungs-Label in gedämpfter Farbe
        titel_lbl = QLabel(titel)
        titel_lbl.setWordWrap(True)  # Umbruch erlauben, falls Titel zu lang
        titel_lbl.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px; font-weight: 500;")

        text_layout.addWidget(self.wert_lbl)
        text_layout.addWidget(titel_lbl)

        # Alles zum Haupt-Layout hinzufügen
        layout.addWidget(icon_lbl)
        layout.addSpacing(12)       # Lücke zwischen Icon und Text
        layout.addLayout(text_layout)
        layout.addStretch()         # Restlichen Platz rechts leer lassen

    def update_wert(self, wert: str):
        """
        Aktualisiert den angezeigten Zahlenwert der Karte.

        :param wert: Neuer Wert als Zeichenkette (z. B. "347" oder "€ 12.500")
        """
        self.wert_lbl.setText(wert)


class MiniChart(QFrame):
    """
    Einfaches Balkendiagramm (kein matplotlib nötig).

    Stellt den Umsatzverlauf der letzten Monate als senkrechte
    Balken dar. Jeder Balken wird proportional zum Maximalwert skaliert.
    """

    def __init__(self, title: str, data: list, parent=None):
        """
        Erstellt das Balkendiagramm.

        :param title:  Überschrift des Diagramms (z. B. "📈 Umsatz letzte 6 Monate")
        :param data:   Liste von Dictionaries mit den Schlüsseln "monat" und "umsatz"
                       Beispiel: [{"monat": "2025-01", "umsatz": 4200.0}, …]
        :param parent: Optionales Eltern-Widget
        """
        super().__init__(parent)

        # Objekt-Name "card" → weißer Kartenstil aus dem Stylesheet
        self.setObjectName("card")
        self.setStyleSheet(f"""
            #card {{
                background: {COLOR_WHITE};
                border-radius: 12px;
                border: 1px solid {COLOR_BORDER};
                padding: 16px;
            }}
        """)

        # Daten als Instanzvariable speichern (aktuell nur zur Referenz)
        self.data = data

        layout = QVBoxLayout(self)

        # Überschrift des Diagramms
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {COLOR_PRIMARY};")
        layout.addWidget(title_lbl)

        # Wenn keine Daten vorhanden sind, Hinweistext anzeigen und abbrechen
        if not data:
            empty = QLabel("Noch keine Daten vorhanden")
            empty.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)
            return  # Frühzeitiger Ausstieg – kein Diagramm zeichnen

        # Maximalen Umsatz aller Datenpunkte ermitteln (für die Skalierung)
        # Der Ausdruck "or 1" verhindert eine Division durch 0 beim nächsten Schritt
        max_val = max(d.get("umsatz", 0) for d in data) or 1

        # Container-Widget für alle Balken (horizontales Layout)
        bars_widget = QWidget()
        bars_layout = QHBoxLayout(bars_widget)
        bars_layout.setSpacing(8)
        bars_layout.setContentsMargins(0, 8, 0, 0)

        # Für jeden Datenpunkt einen Balken zeichnen
        for d in data:
            # Vertikales Teil-Layout: Wert-Label oben, Balken mitte, Monats-Label unten
            bar_container = QVBoxLayout()
            bar_container.setSpacing(4)
            # Ausrichtung nach unten: Kleine Balken "wachsen" von unten nach oben
            bar_container.setAlignment(Qt.AlignmentFlag.AlignBottom)

            umsatz = d.get("umsatz", 0)

            # Balkenhöhe proportional zum Maximum berechnen.
            # max(4, …) stellt sicher, dass selbst ein Null-Wert noch sichtbar ist.
            hoehe = max(4, int((umsatz / max_val) * 100))

            # Der eigentliche Balken als farbiger QFrame
            bar = QFrame()
            bar.setFixedSize(40, hoehe)  # Balkenbreite fix 40px, Höhe dynamisch
            # Farbverlauf von oben (COLOR_SECONDARY) nach unten (dunkleres Rot)
            bar.setStyleSheet(f"""
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {COLOR_SECONDARY}, stop:1 #c1121f);
                border-radius: 4px;
            """)

            # Wert-Label über dem Balken (in Tausend, z. B. "4.2k")
            val_lbl = QLabel(f"{umsatz/1000:.1f}k")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_lbl.setStyleSheet("font-size: 10px; color: " + COLOR_TEXT_LIGHT + ";")
            val_lbl.setFixedWidth(50)

            # Monats-Label unter dem Balken – nur die letzten 5 Zeichen (MM-YY)
            monat_lbl = QLabel(d.get("monat", "")[-5:])  # MM-YY
            monat_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            monat_lbl.setStyleSheet("font-size: 10px; color: " + COLOR_TEXT_LIGHT + ";")
            monat_lbl.setFixedWidth(50)

            # Elemente dem Balken-Container hinzufügen (von oben nach unten)
            bar_container.addWidget(val_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            bar_container.addWidget(bar, alignment=Qt.AlignmentFlag.AlignCenter)
            bar_container.addWidget(monat_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

            # Fertigen Balken dem horizontalen Gesamt-Layout hinzufügen
            bars_layout.addLayout(bar_container)

        # Restlichen Platz rechts leer lassen (Balken linksbündig)
        bars_layout.addStretch()
        layout.addWidget(bars_widget)


class TopArtikelWidget(QFrame):
    """
    Rangliste der umsatzstärksten Artikel.

    Zeigt die Top-Artikel als nummerierte Zeilen mit
    Fortschrittsbalken und Umsatzbetrag an.
    """

    def __init__(self, data: list, parent=None):
        """
        Erstellt die Top-Artikel-Liste.

        :param data:   Liste von Dictionaries mit den Schlüsseln "bezeichnung" und "umsatz".
                       Die Liste sollte bereits absteigend nach Umsatz sortiert sein.
        :param parent: Optionales Eltern-Widget
        """
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            #card {{
                background: {COLOR_WHITE};
                border-radius: 12px;
                border: 1px solid {COLOR_BORDER};
                padding: 16px;
            }}
        """)
        layout = QVBoxLayout(self)

        # Überschrift
        title = QLabel("🏆 Top Artikel")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_PRIMARY};")
        layout.addWidget(title)

        # Leerzustand: Noch keine Verkäufe in der Datenbank
        if not data:
            empty = QLabel("Noch keine Verkäufe")
            empty.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")
            layout.addWidget(empty)
            return

        # Verschiedene Akzentfarben für die Ränge 1–5 (danach wird zyklisch wiederholt)
        farben = [COLOR_SECONDARY, COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING, "#9b59b6"]

        # Umsatz des führenden Artikels als Referenzwert für die Balkenbreite
        max_u = data[0]["umsatz"] if data else 1

        # Für jeden Artikel eine Zeile aufbauen
        for i, art in enumerate(data):
            row = QHBoxLayout()

            # Rang-Nummer (z. B. "#1")
            rang = QLabel(f"#{i+1}")
            rang.setFixedWidth(28)
            rang.setStyleSheet(f"""
                font-weight: 700; font-size: 13px;
                color: {farben[i % len(farben)]};
            """)

            # Artikelbezeichnung, auf 30 Zeichen gekürzt (verhindert Überlauf)
            name = QLabel(art["bezeichnung"][:30])
            name.setStyleSheet("font-size: 12px;")
            # Expanding: Der Name erhält den verfügbaren Platz zwischen Rang und Balken
            name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

            # ── Fortschrittsbalken ────────────────────────────────────────────
            # Grauer Hintergrunds-Rahmen des Balkens
            bar_bg = QFrame()
            bar_bg.setFixedHeight(6)
            bar_bg.setStyleSheet(f"background: #f0f2f5; border-radius: 3px;")

            # Farbiger Fortschrittsbalken als Kind des Hintergrunds-Rahmens
            bar_w = QFrame(bar_bg)

            # Breite proportional zum Maximalumsatz, mindestens 4 Pixel sichtbar
            breite = max(4, int((art["umsatz"] / max_u) * 120))
            bar_w.setFixedSize(breite, 6)
            bar_w.setStyleSheet(f"background: {farben[i % len(farben)]}; border-radius: 3px;")

            # Umsatz-Label rechts in der Zeile
            val = QLabel(f"€ {art['umsatz']:,.0f}")
            val.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLOR_PRIMARY};")
            val.setFixedWidth(80)
            val.setAlignment(Qt.AlignmentFlag.AlignRight)

            # Balken in einen Container packen, damit das Layout korrekt funktioniert
            row.addWidget(rang)
            row.addWidget(name)
            bar_container = QWidget()
            bar_container.setFixedWidth(130)
            bar_container.setLayout(QVBoxLayout())
            bar_container.layout().setContentsMargins(0, 4, 0, 0)  # Kleiner oberer Einzug
            bar_container.layout().addWidget(bar_bg)
            row.addWidget(bar_container)
            row.addWidget(val)

            # Fertige Zeile dem Gesamt-Layout hinzufügen
            layout.addLayout(row)


class StatusVerteilungWidget(QFrame):
    """
    Zeigt die Verteilung aller Bestellungen nach ihrem Status.

    Für jeden Status (z. B. "Offen", "In Bearbeitung", "Geliefert")
    wird eine Zeile mit farbigem Punkt, Statusname, Anzahl und
    prozentualem Anteil angezeigt.
    """

    def __init__(self, data: list, parent=None):
        """
        Erstellt das Status-Verteilungs-Widget.

        :param data:   Liste von Dictionaries mit "status" und "anzahl".
                       Beispiel: [{"status": "Offen", "anzahl": 12}, …]
        :param parent: Optionales Eltern-Widget
        """
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            #card {{
                background: {COLOR_WHITE};
                border-radius: 12px;
                border: 1px solid {COLOR_BORDER};
                padding: 16px;
            }}
        """)
        layout = QVBoxLayout(self)

        # Überschrift
        title = QLabel("📦 Bestellstatus")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_PRIMARY};")
        layout.addWidget(title)

        # Gesamtzahl aller Bestellungen berechnen (für die Prozentwerte)
        # "or 1" verhindert eine Division durch 0
        total = sum(d["anzahl"] for d in data) or 1

        # Für jeden Status eine Zeile erstellen
        for d in data:
            # Farbe aus dem globalen STATUS_FARBEN-Dictionary holen,
            # Fallback auf gedämpftes Grau falls der Status unbekannt ist
            farbe = STATUS_FARBEN.get(d["status"], COLOR_TEXT_LIGHT)

            row = QHBoxLayout()

            # Farbiger Punkt ("●") als visuelles Statusindikator
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {farbe}; font-size: 16px;")
            dot.setFixedWidth(20)  # Feste Breite hält alle Zeilen bündig

            # Statusbezeichnung
            name = QLabel(d["status"])
            name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            name.setStyleSheet("font-size: 12px;")

            # Prozentualen Anteil berechnen und zusammen mit der Anzahl anzeigen
            pct = int(d["anzahl"] / total * 100)
            val = QLabel(f"{d['anzahl']}  ({pct}%)")
            val.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_LIGHT};")

            row.addWidget(dot)
            row.addWidget(name)
            row.addWidget(val)
            layout.addLayout(row)


class DashboardWidget(QWidget):
    """
    Haupt-Widget der Dashboard-Seite.

    Kombiniert alle Karten und Diagramme zu einer scrollbaren Übersichtsseite.
    Aktualisiert sich automatisch alle 60 Sekunden über einen QTimer.

    Aufbau der Seite (von oben nach unten):
    1. Begrüßungszeile
    2. Reihe mit 6 StatCards (Kunden, Artikel, Bestellungen, Offen, Umsatz, Nachbestellen)
    3. Diagramm-Reihe (MiniChart + TopArtikelWidget)
    4. Untere Reihe (StatusVerteilungWidget + optionaler Lager-Warnhinweis)
    """

    def __init__(self, parent=None):
        """
        Erstellt das Dashboard-Widget, baut die UI auf und startet
        den automatischen Aktualisierungs-Timer.

        :param parent: Optionales Eltern-Widget
        """
        super().__init__(parent)

        # Benutzeroberfläche aufbauen
        self._setup_ui()

        # Sofortige erste Befüllung mit Datenbankdaten
        self.refresh()

        # Auto-Refresh alle 60s
        # QTimer löst nach jedem Intervall das timeout-Signal aus,
        # das hier mit der refresh()-Methode verbunden ist.
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(60_000)  # 60.000 Millisekunden = 60 Sekunden

    def _setup_ui(self):
        """
        Baut den statischen Rahmen der Dashboard-Seite auf:
        - Scroll-Bereich für den gesamten Inhalt
        - Begrüßungszeile
        - Leere Platzhalter-Layouts für Karten, Diagramme und untere Reihe

        Die Platzhalter werden später in refresh() mit Inhalten befüllt.
        """
        # QScrollArea: Macht den gesamten Inhalt scrollbar, falls das Fenster zu klein ist
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)             # Inhalt passt sich der Breite an
        scroll.setFrameShape(QFrame.Shape.NoFrame)  # Keinen sichtbaren Rahmen um die ScrollArea
        scroll.setStyleSheet("background: transparent;")

        # Container-Widget innerhalb der ScrollArea
        container = QWidget()
        scroll.setWidget(container)

        # Äußeres Layout des DashboardWidget – nur die ScrollArea
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # Inneres Layout innerhalb der ScrollArea mit Außenabständen
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(24, 20, 24, 24)
        self.main_layout.setSpacing(20)  # Abstand zwischen den einzelnen Zeilen

        # ── Begrüßung ─────────────────────────────────────────────────────────
        greet_row = QHBoxLayout()

        # Großer Begrüßungstext
        greet = QLabel("👋 Willkommen zurück!")
        greet.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        greet.setStyleSheet(f"color: {COLOR_PRIMARY};")

        # Kleiner Untertitel darunter
        sub = QLabel("Hier ist Ihre aktuelle Übersicht")
        sub.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-size: 12px;")

        # Begrüßung und Untertitel vertikal übereinander
        greet_col = QVBoxLayout()
        greet_col.setSpacing(2)
        greet_col.addWidget(greet)
        greet_col.addWidget(sub)

        greet_row.addLayout(greet_col)
        greet_row.addStretch()  # Restlichen Platz rechts frei lassen

        self.main_layout.addLayout(greet_row)

        # ── Stat-Karten ───────────────────────────────────────────────────────
        # Horizontale Reihe der sechs Kennzahl-Karten
        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(16)

        # Jede StatCard wird mit Titel, Platzhalter-Wert "-", Icon und Farbe erstellt
        self.card_kunden       = StatCard("Kunden",         "-",  "👥", COLOR_INFO,      self)
        self.card_artikel      = StatCard("Artikel",        "-",  "🚲", COLOR_PRIMARY,   self)
        self.card_bestellungen = StatCard("Bestellungen",   "-",  "📦", COLOR_SUCCESS,   self)
        self.card_offen        = StatCard("Offen",          "-",  "⏳", COLOR_WARNING,   self)
        self.card_umsatz       = StatCard("Umsatz (Monat)", "-",  "💰", COLOR_SECONDARY, self)
        self.card_lager        = StatCard("Nachbestellen",  "-",  "⚠️", COLOR_DANGER,    self)

        # Alle Karten dem Layout hinzufügen
        for card in [self.card_kunden, self.card_artikel, self.card_bestellungen,
                     self.card_offen, self.card_umsatz, self.card_lager]:
            # Expanding: Karten teilen sich den verfügbaren Platz gleichmäßig
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.stats_row.addWidget(card)

        self.main_layout.addLayout(self.stats_row)

        # ── Diagramme (Platzhalter – werden bei refresh() befüllt) ────────────
        # charts_row: Umsatz-Diagramm (links) + Top-Artikel (rechts)
        self.charts_row = QHBoxLayout()
        self.charts_row.setSpacing(16)
        self.main_layout.addLayout(self.charts_row)

        # bottom_row: Status-Verteilung + optionaler Lager-Warnhinweis
        self.bottom_row = QHBoxLayout()
        self.bottom_row.setSpacing(16)
        self.main_layout.addLayout(self.bottom_row)

        # Streckung am Ende schiebt alles nach oben und verhindert unschöne Dehnung
        self.main_layout.addStretch()

        # Platzhalter-Widgets (werden beim ersten refresh() durch echte Widgets ersetzt)
        self._chart_widget  = None
        self._top_widget    = None
        self._status_widget = None

    def _clear_layout(self, layout):
        """
        Entfernt alle Widgets aus einem Layout und gibt deren Speicher frei.

        Wird vor jedem refresh() aufgerufen, damit die Diagramm-Reihen
        neu aufgebaut werden können ohne Duplikate zu erzeugen.

        :param layout: Das zu leerende QLayout-Objekt
        """
        # Solange noch Elemente im Layout vorhanden sind …
        while layout.count():
            # takeAt(0) entfernt das erste Element und gibt es zurück
            item = layout.takeAt(0)
            if item.widget():
                # deleteLater() gibt das Widget nach dem aktuellen Ereigniszyklus frei
                item.widget().deleteLater()

    def refresh(self):
        """
        Lädt aktuelle Daten aus der Datenbank und aktualisiert alle
        Dashboard-Elemente.

        Diese Methode wird:
        - Einmalig beim Start aufgerufen
        - Automatisch alle 60 Sekunden durch den QTimer ausgelöst
        - Manuell aufgerufen, wenn sich Bestellungsdaten ändern
        """
        # Alle Kennzahlen auf einmal aus der Datenbank holen
        stats = db.get_dashboard_stats()

        # ── StatCards aktualisieren ───────────────────────────────────────────
        self.card_kunden.update_wert(str(stats["kunden_gesamt"]))
        self.card_artikel.update_wert(str(stats["artikel_gesamt"]))
        self.card_bestellungen.update_wert(str(stats["bestellungen_gesamt"]))
        self.card_offen.update_wert(str(stats["bestellungen_offen"]))
        # Umsatz mit Tausendertrennzeichen und ohne Nachkommastellen formatieren
        self.card_umsatz.update_wert(f"€ {stats['umsatz_monat']:,.0f}")
        self.card_lager.update_wert(str(stats["nachbestellen"]))

        # ── Charts neu aufbauen ───────────────────────────────────────────────
        # Alte Diagramm-Widgets entfernen (sonst würden bei jedem Refresh neue hinzukommen)
        self._clear_layout(self.charts_row)
        self._clear_layout(self.bottom_row)

        # Umsatz-Balkendiagramm mit den Monatsdaten der letzten 6 Monate
        chart = MiniChart("📈 Umsatz (letzte 6 Monate)", stats["umsatz_verlauf"])
        chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        chart.setMinimumHeight(180)
        # stretch=2: Das Diagramm bekommt doppelt so viel Platz wie die Top-Artikel-Liste
        self.charts_row.addWidget(chart, stretch=2)

        # Top-Artikel-Liste (bester Artikel ganz oben)
        top = TopArtikelWidget(stats["top_artikel"])
        top.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # stretch=1: Top-Artikel bekommt halb so viel Platz wie das Diagramm
        self.charts_row.addWidget(top, stretch=1)

        # Status-Verteilung (immer anzeigen)
        status_w = StatusVerteilungWidget(stats["status_verteilung"])
        status_w.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        status_w.setFixedWidth(260)  # Feste Breite für das Status-Widget
        self.bottom_row.addWidget(status_w)

        # ── Lager-Warnhinweis (nur bei Bedarf) ───────────────────────────────
        # Den Warnhinweis nur anzeigen, wenn tatsächlich Artikel nachbestellt werden müssen
        if stats["nachbestellen"] > 0:
            # Gelber Warnrahmen
            warn = QFrame()
            warn.setStyleSheet(f"""
                background: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 10px;
                padding: 12px;
            """)
            warn_layout = QHBoxLayout(warn)

            # Warn-Icon
            icon = QLabel("⚠️")
            icon.setFont(QFont("Segoe UI Emoji", 18))

            # Warntext mit fett hervorgehobener Anzahl der betroffenen Artikel
            msg = QLabel(
                f"<b>{stats['nachbestellen']} Artikel</b> haben den Mindestbestand unterschritten "
                "und sollten nachbestellt werden."
            )
            msg.setWordWrap(True)  # Zeilenumbruch bei langen Texten erlauben
            msg.setStyleSheet("color: #856404; font-size: 13px;")

            warn_layout.addWidget(icon)
            warn_layout.addWidget(msg)
            self.bottom_row.addWidget(warn)

        # Restlichen Platz in der unteren Zeile frei lassen
        self.bottom_row.addStretch()
