from anvil import *

from ._anvil_designer import ExamRowTemplate
from ... import cs


class ExamRow(ExamRowTemplate):
    """A previous sitting of a final examination. item = {finished, drill, scenario, passed}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        h = self.item
        n = self.dom_nodes
        n["when"].textContent = cs.date(h.get("finished"), "time")
        n["drill"].textContent = "%d%%" % h["drill"]
        n["scenario"].textContent = "%d%%" % h["scenario"]
        n["res"].className = "ui-badge good" if h["passed"] else "ui-badge warn"
        n["res"].textContent = "Passed" if h["passed"] else "Not passed"
