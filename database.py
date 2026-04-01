"""
Radsport Koch GmbH – Datenbankmodul
====================================
Dieses Modul kapselt alle direkten Zugriffe auf die SQLite-Datenbank.
"Kapseln" bedeutet: alle anderen Teile der Anwendung (z. B. die GUI-Fenster)
rufen nur die Funktionen hier auf – sie wissen nichts über SQL oder Datenbankdetails.
Dieses Muster nennt man "Data Access Layer" (Datenzugriffsschicht).

Enthaltene Bereiche:
- Datenbankverbindung und Initialisierung
- KUNDEN:      anlegen, lesen, aktualisieren, löschen
- ARTIKEL:     anlegen, lesen, aktualisieren, löschen
- BESTELLUNGEN: anlegen, lesen, aktualisieren, löschen
- DASHBOARD:   Statistiken und Kennzahlen für die Startseite

Verwendete Technologie:
- sqlite3: Python-Standardbibliothek für SQLite-Datenbanken (keine Installation nötig)
- SQLite:  Eine serverlose, dateibasierte Datenbank – ideal für Desktop-Anwendungen
"""

import sqlite3         # Python-Standardbibliothek für SQLite-Datenbankzugriff
import os              # Betriebssystemfunktionen, hier für Pfadoperationen
from datetime import datetime  # Datum und Uhrzeit für Zeitstempel (erstellt_am, geaendert_am)

# ──────────────────────────────────────────────────────────────────────────────
# DATEIPFADE
# __file__ ist eine Python-Sondervariable: sie enthält den Pfad der aktuellen
# .py-Datei. os.path.dirname() gibt nur das Verzeichnis zurück.
# os.path.join() setzt Verzeichnis und Dateiname plattformunabhängig zusammen
# (funktioniert unter Windows, Linux und macOS).
# ──────────────────────────────────────────────────────────────────────────────

# All runtime and schema data lives under the data/ subdirectory,
# keeping the project root clean and organised.
_BASE_DIR   = os.path.dirname(__file__)
DB_PATH     = os.path.join(_BASE_DIR, "data", "radsport_koch.db")
SCHEMA_PATH = os.path.join(_BASE_DIR, "data", "schema.sql")


def get_connection() -> sqlite3.Connection:
    """
    Erstellt und gibt eine neue Verbindung zur SQLite-Datenbank zurück.

    Konfiguration der Verbindung:
    - row_factory = sqlite3.Row:  Ergebniszeilen verhalten sich wie Dictionaries,
      d. h. man kann auf Spalten per Name zugreifen (row["vorname"] statt row[0]).
    - PRAGMA foreign_keys = ON:  Aktiviert die Fremdschlüssel-Prüfung in SQLite.
      Standardmässig ist diese in SQLite deaktiviert! Dadurch wird z. B.
      verhindert, dass ein Kunde gelöscht wird, der noch Bestellungen hat.

    Rückgabe:
        sqlite3.Connection – das Verbindungsobjekt zur Datenbank
    """
    conn = sqlite3.connect(DB_PATH)          # Verbindung zur Datenbankdatei öffnen
    conn.row_factory = sqlite3.Row           # Spaltenzugriff per Name ermöglichen
    conn.execute("PRAGMA foreign_keys = ON") # Fremdschlüssel-Validierung einschalten
    return conn


def init_db():
    """
    Initialisiert die Datenbank beim ersten Programmstart.

    Liest die SQL-Schema-Datei (schema.sql) ein und führt sie aus.
    Die Schema-Datei enthält CREATE TABLE IF NOT EXISTS Anweisungen,
    d. h. sie legt Tabellen nur an, wenn sie noch nicht existieren –
    bestehende Daten werden also nicht überschrieben.

    Diese Funktion wird typischerweise einmalig beim Programmstart aufgerufen.
    """
    conn = get_connection()
    # Schema-Datei im UTF-8-Format öffnen und den Inhalt lesen
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        # executescript() führt mehrere SQL-Anweisungen auf einmal aus
        conn.executescript(f.read())
    conn.commit()   # Änderungen dauerhaft in die Datei schreiben
    conn.close()    # Verbindung freigeben (wichtig: sonst bleibt die Datei gesperrt)


# ─────────────────────────────────────────────
# Hilfsfunktionen
# ─────────────────────────────────────────────

