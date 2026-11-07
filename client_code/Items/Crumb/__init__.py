from anvil import *

from ._anvil_designer import CrumbTemplate


class Crumb(CrumbTemplate):
    """One breadcrumb in a Hero. item = {href (None = where you are), label, first}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        self.dom_nodes["sep"].hidden = bool(i.get("first"))
        a, here = self.dom_nodes["a"], self.dom_nodes["here"]
        if i.get("href"):
            a.setAttribute("href", i["href"])
            a.textContent = i.get("label") or ""
            here.hidden = True
        else:
            a.hidden = True
            here.textContent = i.get("label") or ""
            here.setAttribute("aria-current", "page")
