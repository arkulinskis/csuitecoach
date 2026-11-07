from anvil import *

from ._anvil_designer import ModuleRowTemplate


class ModuleRow(ModuleRowTemplate):
    """A module in a program: number, title, summary, minutes / drills / challenge, and (members) progress."""

    def __init__(self, **properties):
        super().__init__(**properties)
        m = self.item
        st = m.get("status")
        n = self.dom_nodes
        n["a"].setAttribute("href", "#module/" + m["id"])
        n["num"].textContent = str(m["n"])
        n["title"].textContent = m["title"]
        n["summary"].textContent = m.get("summary") or ""
        n["mins"].textContent = "%d min" % m["minutes"]
        n["drills"].textContent = "%d drills" % m["items"]
        n["ch"].textContent = m["challenge"]["title"]
        badge = n["st"]
        if st and st.get("complete"):
            badge.className, badge.hidden = "ui-badge good", False
            badge.innerHTML = '<i class="ic ic-check"></i>Complete'
        elif st and st.get("pct"):
            badge.className, badge.hidden = "ui-badge brand", False
            badge.textContent = "%d%% · %d/3 steps" % (st["pct"], st["steps"])
        self.ring_box.visible = bool(st)
        self.members_badge.visible = not st
        if st:
            self.ring.pct = st["pct"]