def _next_nummer(prefix: str, tabelle: str, spalte: str) -> str:
    """
    Generiert die nächste fortlaufende Nummer für Kunden, Artikel oder Bestellungen.

    Beispiele für generierte Nummern:
        K-00001, K-00002, ... (Kunden)
        ART-00001, ART-00002, ... (Artikel)
        B-00001, B-00002, ... (Bestellungen)

    Funktionsweise:
    1. In der Datenbank wird nach der höchsten bereits vorhandenen Nummer gesucht.
    2. Der numerische Teil wird extrahiert (z. B. aus "K-00042" → 42).
    3. Dieser Wert wird um 1 erhöht und als formatierter String zurückgegeben.

    Parameter:
        prefix  – Buchstabenpräfix, z. B. "K", "ART" oder "B"
        tabelle – Name der Datenbanktabelle, z. B. "kunden"
        spalte  – Name der Spalte mit der Nummer, z. B. "kundennummer"

    Rückgabe:
        str – die neue Nummer, z. B. "K-00043"
    """
    conn = get_connection()
    # SQL: Sucht den maximalen numerischen Anteil aller vorhandenen Nummern.
    # SUBSTR(...) schneidet den Präfix und den Bindestrich ab.
    # CAST(... AS INTEGER) wandelt den Textrest in eine Zahl um.
    # LIKE ? filtert nur Zeilen, die zum Präfix passen (z. B. "K-%").
    row = conn.execute(
        f"SELECT MAX(CAST(SUBSTR({spalte}, LENGTH(?) + 2) AS INTEGER)) FROM {tabelle} WHERE {spalte} LIKE ?",
        (prefix, f"{prefix}-%")
    ).fetchone()
    conn.close()
    # row[0] ist der höchste gefundene Wert; "or 0" verhindert einen Fehler wenn
    # die Tabelle noch leer ist (dann gibt MAX() None zurück).
    naechste = (row[0] or 0) + 1
    # :05d formatiert die Zahl fünfstellig mit führenden Nullen, z. B. 1 → "00001"
    return f"{prefix}-{naechste:05d}"


# ─────────────────────────────────────────────
# KUNDEN
# ─────────────────────────────────────────────

def get_alle_kunden(suche: str = "") -> list:
    """
    Lädt alle Kunden aus der Datenbank, optional gefiltert nach einem Suchbegriff.

    Der Suchbegriff wird in mehreren Feldern gleichzeitig gesucht (Vor- und
    Nachname, Kundennummer, E-Mail, Ort, Telefon). Das ermöglicht eine
    flexible Freitextsuche.

    Parameter:
        suche – optionaler Suchbegriff; wenn leer, werden alle Kunden geladen

    Rückgabe:
        list[dict] – Liste von Kunden-Dictionaries (ein Dict pro Kunde)
    """
    conn = get_connection()
    if suche:
        # Suchbegriff mit %-Platzhaltern umgeben → LIKE-Suche findet Teilübereinstimmungen
        # z. B. suche="mül" findet "Müller", "Müllensiefen" usw.
        s = f"%{suche}%"
        rows = conn.execute("""
            SELECT * FROM kunden
            WHERE vorname LIKE ? OR nachname LIKE ? OR kundennummer LIKE ?
               OR email LIKE ? OR ort LIKE ? OR telefon LIKE ?
            ORDER BY nachname, vorname
        """, (s, s, s, s, s, s)).fetchall()
    else:
        # Kein Suchbegriff → alle Kunden laden, alphabetisch nach Name sortiert
        rows = conn.execute("SELECT * FROM kunden ORDER BY nachname, vorname").fetchall()
    conn.close()
    # sqlite3.Row-Objekte in normale Python-Dictionaries umwandeln
    # (einfacher zu verarbeiten in der GUI)
    return [dict(r) for r in rows]


def get_kunde(kunde_id: int) -> dict | None:
    """
    Lädt einen einzelnen Kunden anhand seiner Datenbank-ID.

    Parameter:
        kunde_id – numerische ID des Kunden (Primärschlüssel in der DB-Tabelle)

    Rückgabe:
        dict  – Kundendaten als Dictionary, wenn der Kunde gefunden wurde
        None  – wenn kein Kunde mit dieser ID existiert
    """
    conn = get_connection()
    # Parameterübergabe mit ? schützt vor SQL-Injection-Angriffen
    row = conn.execute("SELECT * FROM kunden WHERE id = ?", (kunde_id,)).fetchone()
    conn.close()
    # Ternärer Ausdruck: gibt dict(row) zurück wenn row nicht None ist, sonst None
    return dict(row) if row else None


