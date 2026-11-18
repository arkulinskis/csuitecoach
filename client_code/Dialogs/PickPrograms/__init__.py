from anvil import *

from ._anvil_designer import PickProgramsTemplate
from ...Items.TrackPick import picked


class PickPrograms(PickProgramsTemplate):
    """Choose a team member's programs. alert(PickPrograms(catalog, on, who)) -> [track ids] or None (cancelled)."""

    def __init__(self, catalog=(), on=(), who="", **properties):
        super().__init__(**properties)
        self.dom_nodes["title"].textContent = "Programs for %s" % who if who else "Programs"
        self.picks_panel.items = [dict(t, on=t["id"] in on) for t in catalog]

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        ids = picked(self.picks_panel)
        if not ids:
            self.message.text, self.message.visible = "Pick at least one program.", True
            return
        self.raise_event("x-close-alert", value=ids)

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)
