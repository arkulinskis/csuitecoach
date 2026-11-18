from anvil import *

from ._anvil_designer import TrackPickTemplate


class TrackPick(TrackPickTemplate):
    """A program to assign, as a tick box (Team invites, Dialogs/PickPrograms). item = {id, title, on}.
    The page reads the ticks with picked(panel)."""

    def __init__(self, **properties):
        super().__init__(**properties)


def picked(panel):
    """The ids of the ticked programs in a RepeatingPanel of TrackPick items."""
    return [c.item["id"] for c in panel.get_components() if getattr(c, "pick", None) is not None and c.pick.checked]
