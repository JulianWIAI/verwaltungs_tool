# 🚲 Radsport Koch GmbH – Verwaltungssystem

Professionelle Kundenverwaltungs- und Bestellsoftware für die **Radsport Koch GmbH**.
Entwickelt mit **Python 3.10+**, **PyQt6** und **SQLite**.

---

## 📋 Features

### Kernfunktionen
| Feature | Beschreibung |
|---|---|
| 👥 **Kundenverwaltung** | Anlegen, Bearbeiten, Löschen mit Adresse, Kontakt, Notizen |
| 🚲 **Artikelverwaltung** | Produktkatalog mit Kategorien, Preisen, Lagerbestand |
| 📦 **Bestellverwaltung** | Bestellungen mit Positionen, Status, Zahlung |
| 🏠 **Dashboard** | Live-Statistiken, Umsatzdiagramm, Top-Artikel |
| 🔍 **Suche** | Echtzeit-Suche in allen Bereichen |
| 🗑️ **Löschfunktion** | Sicheres Löschen mit Integritätsprüfung |

### Zusatzfeatures
- **Automatische Kundennummern** (K-00001, K-00002, ...)
- **Automatische Artikelnummern** (ART-00001, ...)
- **Automatische Bestellnummern** (B-00001, ...)
- **Lagerbestandswarnung** bei Unterschreitung des Mindestbestands
- **Status-Badges** farbcodiert für Bestellstatus und Zahlungsstatus
- **Bestelldetails** mit schnellem Status-Update
- **Kategorien** für Artikel mit Farbcodierung
- **MwSt.-Berechnung** (19%, 7%, 0%)
- **Rabatt & Versandkosten** pro Bestellung
- **Live-Summenberechnung** beim Erstellen von Bestellungen
- **Doppelklick** zum Öffnen/Bearbeiten in allen Tabellen
- **Fremdschlüssel-Schutz**: Kunden/Artikel mit Bestellungen können nicht gelöscht werden
- **Beispieldaten** werden beim ersten Start automatisch eingefügt
- **CSV-Export** für Kunden, Artikel und Bestellungen (Excel-kompatibel)

---

## 🛠️ Installation

### Voraussetzungen
```
Python 3.10 oder neuer
PyQt6
```

### Schritt 1 – PyQt6 installieren
```bash
pip install PyQt6
```

### Schritt 2 – Programm starten
```bash
cd radsport_koch
python main.py
```

Die SQLite-Datenbank (`radsport_koch.db`) wird beim ersten Start automatisch erstellt.

---

## 📁 Projektstruktur

```
radsport_koch/
├── main.py           # Hauptprogramm & Hauptfenster
├── database.py       # Alle Datenbankoperationen (SQLite)
├── schema.sql        # Datenbankschema & Beispieldaten
├── styles.py         # Zentrales Stylesheet & Farben
├── dashboard.py      # Dashboard-Widget
├── kunden.py         # Kundenverwaltung
├── artikel.py        # Artikelverwaltung
├── bestellungen.py   # Bestellverwaltung
├── README.md         # Diese Datei
└── radsport_koch.db  # SQLite-Datenbank (wird automatisch erstellt)
```

---

## 🗄️ Datenbankstruktur

```sql
kunden              -- Kundenstammdaten
kategorien          -- Artikelkategorien
artikel             -- Produktkatalog
bestellungen        -- Bestellköpfe
bestellpositionen   -- Positionen einer Bestellung

-- Views (zur einfachen Abfrage):
v_bestellungen_uebersicht   -- Bestellungen mit Kundendaten & Summen
v_artikel_uebersicht        -- Artikel mit Kategoriename & Statusinfo
```

---

## 💡 Bedienung

- **Neuen Datensatz anlegen**: Schaltfläche „➕ Neu..." klicken
- **Bearbeiten**: Doppelklick auf eine Zeile **oder** Schaltfläche „✏️ Bearbeiten"
- **Löschen**: Schaltfläche „🗑️" (Schutz vor versehentlichem Löschen bei verknüpften Daten)
- **Suchen**: Suchfeld oben links – Echtzeit-Filterung
- **Bestellstatus ändern**: In den Bestelldetails (🔍-Button) direkt updaten
- **CSV exportieren**: Schaltfläche „📥 CSV exportieren" in der Toolbar – speichert die aktuell gefilterte Liste als `.csv`-Datei (mit Semikolon-Trennzeichen, direkt in Excel öffenbar)

---

## 📸 Technologien

| Technologie | Verwendung |
|---|---|
| **Python 3.10+** | Programmiersprache |
| **PyQt6** | GUI-Framework |
| **SQLite 3** | Datenbank (dateibasiert, keine Installation nötig) |
| **SQL Views** | Berechnete Auswertungen (Umsatz, Status) |

---

*Erstellt für den Bachelor Professional – Fachinformatiker*
