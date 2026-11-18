from anvil import *

from ._anvil_designer import TeamTrackTemplate


class TeamTrack(TeamTrackTemplate):
    """One assigned program in a team member's row: title, modules done, progress bar, Certified.
    item = {title, pct, modules_done, modules, certified}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        t = self.item
        self.dom_nodes["title"].textContent = t["title"]
        self.bar.pct = t.get("pct") or 0
        self.bar.label = "%s progress" % t["title"]
        if t.get("certified"):
            self.state_label.text, self.state_label.role = "Certified", ["badge", "badge-gold", "ic-award"]
        else:
            self.state_label.text = "%d/%d modules · %d%%" % (t.get("modules_done") or 0, t.get("modules") or 0, t.get("pct") or 0)
            self.state_label.role = ["fine-print"]
