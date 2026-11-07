from anvil import *

from ._anvil_designer import CredAdminRowTemplate
from ... import cs, state


class CredAdminRow(CredAdminRowTemplate):
    """Admin → Credentials: one issued credential with its Revoked switch (saved straight away; the public
    certificate and verification pages show the new status at once)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c = self.item
        n = self.dom_nodes
        n["holder"].textContent = c["holder"]
        n["demo"].hidden = not c.get("demo")
        n["email"].textContent = c.get("email") or ""
        n["credential"].textContent = c["credential"]
        n["issued"].textContent = cs.date(c.get("issued"))
        n["code"].textContent = c["code"]
        n["code"].setAttribute("href", "#certificate/" + c["code"])
        self.revoked_box.checked = c.get("status") == "revoked"
        state.set_control_attr(self.revoked_box, "aria-label", "Revoked: " + c["code"])

    @handle("revoked_box", "change")
    def revoked_box_change(self, **event_args):
        on = self.revoked_box.checked
        r = state.call("admin_set_revoked", self.item["code"], on)
        if r:
            state.toast("Credential revoked" if on else "Credential reinstated", "ok")
        else:
            self.revoked_box.checked = not on
