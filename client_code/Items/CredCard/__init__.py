from anvil import *

from ._anvil_designer import CredCardTemplate
from ... import cs


class CredCard(CredCardTemplate):
    """One of the member's credentials: a live thumbnail of the certificate, the name, code, date and status."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c = self.item
        n = self.dom_nodes
        n["a"].setAttribute("href", "#certificate/" + c["code"])
        n["title"].textContent = c["credential"]
        n["sub"].textContent = "%s · %s" % (c["code"], cs.date(c.get("issued")))
        revoked = c.get("status") == "revoked"
        self.status.text = "Revoked" if revoked else "Valid"
        self.status.role = ["badge", "badge-bad" if revoked else "badge-good"]
        self.cert.cert = c
