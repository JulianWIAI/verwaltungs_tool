"""
Radsport Koch GmbH – Hauptfenster
==================================
Dieses Modul ist der Einstiegspunkt der gesamten Anwendung.
Es definiert das Hauptfenster (MainWindow), die Seitenleiste (Sidebar),
einzelne Navigations-Schaltflächen (NavButton) sowie den Seiten-Header (PageHeader).

Das Hauptfenster verwendet ein QStackedWidget, um zwischen den vier
Programmseiten (Dashboard, Kunden, Artikel, Bestellungen) zu wechseln,
ohne sie alle gleichzeitig im Speicher zu halten (Lazy Loading).
"""

import sys          # Zugriff auf Kommandozeilenargumente und Beenden der App
import os           # Betriebssystem-Funktionen, z. B. Pfade ermitteln
import ctypes       # Zugriff auf Windows-API-Funktionen (für das Taskleisten-Icon)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QStatusBar,
    QSizePolicy
)
# Qt-Kern: Ausrichtungs-Flags und Größenklasse
from PyQt6.QtCore import Qt, QSize
# Schriftart, Icon und Farb-Klassen aus dem GUI-Modul
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor

# Projektpfad
# Damit Python die eigenen Module (database, styles, …) findet,
# wird das Verzeichnis dieser Datei an den Anfang des Suchpfads gesetzt.
sys.path.insert(0, os.path.dirname(__file__))

import database as db   # Eigenes Datenbankmodul für alle SQL-Zugriffe
from styles import MAIN_STYLE, COLOR_PRIMARY, COLOR_SECONDARY, COLOR_WHITE, COLOR_TEXT_LIGHT
# MAIN_STYLE enthält das globale Qt-Stylesheet der gesamten Anwendung


class NavButton(QPushButton):
    """
    Navigationsschaltfläche in der Seitenleiste.

    Erbt von QPushButton und ergänzt:
    - Emoji + Text als Beschriftung
    - Festes Aussehen über das Objekt-Name-System von Qt
    - Eine Methode zum Hervorheben des aktiven Eintrags
    """

    def __init__(self, icon: str, text: str, parent=None):
        """
        Erstellt einen neuen NavButton.

        :param icon:   Emoji-Zeichen, das links vom Text angezeigt wird (z. B. "🏠")
        :param text:   Beschriftungstext des Buttons (z. B. "Dashboard")
        :param parent: Optionales Eltern-Widget (normalerweise die Sidebar)
        """
        # Ruft den Konstruktor der Elternklasse QPushButton auf und
        # setzt dabei den kombinierten Text aus Icon und Beschriftung.
        # Die Leerzeichen sorgen für einen optischen Einzug.
        super().__init__(f"  {icon}  {text}", parent)

        # Objekt-Name wird vom Qt-Stylesheet genutzt, um diesen Button zu stylen
        self.setObjectName("nav_btn")

        # checkable=False: Der Button soll sich nicht wie ein Toggle-Button verhalten
        self.setCheckable(False)

        # Zeigercursor, damit die Maus beim Überfahren zur Hand wird
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Feste Höhe für ein einheitliches Erscheinungsbild in der Leiste
        self.setFixedHeight(46)

        # Breite: so breit wie möglich (Expanding), Höhe: fest (Fixed)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_active(self, active: bool):
        """
        Hebt diesen Button hervor (aktiv) oder setzt ihn zurück (inaktiv).

        Qt wendet Styles auf Basis des Objekt-Namens an. Durch das Umbenennen
        und anschließende "Polishing" erzwingt Qt eine Neuberechnung des Stils.

        :param active: True = Button gehört zur aktuell angezeigten Seite
        """
        # Je nach Zustand unterschiedlichen Objekt-Namen setzen
        self.setObjectName("nav_btn_active" if active else "nav_btn")

        # unpolish() entfernt den alten Stil …
        self.style().unpolish(self)
        # … polish() wendet den neuen Stil anhand des geänderten Objekt-Namens an
        self.style().polish(self)