def speichere_kunde(daten: dict) -> int:
    """
    Speichert einen Kunden in der Datenbank – entweder als neuer Eintrag (INSERT)
    oder als Aktualisierung eines bestehenden (UPDATE).

    Die Entscheidung zwischen INSERT und UPDATE trifft die Funktion selbst:
    - Ist "id" im daten-Dictionary vorhanden → bestehenden Kunden aktualisieren
    - Ist "id" nicht vorhanden → neuen Kunden anlegen

    Bei einem neuen Kunden wird automatisch eine Kundennummer generiert (K-00001 usw.)
    und ein Zeitstempel für "erstellt_am" gesetzt.

    Parameter:
        daten – Dictionary mit Kundendaten; muss mindestens "vorname" und "nachname"
                enthalten; optionale Felder erhalten Standardwerte über dict.get()

    Rückgabe:
        int – die ID des gespeicherten Kunden (bei UPDATE: vorhandene ID;
              bei INSERT: die neu vergebene Datenbank-ID)
    """
    conn = get_connection()
    # Aktuellen Zeitstempel im Format "JJJJ-MM-TT HH:MM:SS" erzeugen
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if daten.get("id"):
        # ── UPDATE: bestehender Kunde ──
        # Alle Felder außer kundennummer und erstellt_am werden überschrieben.
        # geaendert_am wird auf den aktuellen Zeitstempel gesetzt.
        conn.execute("""
            UPDATE kunden SET vorname=?, nachname=?, email=?, telefon=?,
            strasse=?, plz=?, ort=?, land=?, geburtsdatum=?, notizen=?, geaendert_am=?
            WHERE id=?
        """, (daten["vorname"], daten["nachname"], daten.get("email",""),
              daten.get("telefon",""), daten.get("strasse",""), daten.get("plz",""),
              daten.get("ort",""), daten.get("land","Deutschland"),
              daten.get("geburtsdatum",""), daten.get("notizen",""),
              now, daten["id"]))
        conn.commit(); conn.close()
        return daten["id"]  # Vorhandene ID zurückgeben
    else:
        # ── INSERT: neuer Kunde ──
        # Neue eindeutige Kundennummer generieren (z. B. "K-00007")
        kundennummer = _next_nummer("K", "kunden", "kundennummer")
        # Datensatz einfügen; fehlende Felder erhalten leere Strings als Standard
        cur = conn.execute("""
            INSERT INTO kunden (kundennummer, vorname, nachname, email, telefon,
            strasse, plz, ort, land, geburtsdatum, notizen)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (kundennummer, daten["vorname"], daten["nachname"], daten.get("email",""),
              daten.get("telefon",""), daten.get("strasse",""), daten.get("plz",""),
              daten.get("ort",""), daten.get("land","Deutschland"),
              daten.get("geburtsdatum",""), daten.get("notizen","")))
        conn.commit()
        new_id = cur.lastrowid  # lastrowid: die automatisch vergebene ID des neuen Datensatzes
        conn.close()
        return new_id


def loesche_kunde(kunde_id: int) -> bool:
    """
    Löscht einen Kunden aus der Datenbank.

    Scheitert das Löschen aufgrund eines Fremdschlüssel-Konflikts (d. h. der Kunde
    hat noch verknüpfte Bestellungen), gibt die Funktion False zurück, anstatt
    einen Fehler zu werfen. So kann die GUI dem Nutzer eine verständliche
    Fehlermeldung anzeigen.

    Parameter:
        kunde_id – die Datenbank-ID des zu löschenden Kunden

    Rückgabe:
        True  – Löschen erfolgreich
        False – Löschen fehlgeschlagen (z. B. wegen vorhandener Bestellungen)
    """
    conn = get_connection()
    try:
        conn.execute("DELETE FROM kunden WHERE id = ?", (kunde_id,))
        conn.commit(); conn.close(); return True
    except sqlite3.IntegrityError:
        # IntegrityError: SQLite meldet einen Fremdschlüsselverstoß
        # (PRAGMA foreign_keys = ON aus get_connection() ist hier aktiv)
        conn.close(); return False


# ─────────────────────────────────────────────
# ARTIKEL
# ─────────────────────────────────────────────

def get_alle_artikel(suche: str = "", nur_aktiv: bool = False) -> list:
    """
    Lädt alle Artikel aus der Datenbank-View v_artikel_uebersicht.

    Die View enthält bereits berechnete und zusammengeführte Felder
    (z. B. Kategoriename statt nur Kategorie-ID).

    Parameter:
        suche     – optionaler Suchbegriff für Bezeichnung, Artikelnummer,
                    Hersteller oder Kategorie
        nur_aktiv – wenn True, werden nur aktive (nicht archivierte) Artikel
                    zurückgegeben

    Rückgabe:
        list[dict] – Liste der passenden Artikel
    """
    conn = get_connection()
    # Basisabfrage aus der View; "WHERE 1=1" ist ein Trick damit man später
    # beliebig viele "AND ..."-Bedingungen anhängen kann ohne Sonderfälle
    query = "SELECT * FROM v_artikel_uebersicht WHERE 1=1"
    params = []  # Parameter werden separat gesammelt (Schutz vor SQL-Injection)
    if nur_aktiv:
        # Filtert ausgeschiedene/deaktivierte Artikel heraus
        query += " AND aktiv = 1"
    if suche:
        s = f"%{suche}%"
        # Suche in mehreren Feldern gleichzeitig mit OR-Verknüpfung
        query += " AND (bezeichnung LIKE ? OR artikelnummer LIKE ? OR hersteller LIKE ? OR kategorie LIKE ?)"
        # extend() fügt alle vier Parameter der Liste hinzu (für die vier ?-Platzhalter)
        params.extend([s, s, s, s])
    query += " ORDER BY bezeichnung"  # Alphabetische Sortierung nach Artikelname
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_artikel(artikel_id: int) -> dict | None:
    """
    Lädt einen einzelnen Artikel anhand seiner Datenbank-ID.

    Hinweis: Es wird direkt aus der Basistabelle "artikel" gelesen (nicht aus
    der View), um alle Rohdaten (inkl. Fremdschlüssel wie kategorie_id) zu erhalten.

    Parameter:
        artikel_id – numerische ID des Artikels

    Rückgabe:
        dict  – Artikeldaten, wenn gefunden
        None  – wenn kein Artikel mit dieser ID existiert
    """
    conn = get_connection()
    row = conn.execute("SELECT * FROM artikel WHERE id = ?", (artikel_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_kategorien() -> list:
    """
    Lädt alle Produktkategorien aus der Datenbank.

    Kategorien werden in einem eigenen Formular-Dropdown verwendet,
    damit Artikel einer Kategorie zugeordnet werden können.

    Rückgabe:
        list[dict] – Liste aller Kategorien, sortiert nach Name
    """
    conn = get_connection()
    rows = conn.execute("SELECT * FROM kategorien ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def speichere_artikel(daten: dict) -> int:
    """
    Speichert einen Artikel in der Datenbank – INSERT oder UPDATE je nach Kontext.

    Zahlenfelder wie Preise und Bestände werden explizit in float bzw. int
    umgewandelt, um Typfehler zu vermeiden (GUI-Felder liefern oft Strings).

    Parameter:
        daten – Dictionary mit Artikeldaten; muss mindestens "bezeichnung" enthalten

    Rückgabe:
        int – ID des gespeicherten Artikels
    """
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if daten.get("id"):
        # ── UPDATE: bestehender Artikel ──
        conn.execute("""
            UPDATE artikel SET bezeichnung=?, kategorie_id=?, beschreibung=?,
            einkaufspreis=?, verkaufspreis=?, mwst_satz=?, lagerbestand=?,
            mindestbestand=?, einheit=?, hersteller=?, lieferant=?, aktiv=?, geaendert_am=?
            WHERE id=?
        """, (daten["bezeichnung"], daten.get("kategorie_id"), daten.get("beschreibung",""),
              float(daten.get("einkaufspreis",0)),   # float(): Preis als Dezimalzahl speichern
              float(daten.get("verkaufspreis",0)),
              float(daten.get("mwst_satz",19)),       # Standardmehrwertsteuer: 19 %
              int(daten.get("lagerbestand",0)),        # int(): Bestand ist eine ganze Zahl
              int(daten.get("mindestbestand",5)),      # Standardmindestbestand: 5 Stück
              daten.get("einheit","Stück"),
              daten.get("hersteller",""), daten.get("lieferant",""),
              int(daten.get("aktiv",1)),               # 1 = aktiv, 0 = deaktiviert
              now, daten["id"]))
        conn.commit(); conn.close()
        return daten["id"]
    else:
        # ── INSERT: neuer Artikel ──
        # Neue Artikelnummer generieren (z. B. "ART-00012")
        artikelnummer = _next_nummer("ART", "artikel", "artikelnummer")
        cur = conn.execute("""
            INSERT INTO artikel (artikelnummer, bezeichnung, kategorie_id, beschreibung,
            einkaufspreis, verkaufspreis, mwst_satz, lagerbestand, mindestbestand,
            einheit, hersteller, lieferant)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (artikelnummer, daten["bezeichnung"], daten.get("kategorie_id"),
              daten.get("beschreibung",""), float(daten.get("einkaufspreis",0)),
              float(daten.get("verkaufspreis",0)), float(daten.get("mwst_satz",19)),
              int(daten.get("lagerbestand",0)), int(daten.get("mindestbestand",5)),
              daten.get("einheit","Stück"), daten.get("hersteller",""),
              daten.get("lieferant","")))
        conn.commit(); new_id = cur.lastrowid; conn.close()
        return new_id


