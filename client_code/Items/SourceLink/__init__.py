from anvil import *

from ._anvil_designer import SourceLinkTemplate


class SourceLink(SourceLinkTemplate):
    """A source (opens in a new tab). item = {label, url}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        a = self.dom_nodes["a"]
        a.setAttribute("href", self.item.get("url") or "#")
        a.textContent = self.item.get("label") or ""
