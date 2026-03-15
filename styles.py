"""
Radsport Koch GmbH – Zentrales Stylesheet & Theme
==================================================
Dieses Modul definiert alle visuellen Einstellungen der Anwendung an einem
zentralen Ort. Farben, Status-Kennzeichnungen und das vollständige Qt-Stylesheet
(MAIN_STYLE) werden hier festgelegt und können von allen anderen Modulen
importiert werden.

Vorteile dieses Ansatzes:
- Änderungen am Design müssen nur an einer einzigen Stelle gemacht werden.
- Die gesamte Anwendung sieht dadurch einheitlich aus.
- Farbkonstanten können mit sprechenden Namen (z. B. COLOR_DANGER) verwendet
  werden, statt überall magic hex-Codes wie "#e74c3c" zu schreiben.
"""

# ──────────────────────────────────────────────────────────────────────────────
# FARBKONSTANTEN
# Alle Farben der Anwendung sind hier als Konstanten definiert.
# Eine Konstante in Python wird per Konvention in GROSSBUCHSTABEN geschrieben.
# Hexadezimalfarben wie "#1a2744" entsprechen dem RGB-Format (Rot, Grün, Blau),
# das von HTML und Qt gleichermassen verstanden wird.
# ──────────────────────────────────────────────────────────────────────────────

# Hauptfarben
COLOR_PRIMARY    = "#1a2744"   # Dunkelblau  – wird für Header und Sidebar verwendet
COLOR_SECONDARY  = "#e63946"   # Rot         – Akzentfarbe passend zum Radsport-Thema
COLOR_ACCENT     = "#f4a261"   # Orange      – für Highlights und besondere Hinweise
COLOR_BG         = "#f0f2f5"   # Hellgrau    – Hintergrundfarbe des Hauptfensters
COLOR_WHITE      = "#ffffff"   # Reines Weiß – für Karten und helle Flächen
COLOR_CARD       = "#ffffff"   # Weiß        – Hintergrund von Karten-Widgets
COLOR_TEXT       = "#1d1d1d"   # Fast Schwarz – Standardfarbe für normalen Text
COLOR_TEXT_LIGHT = "#6c757d"   # Mittelgrau  – für Beschriftungen und Hinweistext
COLOR_SUCCESS    = "#2ecc71"   # Grün        – signalisiert Erfolg (z. B. "Geliefert")
COLOR_WARNING    = "#f39c12"   # Gelb/Orange – signalisiert eine Warnung
COLOR_DANGER     = "#e74c3c"   # Rot         – signalisiert einen Fehler oder gefährliche Aktion
COLOR_INFO       = "#3498db"   # Blau        – signalisiert eine Information
COLOR_BORDER     = "#dee2e6"   # Hellgrau    – Rahmenfarbe für Eingabefelder und Karten

# ──────────────────────────────────────────────────────────────────────────────
# STATUS-FARBEN FÜR BESTELLUNGEN
# Ein Python-Dictionary ordnet jedem möglichen Bestellstatus eine Farbe zu.
# So kann die Anwendung einen Status-Text automatisch in der passenden Farbe
# anzeigen, indem sie STATUS_FARBEN["Neu"] aufruft.
# ──────────────────────────────────────────────────────────────────────────────

STATUS_FARBEN = {
    "Neu":             "#3498db",  # Blau    – neue Bestellung, noch nicht bearbeitet
    "In Bearbeitung":  "#f39c12",  # Orange  – Bestellung wird gerade bearbeitet
    "Versendet":       "#9b59b6",  # Lila    – Ware wurde zum Versand übergeben
    "Geliefert":       "#2ecc71",  # Grün    – Ware beim Kunden angekommen
    "Storniert":       "#e74c3c",  # Rot     – Bestellung wurde abgebrochen
    "Zurückgegeben":   "#95a5a6",  # Grau    – Ware wurde vom Kunden zurückgeschickt
}

