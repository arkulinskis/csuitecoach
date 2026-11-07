from anvil import *

from ._anvil_designer import DoItemTemplate


class DoItem(DoItemTemplate):
    """A line in a Do / Avoid list. item = {text, good}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.dom_nodes["ic"].className = "ic ic-check" if self.item.get("good") else "ic ic-x"
        self.dom_nodes["text"].textContent = self.item.get("text") or ""