def loesche_artikel(artikel_id: int) -> bool:
    """
    Löscht einen Artikel aus der Datenbank.

    Kann fehlschlagen wenn der Artikel noch in Bestellpositionen referenziert wird
    (Fremdschlüsselschutz). In diesem Fall wird False zurückgegeben.

    Parameter:
        artikel_id – die Datenbank-ID des zu löschenden Artikels

    Rückgabe:
        True  – Löschen erfolgreich
        False – Löschen fehlgeschlagen (Artikel wird noch verwendet)
    """
    conn = get_connection()
    try:
        conn.execute("DELETE FROM artikel WHERE id = ?", (artikel_id,))
        conn.commit(); conn.close(); return True
    except sqlite3.IntegrityError:
        # Fremdschlüsselfehler: Artikel ist noch in mindestens einer Bestellposition vorhanden
        conn.close(); return False


# ─────────────────────────────────────────────
# BESTELLUNGEN
# ─────────────────────────────────────────────

def get_alle_bestellungen(suche: str = "", status: str = "") -> list:
    """
    Lädt alle Bestellungen aus der View v_bestellungen_uebersicht.

    Die View enthält zusammengeführte Daten aus mehreren Tabellen, z. B.
    den vollständigen Kundennamen und die berechneten Gesamtbeträge.

    Parameter:
        suche  – optionaler Suchbegriff (Bestellnummer, Kundenname, Kundennummer)
        status – optionaler Statusfilter, z. B. "Neu" oder "Geliefert"

    Rückgabe:
        list[dict] – Liste der gefundenen Bestellungen, neueste zuerst
    """
    conn = get_connection()
    query = "SELECT * FROM v_bestellungen_uebersicht WHERE 1=1"
    params = []
    if status:
        # Exakter Statusabgleich (kein LIKE – Status ist ein festgelegter Wert)
        query += " AND status = ?"
        params.append(status)
    if suche:
        s = f"%{suche}%"
        query += " AND (bestellnummer LIKE ? OR kunde_name LIKE ? OR kundennummer LIKE ?)"
        params.extend([s, s, s])
    # Neueste Bestellungen zuerst anzeigen (absteigend nach Datum)
    query += " ORDER BY bestelldatum DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_bestellung(bestell_id: int) -> dict | None:
    """
    Lädt eine einzelne Bestellung anhand ihrer Datenbank-ID.

    Verwendet die View v_bestellungen_uebersicht für vollständige Daten
    inklusive Kundennamen und berechneten Beträgen.

    Parameter:
        bestell_id – numerische ID der Bestellung

    Rückgabe:
        dict  – Bestelldaten, wenn gefunden
        None  – wenn keine Bestellung mit dieser ID existiert
    """
    conn = get_connection()
    row = conn.execute("SELECT * FROM v_bestellungen_uebersicht WHERE id = ?", (bestell_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_bestellpositionen(bestell_id: int) -> list:
    """
    Lädt alle Positionen (Einzelartikel) einer Bestellung.

    Eine Bestellung kann mehrere Positionen haben – z. B.:
        Pos. 1: 2x Fahrradsattel à 49,99 €
        Pos. 2: 1x Helm à 89,99 €

    Die Positionen werden per JOIN mit der Artikeltabelle verknüpft, um
    Bezeichnung, Artikelnummer und Einheit direkt verfügbar zu machen.

    Parameter:
        bestell_id – ID der Bestellung, deren Positionen geladen werden sollen

    Rückgabe:
        list[dict] – Liste der Bestellpositionen, sortiert nach Positionsnummer
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.*, a.bezeichnung, a.artikelnummer, a.einheit
        FROM bestellpositionen p
        JOIN artikel a ON p.artikel_id = a.id
        WHERE p.bestellung_id = ?
        ORDER BY p.position_nr
    """, (bestell_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def speichere_bestellung(daten: dict, positionen: list) -> int:
    """
    Speichert eine Bestellung und ihre Positionen in der Datenbank.

    Diese Funktion führt mehrere SQL-Operationen als eine Transaktion aus:
    1. Bestellung anlegen (INSERT) oder aktualisieren (UPDATE)
    2. Bei Update: alte Positionen löschen
    3. Alle Positionen neu eintragen
    4. Bei neuer Bestellung: Lagerbestand der bestellten Artikel reduzieren

    Eine Transaktion bedeutet: entweder werden ALLE Schritte ausgeführt,
    oder bei einem Fehler wird alles rückgängig gemacht (Rollback). So gibt
    es keine halbfertigen Datensätze in der Datenbank.

    Parameter:
        daten      – Dictionary mit Bestellkopfdaten (Kunde, Datum, Status usw.)
        positionen – Liste von Dictionaries; jede Position enthält artikel_id,
                     menge, einzelpreis und optional mwst_satz und rabatt_prozent

    Rückgabe:
        int – ID der gespeicherten Bestellung

    Wirft:
        Exception – bei Datenbankfehler (nach Rollback)
    """
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        if daten.get("id"):
            # ── UPDATE: bestehende Bestellung aktualisieren ──
            conn.execute("""
                UPDATE bestellungen SET kunden_id=?, lieferdatum=?, status=?,
                zahlungsart=?, zahlungsstatus=?, lieferadresse=?, rabatt_prozent=?,
                versandkosten=?, notizen=?, geaendert_am=?
                WHERE id=?
            """, (daten["kunden_id"], daten.get("lieferdatum",""),
                  daten.get("status","Neu"), daten.get("zahlungsart","Rechnung"),
                  daten.get("zahlungsstatus","Offen"), daten.get("lieferadresse",""),
                  float(daten.get("rabatt_prozent",0)), float(daten.get("versandkosten",0)),
                  daten.get("notizen",""), now, daten["id"]))
            bestell_id = daten["id"]
            # Alle alten Positionen löschen – sie werden gleich neu eingefügt
            # (einfachste Strategie: löschen und neu schreiben statt einzeln vergleichen)
            conn.execute("DELETE FROM bestellpositionen WHERE bestellung_id = ?", (bestell_id,))
        else:
            # ── INSERT: neue Bestellung anlegen ──
            bestellnummer = _next_nummer("B", "bestellungen", "bestellnummer")
            cur = conn.execute("""
                INSERT INTO bestellungen (bestellnummer, kunden_id, lieferdatum, status,
                zahlungsart, zahlungsstatus, lieferadresse, rabatt_prozent, versandkosten, notizen)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (bestellnummer, daten["kunden_id"], daten.get("lieferdatum",""),
                  daten.get("status","Neu"), daten.get("zahlungsart","Rechnung"),
                  daten.get("zahlungsstatus","Offen"), daten.get("lieferadresse",""),
                  float(daten.get("rabatt_prozent",0)), float(daten.get("versandkosten",0)),
                  daten.get("notizen","")))
            bestell_id = cur.lastrowid  # ID der soeben eingefügten Bestellung

        # ── Positionen einfügen ──
        # enumerate(positionen, 1): gibt Paare (1, pos1), (2, pos2) usw. zurück
        # Die 1 bedeutet: die Zählung beginnt bei 1 statt bei 0
        for i, pos in enumerate(positionen, 1):
            conn.execute("""
                INSERT INTO bestellpositionen
                (bestellung_id, artikel_id, menge, einzelpreis, mwst_satz, rabatt_prozent, position_nr)
                VALUES (?,?,?,?,?,?,?)
            """, (bestell_id, pos["artikel_id"], int(pos["menge"]),
                  float(pos["einzelpreis"]), float(pos.get("mwst_satz",19)),
                  float(pos.get("rabatt_prozent",0)), i))  # i = Positionsnummer (1, 2, 3...)

        # Lagerbestand aktualisieren (nur bei neuer Bestellung)
        # Bei einer Aktualisierung wird der Bestand NICHT nochmal reduziert,
        # da er bereits bei der ursprünglichen Bestellung angepasst wurde.
        if not daten.get("id"):
            for pos in positionen:
                # Lagerbestand um die bestellte Menge verringern
                conn.execute(
                    "UPDATE artikel SET lagerbestand = lagerbestand - ? WHERE id = ?",
                    (int(pos["menge"]), pos["artikel_id"])
                )

        conn.commit(); conn.close()
        return bestell_id
    except Exception as e:
        # Bei einem Fehler: alle Änderungen dieser Transaktion rückgängig machen
        conn.rollback(); conn.close()
        raise e  # Fehler weiterwerfen damit die GUI ihn anzeigen kann


def update_bestellstatus(bestell_id: int, status: str, zahlungsstatus: str = None):
    """
    Aktualisiert nur den Status (und optional den Zahlungsstatus) einer Bestellung.

    Diese schnelle Update-Funktion wird verwendet wenn nur der Status geändert
    wird (z. B. von "Neu" auf "In Bearbeitung"), ohne die gesamte Bestellung
    neu zu speichern.

    Parameter:
        bestell_id     – ID der zu aktualisierenden Bestellung
        status         – neuer Bestellstatus (z. B. "Versendet", "Geliefert")
        zahlungsstatus – optionaler neuer Zahlungsstatus (z. B. "Bezahlt");
                         wenn None, wird der Zahlungsstatus nicht verändert
    """
    conn = get_connection()
    if zahlungsstatus:
        # Beide Status und Zeitstempel gleichzeitig aktualisieren
        conn.execute(
            "UPDATE bestellungen SET status=?, zahlungsstatus=?, geaendert_am=? WHERE id=?",
            (status, zahlungsstatus, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), bestell_id)
        )
    else:
        # Nur den Bestellstatus aktualisieren, Zahlungsstatus bleibt unberührt
        conn.execute(
            "UPDATE bestellungen SET status=?, geaendert_am=? WHERE id=?",
            (status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), bestell_id)
        )
    conn.commit(); conn.close()


def loesche_bestellung(bestell_id: int) -> bool:
    """
    Löscht eine Bestellung aus der Datenbank.

    Dank "ON DELETE CASCADE" in der Datenbankdefinition werden beim Löschen
    einer Bestellung auch alle zugehörigen Bestellpositionen automatisch
    mit gelöscht.

    Hinweis: Der Lagerbestand wird beim Löschen einer Bestellung NICHT
    wiederhergestellt. Sollte das gewünscht sein, müsste dies separat
    implementiert werden.

    Parameter:
        bestell_id – ID der zu löschenden Bestellung

    Rückgabe:
        True  – Löschen erfolgreich
        False – Löschen fehlgeschlagen (allgemeiner Fehler)
    """
    conn = get_connection()
    try:
        conn.execute("DELETE FROM bestellungen WHERE id = ?", (bestell_id,))
        conn.commit(); conn.close(); return True
    except Exception:
        # Breiter Exception-Catch: Bestellungen können aus verschiedenen Gründen
        # nicht löschbar sein (z. B. Datenbanksperre)
        conn.close(); return False


# ─────────────────────────────────────────────
# DASHBOARD / STATISTIK
# ─────────────────────────────────────────────

def get_dashboard_stats() -> dict:
    """
    Sammelt alle Kennzahlen und Statistiken für die Dashboard-Startseite.

    Führt mehrere separate SQL-Abfragen aus und fasst die Ergebnisse in
    einem einzigen Dictionary zusammen. Das Dictionary wird dann von der
    Dashboard-Seite verwendet um die Statistik-Karten und Diagramme zu befüllen.

    Enthaltene Kennzahlen:
        kunden_gesamt      – Gesamtanzahl aller Kunden
        artikel_gesamt     – Anzahl aktiver (nicht archivierter) Artikel
        bestellungen_gesamt – Gesamtanzahl aller Bestellungen
        bestellungen_offen  – Bestellungen die noch bearbeitet werden müssen
        umsatz_gesamt      – Gesamtumsatz (ohne stornierte Bestellungen)
        umsatz_monat       – Umsatz des aktuellen Monats
        nachbestellen      – Anzahl Artikel deren Bestand unter Mindestbestand liegt
        umsatz_verlauf     – Monatlicher Umsatz der letzten 6 Monate (für Diagramm)
        top_artikel        – Die 5 umsatzstärksten Artikel
        status_verteilung  – Anzahl Bestellungen pro Status (für Diagramm)

    Rückgabe:
        dict – Dictionary mit allen oben genannten Schlüsseln
    """
    conn = get_connection()
    stats = {}  # Leeres Dictionary; wird Schritt für Schritt befüllt

    # Gesamtanzahl aller Kunden (fetchone()[0] = erste Spalte der ersten Zeile = die Zahl)
    stats["kunden_gesamt"] = conn.execute("SELECT COUNT(*) FROM kunden").fetchone()[0]

    # Nur aktive Artikel zählen (aktiv=1 bedeutet: nicht archiviert)
    stats["artikel_gesamt"] = conn.execute("SELECT COUNT(*) FROM artikel WHERE aktiv=1").fetchone()[0]

    # Alle Bestellungen unabhängig vom Status zählen
    stats["bestellungen_gesamt"] = conn.execute("SELECT COUNT(*) FROM bestellungen").fetchone()[0]

    # Offene Bestellungen = Status ist "Neu" oder "In Bearbeitung"
    stats["bestellungen_offen"] = conn.execute(
        "SELECT COUNT(*) FROM bestellungen WHERE status IN ('Neu','In Bearbeitung')").fetchone()[0]

    # Gesamtumsatz: Summe aller Bruttobeträge, stornierte Bestellungen ausschliessen
    # COALESCE(SUM(...), 0) verhindert NULL wenn noch keine Bestellungen vorhanden sind
    stats["umsatz_gesamt"] = conn.execute(
        "SELECT COALESCE(SUM(gesamtbetrag_brutto),0) FROM v_bestellungen_uebersicht "
        "WHERE status != 'Storniert'").fetchone()[0] or 0.0

    # Umsatz des aktuellen Monats:
    # strftime('%Y-%m', ...) extrahiert Jahr und Monat, z. B. "2026-03"
    # 'now' ist ein SQLite-Schlüsselwort für das aktuelle Datum
    stats["umsatz_monat"] = conn.execute(
        "SELECT COALESCE(SUM(gesamtbetrag_brutto),0) FROM v_bestellungen_uebersicht "
        "WHERE strftime('%Y-%m', bestelldatum) = strftime('%Y-%m', 'now') "
        "AND status != 'Storniert'").fetchone()[0] or 0.0

    # Artikel die nachbestellt werden müssen: Lagerbestand <= Mindestbestand
    stats["nachbestellen"] = conn.execute(
        "SELECT COUNT(*) FROM artikel WHERE lagerbestand <= mindestbestand AND aktiv=1").fetchone()[0]

    # Letzte 6 Monate Umsatz (für ein Linien- oder Balkendiagramm)
    # GROUP BY monat: fasst alle Bestellungen eines Monats zusammen
    # date('now','-6 months'): Datum von vor 6 Monaten berechnen
    rows = conn.execute("""
        SELECT strftime('%Y-%m', bestelldatum) as monat,
               ROUND(SUM(gesamtbetrag_brutto),2) as umsatz
        FROM v_bestellungen_uebersicht
        WHERE status != 'Storniert'
          AND bestelldatum >= date('now','-6 months')
        GROUP BY monat ORDER BY monat
    """).fetchall()
    stats["umsatz_verlauf"] = [dict(r) for r in rows]

    # Top Artikel: Die 5 Artikel mit dem höchsten Gesamtumsatz
    # JOIN verknüpft die Bestellpositionen-Tabelle mit Artikel- und Bestellungstabelle
    rows = conn.execute("""
        SELECT a.bezeichnung, SUM(p.menge) as verkauft,
               ROUND(SUM(p.menge * p.einzelpreis),2) as umsatz
        FROM bestellpositionen p
        JOIN artikel a ON p.artikel_id = a.id
        JOIN bestellungen b ON p.bestellung_id = b.id
        WHERE b.status != 'Storniert'
        GROUP BY a.id ORDER BY umsatz DESC LIMIT 5
    """).fetchall()
    stats["top_artikel"] = [dict(r) for r in rows]

    # Status-Verteilung: Wie viele Bestellungen gibt es je Status?
    # (Für ein Kuchendiagramm oder eine Legende auf dem Dashboard)
    rows = conn.execute("""
        SELECT status, COUNT(*) as anzahl FROM bestellungen GROUP BY status
    """).fetchall()
    stats["status_verteilung"] = [dict(r) for r in rows]

    conn.close()
    return stats  # Fertiges Dictionary mit allen Statistiken zurückgeben
