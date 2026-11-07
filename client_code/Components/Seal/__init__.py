from anvil import *
from anvil.js import window

from ._anvil_designer import SealTemplate


class Seal(SealTemplate):
    """The Institute's seal (an SVG drawn by the cs-cert.js engine)."""

    def __init__(self, **properties):
        self._size, self._decorative, self._ready = 120, False, False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        box = self.dom_nodes["box"]
        box.innerHTML = window.CS.seal(self._size or 120)
        if self._decorative:
            box.setAttribute("aria-hidden", "true")
        else:
            box.removeAttribute("aria-hidden")

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = int(value or 120)
        self._draw()

    @property
    def decorative(self):
        return self._decorative

    @decorative.setter
    def decorative(self, value):
        self._decorative = bool(value)
        self._draw()
