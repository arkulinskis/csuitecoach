from anvil import *

from ._anvil_designer import MetaItemTemplate


class MetaItem(MetaItemTemplate):
    """A fact with an icon (hero bands). item = {icon, text}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.dom_nodes["ic"].className = "ic ic-" + (self.item.get("icon") or "info")
        self.dom_nodes["text"].textContent = self.item.get("text") or ""
