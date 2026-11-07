from anvil import *
import anvil.js

from ._anvil_designer import RubricRowTemplate


class RubricRow(RubricRowTemplate):
    """One criterion of a rubric: a real tick box in a bordered row that turns green when ticked.
    item = {text, i, on, locked} (the Rubric component reads item["on"])."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.item["_form"] = self
        self.dom_nodes["text"].textContent = self.item["text"]
        box = self.dom_nodes["box"]
        box.checked = bool(self.item.get("on"))
        box.disabled = bool(self.item.get("locked"))
        self.row.classes["on"] = bool(self.item.get("on"))
        box.addEventListener("change", anvil.js.report_exceptions(self._change))

    def _change(self, event):
        on = bool(self.dom_nodes["box"].checked)
        self.item["on"] = on
        self.row.classes["on"] = on

    def lock(self):
        self.dom_nodes["box"].disabled = True
