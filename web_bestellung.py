"""
Radsport Koch GmbH – Webshop & Kundenportal
============================================
Flask-Backend für den Online-Auftritt.

Seiten:
  /                       – Shop (Produktkatalog + Bestellung)
  /login                  – Anmelden / Registrieren
  /logout                 – Abmelden
  /profil                 – Profil bearbeiten (Login erforderlich)
  /meine-bestellungen     – Bestellhistorie (Login erforderlich)
  /konto-loeschen         – Konto löschen (Login erforderlich, POST)

API-Endpunkte:
  GET  /api/artikel       – alle aktiven Artikel
  POST /api/bestellungen  – neue Bestellung (Login erforderlich)

Starten: python web_bestellung.py
Öffnen:  http://localhost:5000
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps
from flask import (
    Flask, render_template, jsonify, request,
    session, redirect, url_for
)
import database as db

# ──────────────────────────────────────────────────────────────────────────────
# E-Mail-Konfiguration
# ──────────────────────────────────────────────────────────────────────────────
EMAIL_ABSENDER   = "gjuligast@gmail.com"
EMAIL_APP_PASSWORT = "rezq rxws oezq mqjm"


def sende_bestellbestaetigung(empfaenger_email: str, empfaenger_name: str,
                               bestellung: dict, positionen: list):
    """Sendet eine Bestellbestätigung per E-Mail an den Kunden."""
    try:
        # ── E-Mail-Inhalt aufbauen ────────────────────────────────────────────
        bestell_nr = bestellung.get("id", "–")
        datum      = bestellung.get("erstellt_am", "–")

        # Artikelzeilen für Plain-Text und HTML
        zeilen_txt  = []
        zeilen_html = []
        gesamt      = 0.0

        for pos in positionen:
            name      = pos.get("artikel_name", pos.get("name", "Unbekannt"))
            menge     = int(pos.get("menge", 1))
            einzelpreis = float(pos.get("einzelpreis", pos.get("preis", 0)))
            summe_pos = menge * einzelpreis
            gesamt   += summe_pos

            zeilen_txt.append(
                f"  {name:<40} {menge:>3} x {einzelpreis:>8.2f} € = {summe_pos:>9.2f} €"
            )
            zeilen_html.append(
                f"<tr>"
                f"<td style='padding:6px 12px;border-bottom:1px solid #eee'>{name}</td>"
                f"<td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:center'>{menge}</td>"
                f"<td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:right'>{einzelpreis:.2f} €</td>"
                f"<td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:right'>{summe_pos:.2f} €</td>"
                f"</tr>"
            )

        # ── Plain-Text-Version ────────────────────────────────────────────────
        text_body = f"""Hallo {empfaenger_name},

vielen Dank für Ihre Bestellung bei Radsport Koch GmbH!

Bestellnummer : {bestell_nr}
Bestelldatum  : {datum}

BESTELLÜBERSICHT
{'─' * 70}
{'Artikel':<40} {'Menge':>5}   {'Einzelpreis':>11}   {'Gesamt':>10}
{'─' * 70}
{chr(10).join(zeilen_txt)}
{'─' * 70}
{'GESAMTSUMME':>60}   {gesamt:>9.2f} €