class Sidebar(QFrame):
    """
    Linke Navigationsleiste der Anwendung.

    Enthält:
    - Logo-Bereich mit Firmenname und Icon
    - Abschnitts-Label "NAVIGATION"
    - Vier NavButtons für die einzelnen Seiten
    - Footer mit Versions- und Copyright-Angabe
    """

    def __init__(self, parent=None):
        """
        Baut die Sidebar vollständig auf.

        :param parent: Optionales Eltern-Widget (normalerweise das MainWindow)
        """
        # Konstruktor von QFrame aufrufen
        super().__init__(parent)

        # Objekt-Name für das Stylesheet (färbt den Hintergrund der Sidebar ein)
        self.setObjectName("sidebar")

        # Vertikales Haupt-Layout ohne Außenabstände und ohne Zeilenabstand
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Logo-Bereich ──────────────────────────────────────────────────────
        logo_frame = QFrame()
        # Leicht abgedunkelter Hintergrund mit einer feinen Trennlinie nach unten
        logo_frame.setStyleSheet(f"""
            background: rgba(0,0,0,0.2);
            border-bottom: 1px solid rgba(255,255,255,0.08);
        """)
        logo_frame.setMinimumHeight(100)  # Mindesthöhe des Logo-Bereichs

        # Horizontales Layout innerhalb des Logo-Rahmens
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(14, 14, 14, 14)  # Innenabstände: oben/rechts/unten/links
        logo_layout.setSpacing(10)  # Abstand zwischen Icon und Textblock

        # Fahrrad-Emoji als visuelles Firmenlogo
        bike_icon = QLabel("🚲")
        bike_icon.setFont(QFont("Segoe UI Emoji", 26))  # Emoji-Schriftart, Größe 26
        bike_icon.setStyleSheet("color: white;")
        bike_icon.setFixedSize(40, 40)   # Quadratischer Platzhalter für das Icon
        bike_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Icon zentrieren

        # Vertikale Spalte für Firmenname + Untertitel
        text_col = QVBoxLayout()
        text_col.setSpacing(2)  # Nur 2 Pixel Abstand zwischen den beiden Labels

        # Firmenname in Fettschrift
        title = QLabel("Radsport Koch")
        title.setObjectName("sidebar_title")  # Für Stylesheet-Targeting
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))

        # Untertitel mit Firmenzusatz und Systemnamen
        subtitle = QLabel("GmbH · Verwaltungssystem")
        subtitle.setObjectName("sidebar_subtitle")
        subtitle.setWordWrap(True)  # Zeilenumbruch bei zu geringer Breite erlauben

        text_col.addWidget(title)
        text_col.addWidget(subtitle)

        # Icon und Textblock horizontal zusammensetzen
        logo_layout.addWidget(bike_icon)
        logo_layout.addLayout(text_col)
        layout.addWidget(logo_frame)  # Logo-Bereich dem Haupt-Layout hinzufügen

        # ── Navigations-Sektion ───────────────────────────────────────────────
        layout.addSpacing(12)  # Kleiner Abstand zwischen Logo und Label

        # Abschnitts-Label "NAVIGATION" in Großbuchstaben, halbtransparent
        nav_label = QLabel("  NAVIGATION")
        nav_label.setStyleSheet("""
            color: rgba(255,255,255,0.35);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 0 16px;
        """)
        layout.addWidget(nav_label)
        layout.addSpacing(4)  # Kleiner Abstand zwischen Label und ersten Button

        # Die vier Navigations-Buttons werden als Instanzvariablen gespeichert,
        # damit MainWindow Klick-Signale darauf verbinden kann.
        self.btn_dashboard   = NavButton("🏠", "Dashboard")
        self.btn_kunden      = NavButton("👥", "Kunden")
        self.btn_artikel     = NavButton("🚲", "Artikel")
        self.btn_bestellungen = NavButton("📦", "Bestellungen")

        # Liste aller Nav-Buttons – nützlich für Schleifen (z. B. set_active)
        self.nav_buttons = [
            self.btn_dashboard,
            self.btn_kunden,
            self.btn_artikel,
            self.btn_bestellungen,
        ]

        # Alle Buttons dem Layout hinzufügen
        for btn in self.nav_buttons:
            layout.addWidget(btn)

        # Streckung schiebt den Footer an den unteren Rand der Sidebar
        layout.addStretch()

        # ── Footer ────────────────────────────────────────────────────────────
        footer = QFrame()
        # Feine Trennlinie oben im Footer-Bereich
        footer.setStyleSheet("border-top: 1px solid rgba(255,255,255,0.08);")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        footer_layout.setSpacing(2)

        # Versionsangabe
        version = QLabel("v1.0.0 · 2025")
        version.setStyleSheet("color: rgba(255,255,255,0.35); font-size: 10px;")

        # Copyright-Hinweis
        copy = QLabel("© Radsport Koch GmbH")
        copy.setStyleSheet("color: rgba(255,255,255,0.25); font-size: 10px;")

        footer_layout.addWidget(version)
        footer_layout.addWidget(copy)
        layout.addWidget(footer)  # Footer ganz unten in der Sidebar

    def set_active(self, index: int):
        """
        Markiert den Button an der gegebenen Position als aktiv,
        alle anderen als inaktiv.

        :param index: Index des aktuell aktiven Buttons (0 = Dashboard, …)
        """
        # Über alle Buttons iterieren und jeden entweder aktivieren oder deaktivieren
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == index)  # True nur für den Button mit dem passenden Index