# ──────────────────────────────────────────────────────────────────────────────
# ZAHLUNGS-FARBEN
# Analog zu den Bestellstatus wird auch jeder Zahlungsstatus farblich markiert.
# ──────────────────────────────────────────────────────────────────────────────

ZAHLUNG_FARBEN = {
    "Offen":       "#e74c3c",  # Rot    – Rechnung noch nicht bezahlt
    "Teilbezahlt": "#f39c12",  # Orange – nur ein Teil des Betrags wurde bezahlt
    "Bezahlt":     "#2ecc71",  # Grün   – Rechnung vollständig beglichen
    "Erstattet":   "#95a5a6",  # Grau   – Betrag wurde dem Kunden zurückerstattet
}

# ──────────────────────────────────────────────────────────────────────────────
# HAUPT-STYLESHEET (MAIN_STYLE)
# Dies ist ein sogenannter f-String (formatierter String).
# Die geschweiften Klammern {} werden von Python zur Laufzeit durch die oben
# definierten Farbkonstanten ersetzt, z. B. wird {COLOR_PRIMARY} zu "#1a2744".
# Die doppelten Klammern {{ }} sind kein Python-Code, sondern gehören zur
# Qt-CSS-Syntax und werden als einfache { } in den endgültigen String übernommen.
#
# Qt Stylesheets funktionieren sehr ähnlich wie CSS im Web:
# - Selektoren wie QMainWindow wählen einen Widget-Typ aus.
# - Selektoren wie #sidebar wählen ein Widget mit dem Objektnamen "sidebar" aus.
# - Pseudozustände wie :hover reagieren auf Mausbewegungen.
# ──────────────────────────────────────────────────────────────────────────────