Bei Fragen stehen wir Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen
Ihr Team von Radsport Koch GmbH
"""

        # ── HTML-Version ──────────────────────────────────────────────────────
        html_body = f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;color:#333;max-width:650px;margin:auto">
  <div style="background:#1a73e8;padding:20px 30px">
    <h1 style="color:#fff;margin:0;font-size:22px">Radsport Koch GmbH</h1>
    <p style="color:#c8e0ff;margin:4px 0 0">Bestellbestätigung</p>
  </div>
  <div style="padding:24px 30px">
    <p>Hallo <strong>{empfaenger_name}</strong>,</p>
    <p>vielen Dank für Ihre Bestellung! Wir haben sie erhalten und bearbeiten sie schnellstmöglich.</p>
    <table style="width:100%;border-collapse:collapse;margin:16px 0">
      <tr style="background:#f5f5f5">
        <td style="padding:6px 12px"><strong>Bestellnummer</strong></td>
        <td style="padding:6px 12px">{bestell_nr}</td>
      </tr>
      <tr>
        <td style="padding:6px 12px"><strong>Bestelldatum</strong></td>
        <td style="padding:6px 12px">{datum}</td>
      </tr>
    </table>
    <h3 style="border-bottom:2px solid #1a73e8;padding-bottom:6px">Bestellübersicht</h3>
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr style="background:#1a73e8;color:#fff">
          <th style="padding:8px 12px;text-align:left">Artikel</th>
          <th style="padding:8px 12px;text-align:center">Menge</th>
          <th style="padding:8px 12px;text-align:right">Einzelpreis</th>
          <th style="padding:8px 12px;text-align:right">Gesamt</th>
        </tr>
      </thead>
      <tbody>
        {''.join(zeilen_html)}
      </tbody>
      <tfoot>
        <tr style="background:#f5f5f5;font-weight:bold">
          <td colspan="3" style="padding:10px 12px;text-align:right">Gesamtsumme:</td>
          <td style="padding:10px 12px;text-align:right">{gesamt:.2f} €</td>
        </tr>
      </tfoot>
    </table>
    <p style="margin-top:24px">Bei Fragen stehen wir Ihnen gerne zur Verfügung.</p>
    <p>Mit freundlichen Grüßen<br><strong>Ihr Team von Radsport Koch GmbH</strong></p>
  </div>
  <div style="background:#f0f0f0;padding:12px 30px;font-size:12px;color:#888;text-align:center">
    Radsport Koch GmbH · Diese E-Mail wurde automatisch generiert.
  </div>
</body>
</html>"""

        # ── Nachricht zusammenbauen ───────────────────────────────────────────
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Ihre Bestellbestätigung #{bestell_nr} – Radsport Koch GmbH"
        msg["From"]    = EMAIL_ABSENDER
        msg["To"]      = empfaenger_email

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html",  "utf-8"))

        # ── Versenden über Gmail SMTP ─────────────────────────────────────────
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ABSENDER, EMAIL_APP_PASSWORT)
            server.sendmail(EMAIL_ABSENDER, empfaenger_email, msg.as_string())

        return True
    except Exception as e:
        print(f"[E-Mail] Fehler beim Senden: {e}")
        return False

app = Flask(__name__)
app.secret_key = "radsport_koch_geheim_2025"


# ──────────────────────────────────────────────────────────────────────────────
# Hilfsfunktion: Login-Schutz
# ──────────────────────────────────────────────────────────────────────────────

