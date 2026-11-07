from anvil import *

from ._anvil_designer import TrackCardTemplate
from ... import cs


class TrackCard(TrackCardTemplate):
    """A program as a photo card (landing, catalogue). item = a track from get_catalog."""

    def __init__(self, **properties):
        super().__init__(**properties)
        t = self.item
        s = t.get("status") or {}
        n = self.dom_nodes
        n["a"].setAttribute("href", "#tracks/" + t["id"])
        n["img"].style.backgroundImage = "url(%s)" % cs.photo(t.get("photo"))
        n["code"].textContent = t.get("code") or ""
        n["done"].hidden = not s.get("certified")
        n["role"].textContent = t.get("role") or ""
        n["title"].textContent = t.get("title") or ""
        n["blurb"].textContent = t.get("blurb") or ""
        self.bar_box.visible = bool(s.get("started"))
        self.bar.pct = s.get("pct") or 0
        self.bar.label = "%s progress" % t.get("title")
        n["counts"].textContent = "%d modules · %d drills · %d challenges" % (len(t.get("modules") or []), t.get("items") or 0,
                                                                            t.get("challenges") or 0)
        n["hours"].textContent = "~%s h" % cs.hours(t.get("minutes"))
