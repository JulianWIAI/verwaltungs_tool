-- ============================================================
-- Radsport Koch GmbH – Datenbankschema
-- Erstellt: 2025
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- Kunden
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kunden (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    kundennummer    TEXT    UNIQUE NOT NULL,
    vorname         TEXT    NOT NULL,
    nachname        TEXT    NOT NULL,
    email           TEXT,
    telefon         TEXT,
    strasse         TEXT,
    plz             TEXT,
    ort             TEXT,
    land            TEXT    DEFAULT 'Deutschland',
    geburtsdatum    TEXT,
    notizen         TEXT,
    erstellt_am     TEXT    DEFAULT (datetime('now','localtime')),
    geaendert_am    TEXT    DEFAULT (datetime('now','localtime'))
);

-- ------------------------------------------------------------
-- Kategorien für Artikel
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kategorien (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT    UNIQUE NOT NULL,
    farbe   TEXT    DEFAULT '#3498db'
);

-- Standardkategorien
INSERT OR IGNORE INTO kategorien (name, farbe) VALUES
    ('Fahrräder',       '#e74c3c'),
    ('E-Bikes',         '#2ecc71'),
    ('Zubehör',         '#3498db'),
    ('Bekleidung',      '#9b59b6'),
    ('Ersatzteile',     '#f39c12'),
    ('Helme',           '#1abc9c'),
    ('Werkzeug',        '#95a5a6');

-- ------------------------------------------------------------
-- Artikel / Produkte
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS artikel (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    artikelnummer   TEXT    UNIQUE NOT NULL,
    bezeichnung     TEXT    NOT NULL,
    kategorie_id    INTEGER REFERENCES kategorien(id) ON DELETE SET NULL,
    beschreibung    TEXT,
    einkaufspreis   REAL    DEFAULT 0.0,
    verkaufspreis   REAL    DEFAULT 0.0,
    mwst_satz       REAL    DEFAULT 19.0,
    lagerbestand    INTEGER DEFAULT 0,
    mindestbestand  INTEGER DEFAULT 5,
    einheit         TEXT    DEFAULT 'Stück',
    hersteller      TEXT,
    lieferant       TEXT,
    aktiv           INTEGER DEFAULT 1,
    erstellt_am     TEXT    DEFAULT (datetime('now','localtime')),
    geaendert_am    TEXT    DEFAULT (datetime('now','localtime'))
);

-- ------------------------------------------------------------
-- Bestellungen (Kopf)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bestellungen (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    bestellnummer   TEXT    UNIQUE NOT NULL,
    kunden_id       INTEGER NOT NULL REFERENCES kunden(id) ON DELETE RESTRICT,
    bestelldatum    TEXT    DEFAULT (datetime('now','localtime')),
    lieferdatum     TEXT,
    status          TEXT    DEFAULT 'Neu'
                            CHECK(status IN ('Neu','In Bearbeitung','Versendet','Geliefert','Storniert','Zurückgegeben')),
    zahlungsart     TEXT    DEFAULT 'Rechnung'
                            CHECK(zahlungsart IN ('Bar','EC-Karte','Kreditkarte','Überweisung','Rechnung','PayPal')),
    zahlungsstatus  TEXT    DEFAULT 'Offen'
                            CHECK(zahlungsstatus IN ('Offen','Teilbezahlt','Bezahlt','Erstattet')),
    lieferadresse   TEXT,
    rabatt_prozent  REAL    DEFAULT 0.0,
    versandkosten   REAL    DEFAULT 0.0,
    notizen         TEXT,
    erstellt_am     TEXT    DEFAULT (datetime('now','localtime')),
    geaendert_am    TEXT    DEFAULT (datetime('now','localtime'))
);

-- ------------------------------------------------------------
-- Bestellpositionen (Positionen einer Bestellung)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bestellpositionen (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    bestellung_id   INTEGER NOT NULL REFERENCES bestellungen(id) ON DELETE CASCADE,
    artikel_id      INTEGER NOT NULL REFERENCES artikel(id) ON DELETE RESTRICT,
    menge           INTEGER NOT NULL DEFAULT 1 CHECK(menge > 0),
    einzelpreis     REAL    NOT NULL,
    mwst_satz       REAL    DEFAULT 19.0,
    rabatt_prozent  REAL    DEFAULT 0.0,
    position_nr     INTEGER DEFAULT 1
);

