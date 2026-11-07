from anvil import *

from ._anvil_designer import PathStepTemplate


class PathStep(PathStepTemplate):
    """A program on the path to the Fellowship. item = {title, have}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        have = bool(self.item.get("have"))
        self.dom_nodes["box"].className = "cr-step have" if have else "cr-step"
        self.dom_nodes["ic"].className = "ic ic-award" if have else "ic ic-lock"
        self.dom_nodes["title"].textContent = self.item["title"] + (" (held)" if have else "")
