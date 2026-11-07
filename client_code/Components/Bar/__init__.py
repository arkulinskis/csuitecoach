from anvil import *

from ._anvil_designer import BarTemplate


class Bar(BarTemplate):
    """A progress bar: pct 0-100."""

    def __init__(self, **properties):
        self._pct, self._label, self._ready = 0, "Progress", False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        p = max(0, min(100, int(round(self._pct or 0))))
        self.dom_nodes["fill"].style.transform = "scaleX(%s)" % (p / 100.0)
        bar = self.dom_nodes["bar"]
        bar.setAttribute("aria-valuenow", str(p))
        bar.setAttribute("aria-label", self._label or "Progress")

    @property
    def pct(self):
        return self._pct

    @pct.setter
    def pct(self, value):
        self._pct = value or 0
        self._draw()

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value or "Progress"
        self._draw()