def login_required(f):
    """Dekorator: leitet zur Login-Seite weiter, wenn nicht eingeloggt."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "kunde_id" not in session:
            return redirect(url_for("login_seite"))
        return f(*args, **kwargs)
    return wrapper


def _nav_context():
    """Gemeinsamer Template-Kontext für alle Seiten."""
    return {
        "eingeloggt": "kunde_id" in session,
        "kunde_name": session.get("kunde_name", ""),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Seiten
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/")
def shop():
    """Startseite: Produktkatalog mit Warenkorb und Bestellfunktion."""
    kategorien = db.get_kategorien()
    return render_template("shop.html", kategorien=kategorien, **_nav_context())


@app.route("/login", methods=["GET", "POST"])
def login_seite():
    """Login- und Registrierungsseite."""
    if "kunde_id" in session:
        return redirect(url_for("shop"))

    fehler_login = None
    fehler_reg = None
    tab = request.args.get("tab", "login")  # aktiver Tab: "login" oder "registrieren"

    if request.method == "POST":
        action = request.form.get("action")

        # ── Anmelden ──────────────────────────────────────────────────────────
        if action == "login":
            tab = "login"
            email = request.form.get("email", "").strip()
            passwort = request.form.get("passwort", "")
            if not email or not passwort:
                fehler_login = "Bitte E-Mail und Passwort eingeben."
            else:
                kunde = db.login_kunde(email, passwort)
                if kunde:
                    session["kunde_id"] = kunde["id"]
                    session["kunde_name"] = f"{kunde['vorname']} {kunde['nachname']}"
                    return redirect(url_for("shop"))
                else:
                    fehler_login = "E-Mail-Adresse oder Passwort falsch."

        # ── Registrieren ──────────────────────────────────────────────────────
        elif action == "registrieren":
            tab = "registrieren"
            vorname  = request.form.get("vorname",  "").strip()
            nachname = request.form.get("nachname", "").strip()
            email    = request.form.get("reg_email", "").strip()
            passwort = request.form.get("reg_passwort", "").strip()
            telefon  = request.form.get("telefon",  "").strip()
            strasse  = request.form.get("strasse",  "").strip()
            plz      = request.form.get("plz",      "").strip()
            ort      = request.form.get("ort",      "").strip()

            if not vorname or not nachname or not email:
                fehler_reg = "Vorname, Nachname und E-Mail sind Pflichtfelder."
            elif "@" not in email:
                fehler_reg = "Bitte eine gültige E-Mail-Adresse eingeben."
            elif db.get_kunde_by_email(email):
                fehler_reg = "Diese E-Mail-Adresse ist bereits registriert."
            else:
                daten = {
                    "vorname":  vorname,
                    "nachname": nachname,
                    "email":    email,
                    "passwort": passwort or "student",
                    "telefon":  telefon,
                    "strasse":  strasse,
                    "plz":      plz,
                    "ort":      ort,
                }
                kid = db.speichere_kunde(daten)
                kunde = db.get_kunde(kid)
                session["kunde_id"] = kunde["id"]
                session["kunde_name"] = f"{kunde['vorname']} {kunde['nachname']}"
                return redirect(url_for("shop"))

    return render_template(
        "login.html",
        fehler_login=fehler_login,
        fehler_reg=fehler_reg,
        tab=tab,
        **_nav_context()
    )


@app.route("/logout")
def logout():
    """Abmelden und zur Login-Seite weiterleiten."""
    session.clear()
    return redirect(url_for("login_seite"))


@app.route("/profil", methods=["GET", "POST"])
@login_required
def profil():
    """Profil bearbeiten: Name, Adresse, E-Mail, Passwort."""
    kunde = db.get_kunde(session["kunde_id"])
    erfolg = None
    fehler = None

    if request.method == "POST":
        vorname  = request.form.get("vorname",  "").strip()
        nachname = request.form.get("nachname", "").strip()
        email    = request.form.get("email",    "").strip()

        if not vorname or not nachname or not email:
            fehler = "Vorname, Nachname und E-Mail dürfen nicht leer sein."
        elif "@" not in email:
            fehler = "Bitte eine gültige E-Mail-Adresse eingeben."
        else:
            # Prüfen ob E-Mail schon von einem anderen Kunden verwendet wird
            existing = db.get_kunde_by_email(email)
            if existing and existing["id"] != session["kunde_id"]:
                fehler = "Diese E-Mail-Adresse wird bereits von einem anderen Konto verwendet."
            else:
                daten = {
                    "id":       session["kunde_id"],
                    "vorname":  vorname,
                    "nachname": nachname,
                    "email":    email,
                    "telefon":  request.form.get("telefon", "").strip(),
                    "strasse":  request.form.get("strasse", "").strip(),
                    "plz":      request.form.get("plz",     "").strip(),
                    "ort":      request.form.get("ort",     "").strip(),
                    "land":     request.form.get("land",    "Deutschland").strip(),
                    "geburtsdatum": request.form.get("geburtsdatum", "").strip(),
                }
                # Passwort nur ändern wenn ein neues eingegeben wurde
                neues_pw = request.form.get("neues_passwort", "").strip()
                if neues_pw:
                    daten["passwort"] = neues_pw

                db.speichere_kunde(daten)
                session["kunde_name"] = f"{vorname} {nachname}"
                kunde = db.get_kunde(session["kunde_id"])
                erfolg = "Profil erfolgreich gespeichert."

    return render_template(
        "profil.html",
        kunde=kunde,
        erfolg=erfolg,
        fehler=fehler,
        **_nav_context()
    )


@app.route("/meine-bestellungen")
@login_required
def meine_bestellungen():
    """Bestellhistorie des eingeloggten Kunden."""
    bestellungen = db.get_kunden_bestellungen(session["kunde_id"])
    return render_template(
        "meine_bestellungen.html",
        bestellungen=bestellungen,
        **_nav_context()
    )


@app.route("/konto-loeschen", methods=["POST"])
@login_required
def konto_loeschen():
    """Konto des eingeloggten Kunden löschen."""
    kid = session["kunde_id"]
    ok = db.loesche_kunde(kid)
    if ok:
        session.clear()
        return redirect(url_for("login_seite") + "?geloescht=1")
    # Löschen fehlgeschlagen (Bestellungen vorhanden)
    return redirect(url_for("profil") + "?fehler=bestellungen")


# ──────────────────────────────────────────────────────────────────────────────
# API-Endpunkte
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/bestellungen/<int:bestell_id>")
def api_bestellung_detail(bestell_id):
    """Gibt eine einzelne Bestellung mit allen Positionen zurück (nur eigene Bestellungen)."""
    if "kunde_id" not in session:
        return jsonify({"error": "Nicht eingeloggt"}), 401

    # Eigentümer-Prüfung direkt auf der Basistabelle (View enthält keine kunden_id)
    conn = db.get_connection()
    check = conn.execute(
        "SELECT id FROM bestellungen WHERE id = ? AND kunden_id = ?",
        (bestell_id, session["kunde_id"])
    ).fetchone()
    conn.close()

    if not check:
        return jsonify({"error": "Nicht gefunden oder kein Zugriff"}), 404

    bestellung = db.get_bestellung(bestell_id)
    positionen = db.get_bestellpositionen(bestell_id)

    return jsonify({
        "bestellung": dict(bestellung) if bestellung else {},
        "positionen": [dict(p) for p in positionen],
        "kunde_name": session.get("kunde_name", ""),
    })


@app.route("/api/artikel")
def api_artikel():
    """Alle aktiven Artikel als JSON."""
    artikel = db.get_alle_artikel(nur_aktiv=True)
    return jsonify(artikel)


@app.route("/api/kategorien")
def api_kategorien():
    """Alle Kategorien als JSON."""
    return jsonify(db.get_kategorien())


@app.route("/api/bestellungen", methods=["POST"])
def api_bestellung_erstellen():
    """Neue Bestellung anlegen (Login erforderlich)."""
    if "kunde_id" not in session:
        return jsonify({"success": False, "error": "Nicht eingeloggt"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Keine Daten übermittelt"}), 400

    try:
        bestellung_daten = data.get("bestellung", {})
        bestellung_daten["kunden_id"] = session["kunde_id"]
        positionen = data.get("positionen", [])

        bid = db.speichere_bestellung(bestellung_daten, positionen)
        bestellung = db.get_bestellung(bid)
        pos_liste  = db.get_bestellpositionen(bid)

        # ── Bestellbestätigung per E-Mail senden ─────────────────────────────
        kunde = db.get_kunde(session["kunde_id"])
        if kunde and kunde.get("email"):
            empfaenger_name  = f"{kunde['vorname']} {kunde['nachname']}"
            empfaenger_email = kunde["email"]
            bestellung_dict  = dict(bestellung) if bestellung else {}
            sende_bestellbestaetigung(
                empfaenger_email,
                empfaenger_name,
                bestellung_dict,
                pos_liste,
            )

        return jsonify({
            "success":    True,
            "bestellung": dict(bestellung) if bestellung else {},
            "positionen": pos_liste,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ──────────────────────────────────────────────────────────────────────────────
# Start
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db.init_db()
    print("\n  Radsport Koch – Webshop & Kundenportal")
    print("=" * 45)
    print("  Oeffnen Sie: http://localhost:5000")
    print("=" * 45)
    print("  Strg+C zum Beenden.\n")
    app.run(debug=True, port=5000)