class PageHeader(QFrame):
    """
    Kopfzeile einer Inhaltsseite.

    Zeigt einen fettgedruckten Seitentitel und einen optionalen Untertitel an.
    Wird für jede der vier Hauptseiten oben eingefügt.
    """

    def __init__(self, title: str, subtitle: str = "", parent=None):
        """
        Erstellt den Seiten-Header.

        :param title:    Hauptüberschrift der Seite (z. B. "🏠 Dashboard")
        :param subtitle: Kurze Beschreibung unterhalb des Titels (optional)
        :param parent:   Optionales Eltern-Widget
        """
        super().__init__(parent)

        # Objekt-Name für das Stylesheet (weißer Hintergrund mit Schatten etc.)
        self.setObjectName("page_header")

        # Vertikales Layout mit Innenabständen
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 14, 24, 14)
        layout.setSpacing(2)

        # Haupt-Titel-Label
        t = QLabel(title)
        t.setObjectName("page_title")
        t.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(t)

        # Untertitel nur hinzufügen, wenn ein Text übergeben wurde
        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("page_subtitle")
            layout.addWidget(s)


class MainWindow(QMainWindow):
    """
    Hauptfenster der Anwendung.

    Verantwortlich für:
    - Aufbau des Gesamtlayouts (Sidebar + Inhaltsbereich)
    - Navigation zwischen den Seiten via QStackedWidget
    - Lazy Loading: Seiten-Widgets werden erst beim ersten Aufruf geladen
    - Statusleiste mit Echtzeit-Statistiken aus der Datenbank
    """

    def __init__(self):
        """
        Initialisiert das Hauptfenster, setzt Fenstertitel, Mindestgröße
        und zentriert es auf dem Bildschirm.
        """
        super().__init__()

        # Titelleiste des Betriebssystemfensters
        self.setWindowTitle("Radsport Koch GmbH – Verwaltungssystem")

        # Fenster-Icon setzen (erscheint in der Titelleiste des Fensters)
        # os.path.dirname(__file__) gibt das Verzeichnis dieser Skript-Datei zurück,
        # damit das Icon unabhängig vom Arbeitsverzeichnis gefunden wird
        icon_pfad = os.path.join(os.path.dirname(__file__), "app_icon.png")
        self.setWindowIcon(QIcon(icon_pfad))

        # Mindestgröße: Die App soll nicht kleiner als 1280×780 Pixel werden
        self.setMinimumSize(1280, 780)

        # Startgröße des Fensters beim ersten Öffnen
        self.resize(1400, 860)

        # Zentriert starten
        # primaryScreen().geometry() gibt die Auflösung des Hauptbildschirms zurück
        screen = QApplication.primaryScreen().geometry()
        self.move(
            # X-Position: Mitte des Bildschirms minus halbe Fensterbreite
            (screen.width() - self.width()) // 2,
            # Y-Position: Mitte des Bildschirms minus halbe Fensterhöhe
            (screen.height() - self.height()) // 2
        )

        # Benutzeroberfläche aufbauen
        self._setup_ui()

        # Beim Start direkt das Dashboard (Index 0) anzeigen
        self._navigate(0)

    def _setup_ui(self):
        """
        Baut das gesamte Haupt-UI auf:
        - Zentrales Widget mit horizontalem Layout
        - Sidebar links
        - Inhaltsbereich rechts mit QStackedWidget für die Seiten
        - Statusleiste unten
        """
        # Das zentrale Widget ist der Inhaltscontainer des QMainWindow
        central = QWidget()
        self.setCentralWidget(central)

        # Hauptlayout: Sidebar und Inhaltsbereich nebeneinander
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Kein Außenabstand
        main_layout.setSpacing(0)                    # Kein Abstand zwischen Sidebar und Inhalt

        # ── Sidebar ───────────────────────────────────────────────────────────
        self.sidebar = Sidebar()

        # Jeden Button der Sidebar mit der _navigate-Methode verbinden.
        # lambda: … sorgt dafür, dass der Index erst beim Klick übergeben wird.
        self.sidebar.btn_dashboard.clicked.connect(lambda: self._navigate(0))
        self.sidebar.btn_kunden.clicked.connect(lambda: self._navigate(1))
        self.sidebar.btn_artikel.clicked.connect(lambda: self._navigate(2))
        self.sidebar.btn_bestellungen.clicked.connect(lambda: self._navigate(3))
        main_layout.addWidget(self.sidebar)

        # ── Inhaltsbereich ────────────────────────────────────────────────────
        content_frame = QFrame()
        content_frame.setObjectName("content_area")  # Für Stylesheet-Targeting
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # ── Page Stack ────────────────────────────────────────────────────────
        # QStackedWidget: Zeigt immer nur eine Seite gleichzeitig an.
        # Seitenwechsel erfolgt per setCurrentIndex().
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: #f0f2f5; }")

        # Seiten lazy laden:
        # _pages speichert das Layout jeder Seite, damit später das eigentliche
        # Inhalt-Widget dynamisch hinzugefügt werden kann.
        self._pages = {}

        # Konfiguration aller Seiten: (Titel, Untertitel)
        self._page_configs = [
            ("🏠 Dashboard",    "Aktuelle Übersicht & Statistiken"),
            ("👥 Kunden",       "Kundenstammdaten verwalten"),
            ("🚲 Artikel",      "Produktkatalog & Lager"),
            ("📦 Bestellungen", "Auftragsverwaltung"),
        ]

        # Für jede Seite: Wrapper-Widget + Header anlegen und dem Stack hinzufügen
        for i, (title, subtitle) in enumerate(self._page_configs):
            # Wrapper-Widget enthält Header oben und (später) das Inhalt-Widget darunter
            wrapper = QWidget()
            wrapper.setObjectName("page_wrapper")
            wrapper.setStyleSheet("QWidget#page_wrapper { background: #f0f2f5; }")

            w_layout = QVBoxLayout(wrapper)
            w_layout.setContentsMargins(0, 0, 0, 0)
            w_layout.setSpacing(0)

            # Seitenheader (Titel + Untertitel) direkt einfügen
            header = PageHeader(title, subtitle)
            w_layout.addWidget(header)

            self.stack.addWidget(wrapper)

            # Layout unter dem Schlüssel i speichern – beim ersten Besuch wird
            # hier das eigentliche Seiten-Widget angehängt (Lazy Loading)
            self._pages[i] = w_layout

        content_layout.addWidget(self.stack)

        # Inhaltsbereich nimmt den restlichen horizontalen Platz ein (stretch=1)
        main_layout.addWidget(content_frame, stretch=1)

        # ── Statusbar ─────────────────────────────────────────────────────────
        status = QStatusBar()
        status.setFixedHeight(26)  # Kompakte Höhe für die Statusleiste
        self.setStatusBar(status)
        self._status_bar = status

        # Statusleiste direkt beim Start mit Datenbankwerten befüllen
        self._update_status()

    def _navigate(self, index: int):
        """
        Wechselt zur Seite mit dem angegebenen Index.

        Beim ersten Aufruf einer Seite wird das zugehörige Widget
        dynamisch importiert und dem Layout hinzugefügt (Lazy Loading).
        Das vermeidet lange Startzeiten, weil nicht alle Module sofort geladen werden.

        :param index: 0 = Dashboard, 1 = Kunden, 2 = Artikel, 3 = Bestellungen
        """
        # Aktiven Button in der Sidebar aktualisieren
        self.sidebar.set_active(index)

        # Sichtbare Seite im Stack wechseln
        self.stack.setCurrentIndex(index)

        # Lazy Load der eigentlichen Widgets
        layout = self._pages[index]

        # layout.count() == 1 bedeutet: Bisher wurde nur der Header eingefügt.
        # Das eigentliche Inhalts-Widget fehlt noch → jetzt laden.
        if layout.count() == 1:  # Nur Header vorhanden
            if index == 0:
                # Dashboard-Modul erst jetzt importieren
                from dashboard import DashboardWidget
                w = DashboardWidget()
            elif index == 1:
                from kunden import KundenWidget
                w = KundenWidget()
                # Signal: Wenn Kundendaten geändert werden, Statusleiste aktualisieren
                w.kunden_geaendert.connect(self._update_status)
            elif index == 2:
                from artikel import ArtikelWidget
                w = ArtikelWidget()
                # Signal: Wenn Artikeldaten geändert werden, Statusleiste aktualisieren
                w.artikel_geaendert.connect(self._update_status)
            elif index == 3:
                from bestellungen import BestellungenWidget
                w = BestellungenWidget()
                # Statusleiste und Dashboard bei Bestellungsänderungen aktualisieren
                w.bestellungen_geaendert.connect(self._update_status)
                w.bestellungen_geaendert.connect(self._refresh_dashboard)
            else:
                return  # Unbekannter Index – nichts tun

            # Das neu erstellte Widget dem Seiten-Layout hinzufügen
            layout.addWidget(w)

        # Statusleiste nach jedem Seitenwechsel aktualisieren
        self._update_status()

    def _update_status(self):
        """
        Liest aktuelle Statistiken aus der Datenbank und zeigt sie
        in der Statusleiste am unteren Fensterrand an.
        """
        # Datenbankabfrage: liefert ein Dictionary mit Kennzahlen
        stats = db.get_dashboard_stats()

        # Statusleisten-Text aus den Kennzahlen zusammensetzen
        self._status_bar.showMessage(
            f"  👥 {stats['kunden_gesamt']} Kunden  "
            f"·  🚲 {stats['artikel_gesamt']} Artikel  "
            f"·  📦 {stats['bestellungen_gesamt']} Bestellungen  "
            f"·  💰 Umsatz gesamt: € {stats['umsatz_gesamt']:,.2f}  "
            f"·  ⏳ {stats['bestellungen_offen']} offen"
        )

    def _refresh_dashboard(self):
        """
        Aktualisiert das Dashboard-Widget, falls es bereits geladen wurde.

        Wird aufgerufen, wenn sich Bestellungsdaten ändern, damit die
        Dashboard-Statistiken immer aktuell bleiben.
        """
        # Layout von Seite 0 (Dashboard) holen
        layout = self._pages[0]

        # layout.count() > 1: Dashboard-Widget wurde bereits geladen (Lazy Load erfolgt)
        if layout.count() > 1:
            # Das zweite Element im Layout ist das eigentliche Dashboard-Widget (Index 1)
            w = layout.itemAt(1).widget()

            # Sicherheitsprüfung: Hat das Widget eine refresh()-Methode?
            if hasattr(w, "refresh"):
                w.refresh()  # Dashboard-Inhalte neu laden


