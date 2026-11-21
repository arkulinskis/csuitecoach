from anvil import *

from ._anvil_designer import PlanWeekTemplate
from ... import cs


class PlanWeek(PlanWeekTemplate):
    """One week card of a 90-day plan (Pages/Ninety), with the phase heading above weeks 1, 5 and 9 and its steps in
    a nested RepeatingPanel of Items/PlanStep. item = {n, phase {name, line, first}, steps, now, tickable}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        w, n = self.item, self.dom_nodes
        ph = w["phase"]
        self.phase_box.visible = bool(ph.get("first"))
        cs.set_text(n["phase_name"], ph.get("name"))
        cs.set_text(n["phase_line"], ph.get("line"))
        cs.set_text(n["title"], "Week %d" % w["n"])
        self.card.classes["now"] = bool(w.get("now"))
        steps = w["steps"]
        if w.get("now"):
            badge, cls = "This week", "ui-badge gold"
        elif w.get("tickable"):
            done = sum(1 for s in steps if s.get("done"))
            badge, cls = "%d of %d done" % (done, len(steps)), "ui-badge good" if done == len(steps) else "ui-badge"
        else:
            badge, cls = ph.get("name") or "", "ui-badge"
        cs.set_text(n["badge"], badge)
        n["badge"].className = cls
        self.steps_panel.items = steps
