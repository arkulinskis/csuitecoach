from anvil import *

from ._anvil_designer import ModuleLinkTemplate


class ModuleLink(ModuleLinkTemplate):
    """A module as a row link (exam "still to finish", a case's "Studied in"). item = {id, title, track}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        m = self.item
        self.dom_nodes["a"].setAttribute("href", "#module/" + m["id"])
        self.dom_nodes["title"].textContent = m.get("title") or ""
        sub = self.dom_nodes["sub"]
        sub.textContent = m.get("track") or ""
        sub.hidden = not m.get("track")
