from anvil import *
from anvil.js import window

from ._anvil_designer import CertificateTemplate
from ... import cs


class Certificate(CertificateTemplate):
    """The certificate engine (cs-cert.js) in a component: draws on `cert`, keeps itself scaled to its width while it
    is on the page (ResizeObserver), and lets go of its listeners when the page goes."""

    def __init__(self, **properties):
        self._cert, self._decorative, self._stop, self._ready = None, False, None, False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        wrap = self.dom_nodes["wrap"]
        if self._stop is not None:
            self._stop()
            self._stop = None
        if not self._cert:
            wrap.innerHTML = ""
            return
        wrap.innerHTML = window.CS.cert(cs.js(self._cert))
        if self._decorative:
            wrap.setAttribute("aria-hidden", "true")
        self._stop = window.CS.fitCert(wrap)

    @handle("", "hide")
    def form_hide(self, **event_args):
        if self._stop is not None:
            self._stop()
            self._stop = None

    @handle("", "show")
    def form_show(self, **event_args):
        if self._stop is None and self._cert:
            self._stop = window.CS.fitCert(self.dom_nodes["wrap"])

    @property
    def cert(self):
        return self._cert

    @cert.setter
    def cert(self, value):
        self._cert = value
        self._draw()

    @property
    def decorative(self):
        return self._decorative

    @decorative.setter
    def decorative(self, value):
        self._decorative = bool(value)
        self._draw()
