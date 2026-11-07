from anvil import *

from ._anvil_designer import HonourCardTemplate
from ... import cs, state


class HonourCard(HonourCardTemplate):
    """A graduate on the public Honour Roll (landing, verify, home). item = {name, title, credential, code, issued,
    compact}. Compact rows (the dashboard) show when instead of the job title."""

    def __init__(self, **properties):
        super().__init__(**properties)
        h = self.item
        n = self.dom_nodes
        n["a"].setAttribute("href", "#verify/" + h["code"])
        if h.get("compact"):
            n["a"].className = "cs-honour compact"
        n["ini"].textContent = state.initials(h.get("name"))
        n["name"].textContent = h.get("name") or ""
        if h.get("compact"):
            n["title"].textContent = "%s · %s" % (h.get("credential") or "", cs.ago(h.get("issued")))
            n["cred"].hidden = True
        else:
            n["title"].textContent = h.get("title") or ""
            n["title"].hidden = not h.get("title")
            n["cred"].textContent = h.get("credential") or ""
