from anvil import *

from ._anvil_designer import HomeTrackTemplate
from ... import cs


class HomeTrack(HomeTrackTemplate):
    """A program row on the dashboard: photo, title, modules done, progress, certified / exam open / percent."""

    def __init__(self, **properties):
        super().__init__(**properties)
        t = self.item
        s = t["status"]
        n = self.dom_nodes
        n["a"].setAttribute("href", "#tracks/" + t["id"])
        n["th"].style.backgroundImage = "url(%s)" % cs.photo(t.get("photo"))
        n["title"].textContent = t["title"]
        n["sub"].textContent = "%s · %d/%d modules" % (t.get("role") or "", s["modules_done"], s["modules"])
        self.bar.pct = s["pct"]
        self.bar.label = "%s progress" % t["title"]
        if s.get("certified"):
            self.state_label.text, self.state_label.role = "Certified", ["badge", "badge-gold", "ic-award"]
        elif s.get("exam_ready"):
            self.state_label.text, self.state_label.role = "Exam open", ["badge", "badge-brand"]
        else:
            self.state_label.text, self.state_label.role = "%d%%" % s["pct"], ["fine-print"]
