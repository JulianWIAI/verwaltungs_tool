"""
Radsport Koch GmbH – Datenbankmodul
Kapselt alle SQLite-Operationen.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "radsport_koch.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Datenbank initialisieren – Schema anlegen wenn noch nicht vorhanden."""
    conn = get_connection()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# Hilfsfunktionen
# ─────────────────────────────────────────────

def _next_nummer(prefix: str, tabelle: str, spalte: str) -> str:
    conn = get_connection()
    row = conn.execute(
        f"SELECT MAX(CAST(SUBSTR({spalte}, LENGTH(?) + 2) AS INTEGER)) FROM {tabelle} WHERE {spalte} LIKE ?",
        (prefix, f"{prefix}-%")
    ).fetchone()
    conn.close()
    naechste = (row[0] or 0) + 1
    return f"{prefix}-{naechste:05d}"


# ─────────────────────────────────────────────
# KUNDEN
# ─────────────────────────────────────────────

def get_alle_kunden(suche: str = "") -> list:
    conn = get_connection()
    if suche:
        s = f"%{suche}%"
        rows = conn.execute("""
            SELECT * FROM kunden
            WHERE vorname LIKE ? OR nachname LIKE ? OR kundennummer LIKE ?
               OR email LIKE ? OR ort LIKE ? OR telefon LIKE ?
            ORDER BY nachname, vorname
        """, (s, s, s, s, s, s)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM kunden ORDER BY nachname, vorname").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_kunde(kunde_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM kunden WHERE id = ?", (kunde_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def speichere_kunde(daten: dict) -> int:
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if daten.get("id"):
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
        return daten["id"]
    else:
        kundennummer = _next_nummer("K", "kunden", "kundennummer")
        cur = conn.execute("""
            INSERT INTO kunden (kundennummer, vorname, nachname, email, telefon,
            strasse, plz, ort, land, geburtsdatum, notizen)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (kundennummer, daten["vorname"], daten["nachname"], daten.get("email",""),
              daten.get("telefon",""), daten.get("strasse",""), daten.get("plz",""),
              daten.get("ort",""), daten.get("land","Deutschland"),
              daten.get("geburtsdatum",""), daten.get("notizen","")))
        conn.commit(); new_id = cur.lastrowid; conn.close()
        return new_id


def loesche_kunde(kunde_id: int) -> bool:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM kunden WHERE id = ?", (kunde_id,))
        conn.commit(); conn.close(); return True
    except sqlite3.IntegrityError:
        conn.close(); return False


# ─────────────────────────────────────────────
# ARTIKEL
# ─────────────────────────────────────────────

def get_alle_artikel(suche: str = "", nur_aktiv: bool = False) -> list:
    conn = get_connection()
    query = "SELECT * FROM v_artikel_uebersicht WHERE 1=1"
    params = []
    if nur_aktiv:
        query += " AND aktiv = 1"
    if suche:
        s = f"%{suche}%"
        query += " AND (bezeichnung LIKE ? OR artikelnummer LIKE ? OR hersteller LIKE ? OR kategorie LIKE ?)"
        params.extend([s, s, s, s])
    query += " ORDER BY bezeichnung"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_artikel(artikel_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM artikel WHERE id = ?", (artikel_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_kategorien() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM kategorien ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def speichere_artikel(daten: dict) -> int:
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if daten.get("id"):
        conn.execute("""
            UPDATE artikel SET bezeichnung=?, kategorie_id=?, beschreibung=?,
            einkaufspreis=?, verkaufspreis=?, mwst_satz=?, lagerbestand=?,
            mindestbestand=?, einheit=?, hersteller=?, lieferant=?, aktiv=?, geaendert_am=?
            WHERE id=?
        """, (daten["bezeichnung"], daten.get("kategorie_id"), daten.get("beschreibung",""),
              float(daten.get("einkaufspreis",0)), float(daten.get("verkaufspreis",0)),
              float(daten.get("mwst_satz",19)), int(daten.get("lagerbestand",0)),
              int(daten.get("mindestbestand",5)), daten.get("einheit","Stück"),
              daten.get("hersteller",""), daten.get("lieferant",""),
              int(daten.get("aktiv",1)), now, daten["id"]))
        conn.commit(); conn.close()
        return daten["id"]
    else:
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
    conn = get_connection()
    try:
        conn.execute("DELETE FROM artikel WHERE id = ?", (artikel_id,))
        conn.commit(); conn.close(); return True
    except sqlite3.IntegrityError:
        conn.close(); return False


# ─────────────────────────────────────────────
# BESTELLUNGEN
# ─────────────────────────────────────────────

def get_alle_bestellungen(suche: str = "", status: str = "") -> list:
    conn = get_connection()
    query = "SELECT * FROM v_bestellungen_uebersicht WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if suche:
        s = f"%{suche}%"
        query += " AND (bestellnummer LIKE ? OR kunde_name LIKE ? OR kundennummer LIKE ?)"
        params.extend([s, s, s])
    query += " ORDER BY bestelldatum DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_bestellung(bestell_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM v_bestellungen_uebersicht WHERE id = ?", (bestell_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_bestellpositionen(bestell_id: int) -> list:
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
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        if daten.get("id"):
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
            conn.execute("DELETE FROM bestellpositionen WHERE bestellung_id = ?", (bestell_id,))
        else:
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
            bestell_id = cur.lastrowid

        for i, pos in enumerate(positionen, 1):
            conn.execute("""
                INSERT INTO bestellpositionen
                (bestellung_id, artikel_id, menge, einzelpreis, mwst_satz, rabatt_prozent, position_nr)
                VALUES (?,?,?,?,?,?,?)
            """, (bestell_id, pos["artikel_id"], int(pos["menge"]),
                  float(pos["einzelpreis"]), float(pos.get("mwst_satz",19)),
                  float(pos.get("rabatt_prozent",0)), i))

        # Lagerbestand aktualisieren (nur bei neuer Bestellung)
        if not daten.get("id"):
            for pos in positionen:
                conn.execute(
                    "UPDATE artikel SET lagerbestand = lagerbestand - ? WHERE id = ?",
                    (int(pos["menge"]), pos["artikel_id"])
                )

        conn.commit(); conn.close()
        return bestell_id
    except Exception as e:
        conn.rollback(); conn.close()
        raise e


def update_bestellstatus(bestell_id: int, status: str, zahlungsstatus: str = None):
    conn = get_connection()
    if zahlungsstatus:
        conn.execute(
            "UPDATE bestellungen SET status=?, zahlungsstatus=?, geaendert_am=? WHERE id=?",
            (status, zahlungsstatus, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), bestell_id)
        )
    else:
        conn.execute(
            "UPDATE bestellungen SET status=?, geaendert_am=? WHERE id=?",
            (status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), bestell_id)
        )
    conn.commit(); conn.close()


def loesche_bestellung(bestell_id: int) -> bool:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM bestellungen WHERE id = ?", (bestell_id,))
        conn.commit(); conn.close(); return True
    except Exception:
        conn.close(); return False


# ─────────────────────────────────────────────
# DASHBOARD / STATISTIK
# ─────────────────────────────────────────────

def get_dashboard_stats() -> dict:
    conn = get_connection()
    stats = {}
    stats["kunden_gesamt"] = conn.execute("SELECT COUNT(*) FROM kunden").fetchone()[0]
    stats["artikel_gesamt"] = conn.execute("SELECT COUNT(*) FROM artikel WHERE aktiv=1").fetchone()[0]
    stats["bestellungen_gesamt"] = conn.execute("SELECT COUNT(*) FROM bestellungen").fetchone()[0]
    stats["bestellungen_offen"] = conn.execute(
        "SELECT COUNT(*) FROM bestellungen WHERE status IN ('Neu','In Bearbeitung')").fetchone()[0]
    stats["umsatz_gesamt"] = conn.execute(
        "SELECT COALESCE(SUM(gesamtbetrag_brutto),0) FROM v_bestellungen_uebersicht "
        "WHERE status != 'Storniert'").fetchone()[0] or 0.0
    stats["umsatz_monat"] = conn.execute(
        "SELECT COALESCE(SUM(gesamtbetrag_brutto),0) FROM v_bestellungen_uebersicht "
        "WHERE strftime('%Y-%m', bestelldatum) = strftime('%Y-%m', 'now') "
        "AND status != 'Storniert'").fetchone()[0] or 0.0
    stats["nachbestellen"] = conn.execute(
        "SELECT COUNT(*) FROM artikel WHERE lagerbestand <= mindestbestand AND aktiv=1").fetchone()[0]
    # Letzte 6 Monate Umsatz
    rows = conn.execute("""
        SELECT strftime('%Y-%m', bestelldatum) as monat,
               ROUND(SUM(gesamtbetrag_brutto),2) as umsatz
        FROM v_bestellungen_uebersicht
        WHERE status != 'Storniert'
          AND bestelldatum >= date('now','-6 months')
        GROUP BY monat ORDER BY monat
    """).fetchall()
    stats["umsatz_verlauf"] = [dict(r) for r in rows]
    # Top Artikel
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
    # Status-Verteilung
    rows = conn.execute("""
        SELECT status, COUNT(*) as anzahl FROM bestellungen GROUP BY status
    """).fetchall()
    stats["status_verteilung"] = [dict(r) for r in rows]
    conn.close()
    return stats