MAIN_STYLE = f"""
/* ── Global ── */
/* Gilt für das Hauptfenster und alle Dialoge der Anwendung */
QMainWindow, QDialog {{
    background-color: {COLOR_BG};           /* Hintergrundfarbe: helles Grau */
    font-family: 'Segoe UI', Arial, sans-serif; /* Schriftart: modern und gut lesbar */
    font-size: 13px;                        /* Standardschriftgröße in Pixeln */
    color: {COLOR_TEXT};                    /* Standardtextfarbe: fast Schwarz */
}}

/* Basisstil für alle Qt-Widgets (Schaltflächen, Labels usw.) */
QWidget {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: {COLOR_TEXT};
}}

/* ── Sidebar Navigation ── */
/* Die Seitenleiste ist ein Widget mit dem Objektnamen "sidebar". */
/* min-width und max-width sind gleich – die Breite ist damit fest auf 220px fixiert. */
#sidebar {{
    background-color: {COLOR_PRIMARY};  /* Dunkelblauer Hintergrund */
    min-width: 220px;                   /* Mindestbreite = Maximalbreite → fixe Breite */
    max-width: 220px;
}}

/* Titel-Label ganz oben in der Sidebar (Firmenname) */
#sidebar_title {{
    color: {COLOR_WHITE};     /* Weißer Text auf dunklem Hintergrund */
    font-size: 16px;          /* Etwas größer als der Standard */
    font-weight: bold;        /* Fettdruck für den Firmentitel */
    padding: 8px 0;           /* Innenabstand: 8px oben/unten, 0px links/rechts */
}}

/* Untertitel unterhalb des Firmennamens (z. B. "Verwaltung") */
#sidebar_subtitle {{
    color: rgba(255,255,255,0.6); /* Halbtransparentes Weiß – dezenter Hinweistext */
    font-size: 10px;
    padding-bottom: 10px;
}}

/* Normaler (nicht aktiver) Navigationsbutton in der Sidebar */
#nav_btn {{
    background: transparent;           /* Kein Hintergrund – sieht wie ein Link aus */
    color: rgba(255,255,255,0.75);     /* Leicht transparentes Weiß */
    border: none;                      /* Kein Rahmen */
    border-radius: 8px;                /* Abgerundete Ecken */
    padding: 12px 16px;                /* Innenabstand: großzügig für einfachere Bedienung */
    text-align: left;                  /* Text linksbündig ausrichten */
    font-size: 13px;
    font-weight: 500;                  /* Medium-Schriftstärke (zwischen Normal und Fett) */
    margin: 2px 8px;                   /* Außenabstand: kleiner Abstand zwischen den Buttons */
}}

/* Hover-Effekt: Wenn die Maus über einen nicht-aktiven Button fährt */
#nav_btn:hover {{
    background-color: rgba(255,255,255,0.1); /* Leichter weißer Schimmer als Feedback */
    color: {COLOR_WHITE};                    /* Text wird reines Weiß */
}}

/* Aktiver Navigationsbutton – zeigt die aktuell geöffnete Seite an */
#nav_btn_active {{
    background-color: {COLOR_SECONDARY};  /* Roter Hintergrund hebt aktiven Button hervor */
    color: {COLOR_WHITE};
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;   /* Etwas fetter als der inaktive Button */
    margin: 2px 8px;
}}

/* ── Content Bereich ── */
/* Der Hauptbereich rechts neben der Sidebar */
#content_area {{
    background-color: {COLOR_BG};
    padding: 0;  /* Kein Innenabstand – die einzelnen Seiten verwalten ihren eigenen Abstand */
}}

/* ── Page Header ── */
/* Der weiße Kopfbereich jeder Seite mit Titel und Untertitel */
#page_header {{
    background-color: {COLOR_WHITE};
    border-bottom: 1px solid {COLOR_BORDER};  /* Dünne Trennlinie nach unten */
    padding: 16px 24px;                       /* Großzügiger Innenabstand */
}}

/* Großer Seitentitel, z. B. "Kunden" oder "Bestellungen" */
#page_title {{
    font-size: 22px;
    font-weight: 700;          /* Sehr fett (700 = Bold) */
    color: {COLOR_PRIMARY};    /* Dunkelblau passend zur Sidebar */
}}

/* Kleiner Hinweistext unterhalb des Titels */
#page_subtitle {{
    font-size: 12px;
    color: {COLOR_TEXT_LIGHT}; /* Grau – weniger auffällig als der Haupttitel */
}}

/* ── Karten / Panels ── */
/* Eine "Karte" ist ein weißes, abgerundetes Panel zur Gruppierung von Inhalten */
#card {{
    background-color: {COLOR_WHITE};
    border-radius: 12px;             /* Stärker abgerundet für einen modernen Look */
    border: 1px solid {COLOR_BORDER};
    padding: 20px;
}}

/* Statistik-Karte auf dem Dashboard (z. B. "Gesamtkundenzahl") */
#stat_card {{
    background-color: {COLOR_WHITE};
    border-radius: 12px;
    border: 1px solid {COLOR_BORDER};
    padding: 20px;
    min-width: 190px;  /* Mindestbreite damit die Karten nicht zu schmal werden */
}}

/* Die große Zahl auf einer Statistikkarte (z. B. "42") */
#stat_value {{
    font-size: 28px;       /* Groß und gut sichtbar */
    font-weight: 700;
    color: {COLOR_PRIMARY};
}}

/* Die Beschriftung unter der Zahl (z. B. "Kunden gesamt") */
#stat_label {{
    font-size: 12px;
    color: {COLOR_TEXT_LIGHT};
}}

/* ── Tabellen ── */
/* Stil für QTableWidget – wird für Kunden-, Artikel- und Bestelllisten verwendet */
QTableWidget {{
    background-color: {COLOR_WHITE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    gridline-color: #f1f3f4;               /* Sehr helle Gitterlinien zwischen Zellen */
    selection-background-color: #e8f0fe;   /* Hellblauer Hintergrund für ausgewählte Zeile */
    selection-color: {COLOR_TEXT};         /* Textfarbe bleibt dunkel, auch wenn markiert */
    alternate-background-color: #fafbfc;   /* Abwechselnde Zeilenhintergründe (Zebra-Muster) */
    font-size: 13px;
}}

/* Einzelne Tabellenzelle */
QTableWidget::item {{
    padding: 8px 12px;  /* Innenabstand macht die Zeilen luftiger und lesbarer */
    border: none;
}}

/* Ausgewählte Tabellenzelle */
QTableWidget::item:selected {{
    background-color: #dbeafe;  /* Etwas kräftigeres Blau wenn Zeile ausgewählt ist */
    color: {COLOR_TEXT};
}}

/* Spaltenkopf-Zellen der Tabelle */
QHeaderView::section {{
    background-color: {COLOR_PRIMARY};          /* Dunkelblauer Header – wie die Sidebar */
    color: {COLOR_WHITE};
    font-weight: 600;
    font-size: 12px;
    padding: 10px 12px;
    border: none;
    border-right: 1px solid rgba(255,255,255,0.1); /* Dünne halbdurchsichtige Trennlinie */
}}

/* Erste Spaltenüberschrift: linke obere Ecke abrunden */
QHeaderView::section:first {{
    border-top-left-radius: 8px;
}}

/* Letzte Spaltenüberschrift: rechte obere Ecke abrunden, rechte Trennlinie entfernen */
QHeaderView::section:last {{
    border-top-right-radius: 8px;
    border-right: none;
}}

/* ── Buttons ── */
/* Primärer Button – Hauptaktion auf einer Seite (z. B. "Speichern", "Neu anlegen") */
#btn_primary {{
    background-color: {COLOR_SECONDARY};  /* Rot – fällt sofort ins Auge */
    color: {COLOR_WHITE};
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
    min-width: 100px;  /* Verhindert, dass der Button bei kurzem Text zu schmal wird */
}}

/* Hover-Effekt: Button wird etwas dunkler wenn Maus drüber fährt */
#btn_primary:hover {{
    background-color: #c1121f;
}}

/* Pressed-Effekt: Button wird noch dunkler wenn er gedrückt wird */
#btn_primary:pressed {{
    background-color: #9e1a2a;
}}

/* Sekundärer Button – weniger wichtige Aktion (z. B. "Details anzeigen") */
#btn_secondary {{
    background-color: {COLOR_PRIMARY};  /* Dunkelblau – weniger auffällig als Rot */
    color: {COLOR_WHITE};
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
    min-width: 100px;
}}

/* Hover-Effekt für sekundären Button */
#btn_secondary:hover {{
    background-color: #263561;  /* Etwas helleres Blau */
}}

/* Gefahr-Button – für destruktive Aktionen wie "Löschen" */
/* Outline-Stil (transparenter Hintergrund, farbiger Rahmen) signalisiert: Vorsicht! */
#btn_danger {{
    background-color: transparent;
    color: {COLOR_DANGER};             /* Roter Text */
    border: 1.5px solid {COLOR_DANGER}; /* Roter Rahmen */
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 12px;
}}

/* Hover: Button füllt sich rot – deutliche Warnung vor der Aktion */
#btn_danger:hover {{
    background-color: {COLOR_DANGER};
    color: {COLOR_WHITE};
}}

/* Icon-Button – für Aktionen mit Symbol (z. B. "Exportieren", "Drucken") */
#btn_icon {{
    background-color: transparent;
    border: 1.5px solid #555555;  /* Grauer Rahmen – neutraler Stil */
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 13px;
    color: #222222;
    min-width: 80px;
}}

/* Hover: Rahmen und Text werden dunkelblau (passend zur Primärfarbe) */
#btn_icon:hover {{
    background-color: {COLOR_BG};
    border-color: {COLOR_PRIMARY};
    color: {COLOR_PRIMARY};
}}

/* ── Eingabefelder ── */
/* Gemeinsamer Stil für alle Eingabe-Widgets:
   QLineEdit       = einzeiliges Textfeld
   QTextEdit       = mehrzeiliges Textfeld
   QComboBox       = Auswahlmenü (Dropdown)
   QSpinBox        = Ganzzahl-Eingabe mit Pfeilen
   QDoubleSpinBox  = Dezimalzahl-Eingabe mit Pfeilen
   QDateEdit       = Datumseingabe */
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    border: 1.5px solid {COLOR_BORDER};          /* Grauer Rahmen im Normalzustand */
    border-radius: 8px;
    padding: 8px 12px;
    background-color: {COLOR_WHITE};
    font-size: 13px;
    color: {COLOR_TEXT};
    selection-background-color: #dbeafe;         /* Hellblau wenn Text markiert ist */
}}

/* Fokus-Stil: Rahmen wird rot wenn das Feld aktiv ist (Nutzer tippt gerade) */
QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
    border-color: {COLOR_SECONDARY};  /* Roter Rahmen – zeigt: dieses Feld ist aktiv */
    outline: none;                    /* Browser-Standard-Outline entfernen */
}}

/* Schreibgeschützte Felder (read-only) erscheinen grauer – man erkennt: nicht editierbar */
QLineEdit:read-only {{
    background-color: #f8f9fa;
    color: {COLOR_TEXT_LIGHT};
}}

/* ── ComboBox (Dropdown) Detailstyling ── */
/* Der Pfeil-Bereich rechts in der ComboBox */
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

/* Eigener Pfeil statt des System-Standard-Pfeils:
   Dreieck wird durch Null-Breite-Rahmen-Trick erzeugt (CSS-Dreieck-Technik) */
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;    /* Linker Rand transparent = linke Dreieckseite */
    border-right: 5px solid transparent;   /* Rechter Rand transparent = rechte Dreieckseite */
    border-top: 6px solid {COLOR_TEXT_LIGHT}; /* Oberer Rand sichtbar = Dreieckspitze nach unten */
    margin-right: 8px;
}}

/* Die aufgeklappte Liste der ComboBox */
QComboBox QAbstractItemView {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    background: {COLOR_WHITE};
    selection-background-color: #dbeafe;  /* Blau wenn ein Eintrag ausgewählt wird */
}}

/* ── Suchleiste ── */
/* Spezieller Stil für das Suchfeld – mit mehr Rundung (border-radius: 20px = Pille) */
#search_input {{
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 20px;                  /* Stark abgerundet → "Pill"-Form */
    padding: 8px 16px 8px 36px;          /* Links 36px Platz für ein Such-Icon */
    background-color: {COLOR_WHITE};
    font-size: 13px;
    min-width: 260px;
}}

/* Fokus-Rahmen wird auch hier rot */
#search_input:focus {{
    border-color: {COLOR_SECONDARY};
}}

/* ── Labels ── */
/* Formular-Beschriftungen (z. B. "VORNAME:", "E-MAIL:") */
#label_form {{
    font-weight: 600;
    font-size: 12px;
    color: {COLOR_TEXT_LIGHT};   /* Grau – dezenter als Pflichtfelder */
    text-transform: uppercase;   /* Automatisch in Großbuchstaben umwandeln */
}}

/* ── Tabs ── */
/* Der Rahmen des Tab-Containers */
QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    background: {COLOR_WHITE};
}}

/* Einzelner Tab-Reiter im Normalzustand */
QTabBar::tab {{
    background: transparent;
    color: {COLOR_TEXT_LIGHT};            /* Grau – nicht ausgewählte Tabs sind dezent */
    padding: 10px 20px;
    border: none;
    border-bottom: 2px solid transparent; /* Unsichtbare Linie – Platz für aktiven Unterstrich */
    font-size: 13px;
    font-weight: 500;
}}

/* Aktiver Tab – durch roten Unterstrich hervorgehoben */
QTabBar::tab:selected {{
    color: {COLOR_SECONDARY};                          /* Text wird rot */
    border-bottom: 2px solid {COLOR_SECONDARY};        /* Roter Unterstrich = aktiver Reiter */
    font-weight: 600;
}}

/* Hover auf einem nicht ausgewählten Tab – leichter Hintergrund als Feedback */
QTabBar::tab:hover:!selected {{
    color: {COLOR_TEXT};
    background: rgba(0,0,0,0.03);  /* Kaum sichtbarer dunkler Schimmer */
}}

/* ── Scrollbars ── */
/* Vertikale Scrollbar – schmaler moderner Stil */
QScrollBar:vertical {{
    background: {COLOR_BG};
    width: 8px;          /* Schmal – nimmt wenig Platz weg */
    border-radius: 4px;
}}
/* Der greifbare Scrollbalken (Thumb) */
QScrollBar::handle:vertical {{
    background: #c4c9d4;
    border-radius: 4px;
    min-height: 30px;    /* Mindesthöhe damit man ihn noch gut greifen kann */
}}
/* Hover auf dem Scrollbalken – wird etwas dunkler */
QScrollBar::handle:vertical:hover {{
    background: #9ea5b0;
}}
/* Pfeile der Scrollbar verstecken (height: 0) – moderner Look ohne Pfeile */
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* Horizontale Scrollbar – analog zur vertikalen */
QScrollBar:horizontal {{
    background: {COLOR_BG};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: #c4c9d4;
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: #9ea5b0;
}}
/* Pfeile auch hier verstecken */
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Dialoge ── */
/* Separate Fenster (z. B. "Neuer Kunde", "Bestellung bearbeiten") */
QDialog {{
    background-color: {COLOR_WHITE};
    border-radius: 12px;
}}

/* ── Splitter ── */
/* Der Trennbalken zwischen zwei Bereichen (z. B. Liste und Detailansicht) */
QSplitter::handle {{
    background: {COLOR_BORDER};  /* Helle Linie als Trennungselement */
    width: 1px;                  /* Sehr dünn – kaum sichtbar */
}}

/* ── Tooltips ── */
/* Kleine Hinweistexte die erscheinen, wenn die Maus über ein Element fährt */
QToolTip {{
    background-color: {COLOR_PRIMARY};  /* Dunkler Hintergrund = gut lesbar */
    color: {COLOR_WHITE};
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ── Statusbar ── */
/* Die Leiste am unteren Rand des Hauptfensters (zeigt z. B. Bereitschaftsmeldungen) */
QStatusBar {{
    background-color: {COLOR_PRIMARY};
    color: rgba(255,255,255,0.8);  /* Leicht transparentes Weiß – nicht zu grell */
    font-size: 12px;
    padding: 4px 12px;
}}

/* ── Message Boxes ── */
/* Systemnachrichten-Dialoge (z. B. Bestätigungs- oder Fehlermeldungen) */
QMessageBox {{
    background-color: {COLOR_WHITE};
}}
/* Buttons in Nachrichtendialogen erhalten den primären Button-Stil */
QMessageBox QPushButton {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_WHITE};
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
    min-width: 80px;
}}
QMessageBox QPushButton:hover {{
    background-color: #c1121f;
}}

/* ── CheckBox ── */
/* Ankreuzfelder (z. B. "Artikel aktiv?") */
QCheckBox {{
    spacing: 8px;  /* Abstand zwischen dem Kästchen und dem Beschriftungstext */
}}
/* Das eigentliche Häkchen-Kästchen */
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLOR_BORDER};
    border-radius: 4px;
    background: {COLOR_WHITE};
}}
/* Kästchen wenn es angehakt ist – roter Hintergrund passend zur Primärfarbe */
QCheckBox::indicator:checked {{
    background-color: {COLOR_SECONDARY};  /* Rotes Häkchen */
    border-color: {COLOR_SECONDARY};
}}
"""
