from anvil import *

from ._anvil_designer import ParaTemplate


class Para(ParaTemplate):
    """One paragraph of a briefing or a case story. item = the text."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        self.dom_nodes["p"].textContent = i if isinstance(i, str) else (i.get("text") or "")