-- ------------------------------------------------------------
-- Nützliche Views
-- ------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_bestellungen_uebersicht AS
SELECT
    b.id,
    b.bestellnummer,
    b.bestelldatum,
    b.lieferdatum,
    b.status,
    b.zahlungsstatus,
    b.zahlungsart,
    k.kundennummer,
    k.vorname || ' ' || k.nachname AS kunde_name,
    k.email AS kunde_email,
    COUNT(p.id) AS anzahl_positionen,
    ROUND(
        SUM(p.menge * p.einzelpreis * (1 - p.rabatt_prozent/100.0))
        * (1 - b.rabatt_prozent/100.0)
        + b.versandkosten, 2
    ) AS gesamtbetrag_netto,
    ROUND(
        SUM(p.menge * p.einzelpreis * (1 - p.rabatt_prozent/100.0) * (1 + p.mwst_satz/100.0))
        * (1 - b.rabatt_prozent/100.0)
        + b.versandkosten, 2
    ) AS gesamtbetrag_brutto,
    b.notizen
FROM bestellungen b
JOIN kunden k ON b.kunden_id = k.id
LEFT JOIN bestellpositionen p ON p.bestellung_id = b.id
GROUP BY b.id;

CREATE VIEW IF NOT EXISTS v_artikel_uebersicht AS
SELECT
    a.id,
    a.artikelnummer,
    a.bezeichnung,
    k.name AS kategorie,
    k.farbe AS kategorie_farbe,
    a.hersteller,
    a.verkaufspreis,
    a.einkaufspreis,
    a.mwst_satz,
    a.lagerbestand,
    a.mindestbestand,
    a.einheit,
    CASE WHEN a.lagerbestand <= a.mindestbestand THEN 1 ELSE 0 END AS nachbestellen,
    a.aktiv
FROM artikel a
LEFT JOIN kategorien k ON a.kategorie_id = k.id;

-- ------------------------------------------------------------
-- Beispieldaten
-- ------------------------------------------------------------
INSERT OR IGNORE INTO kunden
    (kundennummer, vorname, nachname, email, telefon, strasse, plz, ort, notizen)
VALUES
    ('K-00001','Max','Mustermann','max.mustermann@email.de','0911 123456','Hauptstraße 1','90403','Nürnberg','Stammkunde seit 2020'),
    ('K-00002','Erika','Musterfrau','erika@muster.de','0911 654321','Fahrradweg 7','90402','Nürnberg','Interessiert an E-Bikes'),
    ('K-00003','Hans','Koch','hans.koch@firma.de','09134 88776','Rennstraße 42','91054','Erlangen','Vereinsmitglied TSV Erlangen'),
    ('K-00004','Laura','Schmidt','l.schmidt@web.de','0172 9988776','Bergstraße 5','91052','Erlangen',NULL);

INSERT OR IGNORE INTO artikel
    (artikelnummer, bezeichnung, kategorie_id, einkaufspreis, verkaufspreis, lagerbestand, mindestbestand, hersteller, beschreibung)
VALUES
    ('ART-00001','Trek FX 3 Disc','1', 599.00, 899.00, 8, 3,'Trek','Vielseitiges Fitness-Fahrrad mit hydraulischen Scheibenbremsen'),
    ('ART-00002','Cube Reaction Hybrid 625','2', 1799.00, 2499.00, 4, 2,'Cube','E-MTB mit Bosch Performance CX Motor'),
    ('ART-00003','Fahrradhelm Giro Syntax','6', 49.90, 89.95, 15, 5,'Giro','MIPS-Technologie, Größen S-XL'),
    ('ART-00004','Fahrradschloss Kryptonite Evolution','3', 28.00, 49.95, 22, 8,'Kryptonite','Bügelschloss mit 13mm gehärtetem Stahl'),
    ('ART-00005','Shimano Bremsbeläge B01S','5', 4.50, 12.95, 45, 15,'Shimano','Für hydraulische Scheibenbremsen'),
    ('ART-00006','Radhose Vaude Men Pro','4', 55.00, 99.95, 10, 4,'Vaude','Mit Innensitz, Herren, Gr. S-XXL'),
    ('ART-00007','Pumpe Topeak Joe Blow Sport','3', 18.00, 34.95, 12, 5,'Topeak','Standpumpe mit Manometer'),
    ('ART-00008','Fahrradcomputer Garmin Edge 530','3', 149.00, 249.95, 6, 3,'Garmin','GPS-Navigation, Herzfrequenz-kompatibel');
