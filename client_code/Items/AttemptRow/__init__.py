from anvil import *

from ._anvil_designer import AttemptRowTemplate
from ... import cs


class AttemptRow(AttemptRowTemplate):
    """A past attempt at a challenge (opens to show the answer and "Ask for a second opinion", which raises x-ask on
    the panel; Pages/Challenge makes the link). item = {id, created, score, answer, pass_mark, member}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        a = self.item
        n = self.dom_nodes
        n["when"].textContent = cs.date(a.get("created"), "time")
        n["score"].textContent = "%d%%" % a["score"]
        n["score"].className = "good" if a["score"] >= a.get("pass_mark", 70) else "warn"
        n["answer"].textContent = a.get("answer") or ""
        self.ask_button.visible = bool(a.get("member") and a.get("id"))

    @handle("ask_button", "click")
    def ask_button_click(self, **event_args):
        if self.parent is not None:
            self.parent.raise_event("x-ask", attempt_id=self.item.get("id"))
