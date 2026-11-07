import anvil.server
from anvil import *

from ._anvil_designer import VerifyTemplate
from ... import cs, router, state


class Verify(VerifyTemplate):
    """#verify, #verify/<code>: public verification against the Institute's register (get_credential), plus the
    public Honour Roll (get_honour_roll). A lookup changes the address to #verify/<CODE>, so it can be shared."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.hero.set(photo="ph-signing", title="Verify a credential",
                      lead="Enter a credential ID to confirm it was issued by the C-Suite Coach Institute and is still valid.")
        state.set_control_attr(self.code_box, "aria-label", "Credential ID")
        code = args[0] if args else ""
        self.code_box.text = code
        roll = anvil.server.call_s("get_honour_roll")["items"]
        self.roll_panel.items = roll
        self.no_roll.visible = not roll
        self.roll_panel.visible = bool(roll)
        if code:
            self._check(code)

    def _check(self, code):
        r = anvil.server.call("get_credential", code)
        n = self.dom_nodes
        n["res_box"].hidden = False
        if r.get("ok") is False:
            self._result("bad", "alert", "Please wait", r.get("error"))
            return
        if not r.get("found"):
            self._result("bad", "alert", "Not found", "No credential with the ID %s is on the register. Check for typos." % code.upper())
            return
        valid = r["status"] == "valid"
        self._result("ok" if valid else "bad", "shield" if valid else "alert",
                     "Verified: a valid credential" if valid else "Revoked: no longer valid", "")
        self.res_dl.visible = True
        cs.set_text(n["holder"], r["holder"])
        cs.set_text(n["credential"], r["credential"])
        cs.set_text(n["issued"], cs.date(r["issued"], "long"))
        cs.set_text(n["code"], r["code"])
        n["sample"].hidden = not r.get("demo")
        n["view"].setAttribute("href", "#certificate/" + r["code"])
        n["view"].hidden = False

    def _result(self, kind, icon, head, text):
        n = self.dom_nodes
        n["res_box"].className = "vf-res " + kind
        n["res_ic"].className = "ic ic-" + icon
        cs.set_text(n["res_head"], head)
        cs.set_text(n["res_text"], text)
        n["res_text"].hidden = not text
        self.res_dl.visible = False
        n["view"].hidden = True

    @handle("code_box", "pressed_enter")
    def code_box_pressed_enter(self, **event_args):
        self.verify_button_click()

    @handle("verify_button", "click")
    def verify_button_click(self, **event_args):
        code = (self.code_box.text or "").strip()
        if not code:
            return
        router.replace("verify", code.upper())
        self._check(code)
