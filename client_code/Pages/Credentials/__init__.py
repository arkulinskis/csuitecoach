from anvil import *

from ._anvil_designer import CredentialsTemplate
from ... import state


class Credentials(CredentialsTemplate):
    """#credentials: the member's certificates (my_credentials), the path to the Fellowship, and the Honour Roll
    opt-in (update_profile, saved at once)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        d = state.call("my_credentials")
        if not d:
            return
        valid = len([c for c in d["items"] if c["status"] == "valid"])
        self.hero.set(photo="ph-signing", title="Your credentials",
                      lead="Every credential has a public verification page on the Institute's register. Share the link, "
                           "print the certificate, or add it to LinkedIn.",
                      meta=[["award", state.plural(valid, "credential")],
                            ["shield", "On the Honour Roll" if d["honour_roll"] else "Not on the Honour Roll"]])
        self.creds_panel.items = d["items"]
        self.empty.visible = not d["items"]
        self.creds_panel.visible = bool(d["items"])
        f = d["fellow"]
        self.dom_nodes["fellow_count"].textContent = "Achieved" if f["have"] else "%d of 3" % ((1 if f["core"] else 0) + f["roles"])
        self.path_panel.items = d["tracks"]
        self.honour_box.checked = d["honour_roll"]

    @handle("honour_box", "change")
    def honour_box_change(self, **event_args):
        on = self.honour_box.checked
        r = state.call("update_profile", state.me()["name"], None, on)
        if r:
            state.set_me(r["me"])
            state.toast("You're on the Honour Roll" if on else "Removed from the Honour Roll", "ok")
        else:
            self.honour_box.checked = not on
