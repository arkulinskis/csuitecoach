from anvil import *
from anvil.js import window

from ._anvil_designer import RingTemplate


class Ring(RingTemplate):
    """A progress ring drawn by the cs-cert.js engine."""

    def __init__(self, **properties):
        self._pct, self._size, self._label, self._ready = 0, 64, "", False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if self._ready:
            self.dom_nodes["box"].innerHTML = window.CS.ring(self._pct or 0, self._size or 64, self._label or "")

    @property
    def pct(self):
        return self._pct

    @pct.setter
    def pct(self, value):
        self._pct = value or 0
        self._draw()

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = int(value or 64)
        self._draw()

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value or ""
        self._draw()
