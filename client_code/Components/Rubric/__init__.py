from anvil import *

from ._anvil_designer import RubricTemplate


class Rubric(RubricTemplate):
    """The examiners' criteria, ticked by the member. value() -> [bool, ...]; lock() disables every box."""

    def __init__(self, **properties):
        self._items: list = []
        self._rows: list = []
        self._ready = False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        self._rows = [{"text": t, "i": i, "on": False, "locked": False} for i, t in enumerate(self._items or [])]
        self.panel.items = self._rows

    def value(self):
        return [bool(r["on"]) for r in self._rows]

    def lock(self):
        for r in self._rows:
            r["locked"] = True
            form = r.get("_form")
            if form is not None:
                form.lock()

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, value):
        self._items = list(value or [])
        self._draw()
