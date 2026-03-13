"""
Radsport Koch GmbH – Zentrales Stylesheet & Theme
"""

# Hauptfarben
COLOR_PRIMARY    = "#1a2744"   # Dunkelblau (Header/Sidebar)
COLOR_SECONDARY  = "#e63946"   # Rot (Akzent / Radsport)
COLOR_ACCENT     = "#f4a261"   # Orange (Highlights)
COLOR_BG         = "#f0f2f5"   # Hellgrau (Hintergrund)
COLOR_WHITE      = "#ffffff"
COLOR_CARD       = "#ffffff"
COLOR_TEXT       = "#1d1d1d"
COLOR_TEXT_LIGHT = "#6c757d"
COLOR_SUCCESS    = "#2ecc71"
COLOR_WARNING    = "#f39c12"
COLOR_DANGER     = "#e74c3c"
COLOR_INFO       = "#3498db"
COLOR_BORDER     = "#dee2e6"

STATUS_FARBEN = {
    "Neu":             "#3498db",
    "In Bearbeitung":  "#f39c12",
    "Versendet":       "#9b59b6",
    "Geliefert":       "#2ecc71",
    "Storniert":       "#e74c3c",
    "Zurückgegeben":   "#95a5a6",
}

ZAHLUNG_FARBEN = {
    "Offen":       "#e74c3c",
    "Teilbezahlt": "#f39c12",
    "Bezahlt":     "#2ecc71",
    "Erstattet":   "#95a5a6",
}

