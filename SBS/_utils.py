"""
_utils – Shared utility helpers for the SBS package.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Provide small, stateless helper functions used by more than one SBS module.
  - Avoid circular imports by keeping shared code here rather than inside a class module.

Dependencies:
  - styles: centralised colour constants
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt


def _farbe_badge(text: str, farbe: str) -> QLabel:
    """
    Create a coloured badge label (rounded pill with text).

    Used to visually highlight status information.

    :param text:  Text to display inside the badge (e.g. "Open")
    :param farbe: Hex colour code for the accent colour (e.g. "#e63946")
    :return:      Fully styled QLabel ready for insertion into a layout.
    """
    lbl = QLabel(text)
    # Appending "22" as a hex alpha value to the colour gives ~13% opacity for the background,
    # producing a transparent-tinted badge instead of a fully filled one.
    lbl.setStyleSheet(f"""
        background-color: {farbe}22;
        color: {farbe};
        border-radius: 10px;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: 600;
    """)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centre text horizontally and vertically
    return lbl