def main():
    """
    Einstiegspunkt der Anwendung.

    Erstellt die QApplication, initialisiert die Datenbank,
    öffnet das Hauptfenster und startet die Qt-Ereignisschleife.
    """
    # Windows-Taskleisten-Icon fix:
    # Windows gruppiert Taskleisten-Buttons anhand der "AppUserModelID".
    # Ohne diese ID erbt das Programm das Icon des Python-Interpreters.
    # SetCurrentProcessExplicitAppUserModelID() weist dem Prozess eine eigene
    # ID zu, sodass Windows das Qt-Fenster-Icon in der Taskleiste anzeigt.
    if sys.platform == "win32":
        import ctypes
        myappid = 'mycompany.myproduct.subproduct.version'  # Use whatever ID you had before
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # QApplication muss als erstes erstellt werden – sie verwaltet die GUI-Ressourcen.
    # sys.argv übergibt eventuelle Kommandozeilenargumente an Qt.
    app = QApplication(sys.argv)

    # Metadaten der Anwendung (werden z. B. in Systemdialogen angezeigt)
    app.setApplicationName("Radsport Koch GmbH")
    app.setApplicationVersion("1.0.0")

    # App-Icon setzen – dieses Icon erscheint in der Windows-Taskleiste,
    # im Alt-Tab-Dialog und überall dort, wo das Betriebssystem ein App-Symbol anzeigt.
    # Es muss auf der QApplication gesetzt werden (nicht nur auf dem Fenster),
    # damit Windows es als Taskleisten-Icon erkennt.
    icon_pfad = os.path.join(os.path.dirname(__file__), "app_icon.png")
    app.setWindowIcon(QIcon(icon_pfad))

    # Globales Stylesheet auf die gesamte Anwendung anwenden
    app.setStyleSheet(MAIN_STYLE)

    # Datenbank initialisieren:
    # Erstellt die SQLite-Datenbankdatei und alle Tabellen, falls sie noch nicht existieren
    db.init_db()

    # Hauptfenster erstellen und anzeigen
    window = MainWindow()
    window.show()

    # Qt-Ereignisschleife starten. Das Programm läuft hier, bis das Fenster geschlossen wird.
    # sys.exit() sorgt dafür, dass der Exit-Code von Qt an das Betriebssystem weitergegeben wird.
    sys.exit(app.exec())


# Standardmäßiges Python-Einstiegsmuster:
# Dieser Block wird nur ausgeführt, wenn die Datei direkt gestartet wird,
# NICHT wenn sie als Modul von einer anderen Datei importiert wird.
if __name__ == "__main__":
    main()
