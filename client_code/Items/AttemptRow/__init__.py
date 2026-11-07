from anvil import *

from ._anvil_designer import AttemptRowTemplate
from ... import cs


class AttemptRow(AttemptRowTemplate):
    """A past attempt at a challenge (opens to show the answer). item = {created, score, answer, pass_mark}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        a = self.item
        n = self.dom_nodes
        n["when"].textContent = cs.date(a.get("created"), "time")
        n["score"].textContent = "%d%%" % a["score"]
        n["score"].className = "good" if a["score"] >= a.get("pass_mark", 70) else "warn"
        n["answer"].textContent = a.get("answer") or ""
