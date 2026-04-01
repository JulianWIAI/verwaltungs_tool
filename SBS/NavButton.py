"""
NavButton – Navigation button used in the sidebar.

Part of the Radsport Koch GmbH management system.
Extracted into its own module as part of the SBS (Single-class Building System) package.

Responsibilities:
  - Display an emoji icon and a text label as a sidebar navigation entry.
  - Visually highlight itself when it represents the currently active page.

Dependencies:
  - styles: centralised colour constants (not imported directly; styling comes from
    the application-level stylesheet via object names)
"""

from PyQt6.QtWidgets import QPushButton, QSizePolicy
from PyQt6.QtCore import Qt


class NavButton(QPushButton):
    """
    Navigation button used in the application sidebar.

    Extends QPushButton with:
    - An emoji icon plus text label as its caption.
    - A fixed appearance driven by Qt's object-name styling system.
    - A method to highlight the button for the currently active page.
    """

    def __init__(self, icon: str, text: str, parent=None):
        """
        Create a new NavButton.

        :param icon:   Emoji character displayed to the left of the text (e.g. "🏠")
        :param text:   Caption of the button (e.g. "Dashboard")
        :param parent: Optional parent widget (normally the Sidebar)
        """
        # Call the parent class constructor and set the combined icon + text label.
        # The extra spaces create a small visual indent.
        super().__init__(f"  {icon}  {text}", parent)

        # Object name is used by the Qt stylesheet to style this button.
        self.setObjectName("nav_btn")

        # checkable=False: the button should not behave like a toggle button.
        self.setCheckable(False)

        # Show a pointing-hand cursor when hovering over the button.
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Fixed height for a consistent appearance within the sidebar.
        self.setFixedHeight(46)

        # Width: expand to fill available space; height: fixed.
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_active(self, active: bool):
        """
        Highlight this button (active) or reset it (inactive).

        Qt applies styles based on the object name.  By renaming the object and
        then re-polishing, Qt is forced to recalculate the style immediately.

        :param active: True if this button belongs to the currently displayed page.
        """
        # Set a different object name depending on the active/inactive state.
        self.setObjectName("nav_btn_active" if active else "nav_btn")

        # unpolish() removes the old style …
        self.style().unpolish(self)
        # … polish() applies the new style based on the updated object name.
        self.style().polish(self)