MAIN_STYLE = f"""
/* ── Global ── */
QMainWindow, QDialog {{
    background-color: {COLOR_BG};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: {COLOR_TEXT};
}}

QWidget {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: {COLOR_TEXT};
}}

/* ── Sidebar Navigation ── */
#sidebar {{
    background-color: {COLOR_PRIMARY};
    min-width: 220px;
    max-width: 220px;
}}

#sidebar_title {{
    color: {COLOR_WHITE};
    font-size: 16px;
    font-weight: bold;
    padding: 8px 0;
}}

#sidebar_subtitle {{
    color: rgba(255,255,255,0.6);
    font-size: 10px;
    padding-bottom: 10px;
}}

#nav_btn {{
    background: transparent;
    color: rgba(255,255,255,0.75);
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
    margin: 2px 8px;
}}

#nav_btn:hover {{
    background-color: rgba(255,255,255,0.1);
    color: {COLOR_WHITE};
}}

#nav_btn_active {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_WHITE};
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
    margin: 2px 8px;
}}

/* ── Content Bereich ── */
#content_area {{
    background-color: {COLOR_BG};
    padding: 0;
}}

/* ── Page Header ── */
#page_header {{
    background-color: {COLOR_WHITE};
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 16px 24px;
}}

#page_title {{
    font-size: 22px;
    font-weight: 700;
    color: {COLOR_PRIMARY};
}}

#page_subtitle {{
    font-size: 12px;
    color: {COLOR_TEXT_LIGHT};
}}

/* ── Karten / Panels ── */
#card {{
    background-color: {COLOR_WHITE};
    border-radius: 12px;
    border: 1px solid {COLOR_BORDER};
    padding: 20px;
}}

#stat_card {{
    background-color: {COLOR_WHITE};
    border-radius: 12px;
    border: 1px solid {COLOR_BORDER};
    padding: 20px;
    min-width: 160px;
}}

#stat_value {{
    font-size: 28px;
    font-weight: 700;
    color: {COLOR_PRIMARY};
}}

#stat_label {{
    font-size: 12px;
    color: {COLOR_TEXT_LIGHT};
}}

/* ── Tabellen ── */
QTableWidget {{
    background-color: {COLOR_WHITE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    gridline-color: #f1f3f4;
    selection-background-color: #e8f0fe;
    selection-color: {COLOR_TEXT};
    alternate-background-color: #fafbfc;
    font-size: 13px;
}}

QTableWidget::item {{
    padding: 8px 12px;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: #dbeafe;
    color: {COLOR_TEXT};
}}

QHeaderView::section {{
    background-color: {COLOR_PRIMARY};
    color: {COLOR_WHITE};
    font-weight: 600;
    font-size: 12px;
    padding: 10px 12px;
    border: none;
    border-right: 1px solid rgba(255,255,255,0.1);
}}

QHeaderView::section:first {{
    border-top-left-radius: 8px;
}}

QHeaderView::section:last {{
    border-top-right-radius: 8px;
    border-right: none;
}}

/* ── Buttons ── */
#btn_primary {{
    background-color: {COLOR_SECONDARY};
    color: {COLOR_WHITE};
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
    min-width: 100px;
}}

#btn_primary:hover {{
    background-color: #c1121f;
}}

#btn_primary:pressed {{
    background-color: #9e1a2a;
}}

#btn_secondary {{
    background-color: {COLOR_PRIMARY};
    color: {COLOR_WHITE};
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
    min-width: 100px;
}}

#btn_secondary:hover {{
    background-color: #263561;
}}

#btn_danger {{
    background-color: transparent;
    color: {COLOR_DANGER};
    border: 1.5px solid {COLOR_DANGER};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 12px;
}}

#btn_danger:hover {{
    background-color: {COLOR_DANGER};
    color: {COLOR_WHITE};
}}

#btn_icon {{
    background-color: transparent;
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 13px;
    color: {COLOR_TEXT};
    min-width: 80px;
}}

#btn_icon:hover {{
    background-color: {COLOR_BG};
    border-color: {COLOR_PRIMARY};
    color: {COLOR_PRIMARY};
}}

/* ── Eingabefelder ── */
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    background-color: {COLOR_WHITE};
    font-size: 13px;
    color: {COLOR_TEXT};
    selection-background-color: #dbeafe;
}}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
    border-color: {COLOR_SECONDARY};
    outline: none;
}}

QLineEdit:read-only {{
    background-color: #f8f9fa;
    color: {COLOR_TEXT_LIGHT};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLOR_TEXT_LIGHT};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    background: {COLOR_WHITE};
    selection-background-color: #dbeafe;
}}

/* ── Suchleiste ── */
#search_input {{
    border: 1.5px solid {COLOR_BORDER};
    border-radius: 20px;
    padding: 8px 16px 8px 36px;
    background-color: {COLOR_WHITE};
    font-size: 13px;
    min-width: 260px;
}}

#search_input:focus {{
    border-color: {COLOR_SECONDARY};
}}

/* ── Labels ── */
#label_form {{
    font-weight: 600;
    font-size: 12px;
    color: {COLOR_TEXT_LIGHT};
    text-transform: uppercase;
}}

/* ── Tabs ── */
QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    background: {COLOR_WHITE};
}}

QTabBar::tab {{
    background: transparent;
    color: {COLOR_TEXT_LIGHT};
    padding: 10px 20px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    color: {COLOR_SECONDARY};
    border-bottom: 2px solid {COLOR_SECONDARY};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    color: {COLOR_TEXT};
    background: rgba(0,0,0,0.03);
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: {COLOR_BG};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: #c4c9d4;
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #9ea5b0;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

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
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Dialoge ── */
QDialog {{
    background-color: {COLOR_WHITE};
    border-radius: 12px;
}}

/* ── Splitter ── */
QSplitter::handle {{
    background: {COLOR_BORDER};
    width: 1px;
}}

/* ── Tooltips ── */
QToolTip {{
    background-color: {COLOR_PRIMARY};
    color: {COLOR_WHITE};
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ── Statusbar ── */
QStatusBar {{
    background-color: {COLOR_PRIMARY};
    color: rgba(255,255,255,0.8);
    font-size: 12px;
    padding: 4px 12px;
}}

/* ── Message Boxes ── */
QMessageBox {{
    background-color: {COLOR_WHITE};
}}
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
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLOR_BORDER};
    border-radius: 4px;
    background: {COLOR_WHITE};
}}
QCheckBox::indicator:checked {{
    background-color: {COLOR_SECONDARY};
    border-color: {COLOR_SECONDARY};
}}
"""
