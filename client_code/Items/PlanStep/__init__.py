from anvil import *
import anvil.js

from ._anvil_designer import PlanStepTemplate
from ... import cs


class PlanStep(PlanStepTemplate):
    """One step of a 90-day plan: the action, why (one line), a module or case link and the source. A tick box when
    it's the member's saved plan (the page saves it: item["host"].tick(step_id, done) -> False to undo).
    item = {id, text, why, source {label, url}, link, link_label, tag, tickable, done, host}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        s, n = self.item, self.dom_nodes
        cs.set_text(n["text"], s["text"])
        n["tag"].hidden = not s.get("tag")
        cs.set_text(n["tag"], s.get("tag") or "")
        cs.set_text(n["why"], s["why"])
        n["link"].setAttribute("href", s["link"])
        cs.set_text(n["link"], s.get("link_label") or "Read more")
        n["src"].setAttribute("href", s["source"]["url"])
        cs.set_text(n["src"], "Source: " + s["source"]["label"])
        tickable = bool(s.get("tickable"))
        self.tick_box.visible, self.dot.visible = tickable, not tickable
        box = n["box"]
        box.checked = bool(s.get("done"))
        box.setAttribute("aria-label", "Done: " + s["text"])
        self.row.classes["done"] = bool(s.get("done"))
        box.addEventListener("change", anvil.js.report_exceptions(self._change))

    def _change(self, event):
        box = self.dom_nodes["box"]
        on = bool(box.checked)
        host = self.item.get("host")
        if host is not None and host.tick(self.item["id"], on) is False:
            box.checked = not on
            return
        self.item["done"] = on
        self.row.classes["done"] = on
