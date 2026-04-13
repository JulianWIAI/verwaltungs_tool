"""
Radsport Koch GmbH – Webbasiertes Bestellformular
==================================================
Flask-Backend für den Online-Bestellprozess.

Starten: python web_bestellung.py
Öffnen:  http://localhost:5000
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, jsonify, request
import database as db

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('bestellung.html')


@app.route('/api/artikel')
def api_artikel():
    artikel = db.get_alle_artikel(nur_aktiv=True)
    return jsonify(artikel)


@app.route('/api/kunden/suche')
def api_kunden_suche():
    q = request.args.get('q', '')
    kunden = db.get_alle_kunden(suche=q)
    return jsonify(kunden)


@app.route('/api/kunden/<int:kunde_id>')
def api_kunde_get(kunde_id):
    kunde = db.get_kunde(kunde_id)
    if kunde is None:
        return jsonify({'error': 'Kunde nicht gefunden'}), 404
    return jsonify(kunde)


@app.route('/api/kunden', methods=['POST'])
def api_kunden_erstellen():
    daten = request.get_json()
    if not daten:
        return jsonify({'success': False, 'error': 'Keine Daten übermittelt'}), 400
    try:
        kid = db.speichere_kunde(daten)
        kunde = db.get_kunde(kid)
        return jsonify({'success': True, 'kunde': kunde})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/bestellungen', methods=['POST'])
def api_bestellung_erstellen():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Keine Daten übermittelt'}), 400
    try:
        bid = db.speichere_bestellung(data['bestellung'], data['positionen'])
        bestellung = db.get_bestellung(bid)
        positionen = db.get_bestellpositionen(bid)
        return jsonify({
            'success': True,
            'bestellung': dict(bestellung) if bestellung else {},
            'positionen': positionen
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == '__main__':
    db.init_db()
    print("\n  Radsport Koch – Bestellformular")
    print("=" * 40)
    print("  Oeffnen Sie: http://localhost:5000")
    print("=" * 40)
    print("Druecken Sie Strg+C zum Beenden.\n")
    app.run(debug=True, port=5000)
