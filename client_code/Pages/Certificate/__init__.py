import anvil.server
from anvil import *
from anvil.js import window

from ._anvil_designer import CertificateTemplate
from ...Dialogs.LinkBox import LinkBox
from ... import cs, state


class Certificate(CertificateTemplate):
    """#certificate/<code>: public. The printable certificate (the cs-cert.js engine) with its verification status,
    copy link, print / save as PDF, and Add to LinkedIn for its holder. get_credential."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.code = args[0] if args else ""
        r = anvil.server.call("get_credential", self.code)
        found = bool(r and r.get("found"))
        self.found_part.visible, self.missing_part.visible = found, not found
        if not found:
            if r and r.get("ok") is False:
                cs.set_text(self.dom_nodes["missing_text"], r.get("error"))
            return
        c = r
        cs.title("%s, %s" % (c["holder"], c["credential"]))
        n = self.dom_nodes
        cs.set_text(n["title"], c["credential"])
        self.cert.cert = c
        url = cs.verify_url(c["code"])
        d = window.Date(c["issued"])
        q = window.encodeURIComponent
        li = ("https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&name=" + q(c["credential"]) +
              "&organizationName=" + q(cs.INSTITUTE) + "&issueYear=%d&issueMonth=%d" % (d.getFullYear(), d.getMonth() + 1) +
              "&certUrl=" + q(url) + "&certId=" + q(c["code"]))
        n["linkedin_a"].hidden = not (c.get("mine") and c["status"] == "valid")
        n["linkedin_a"].setAttribute("href", li)
        valid = c["status"] == "valid"
        self.valid_box.visible, self.revoked_box.visible = valid, not valid
        cs.set_text(n["valid_text"], "Issued by the C-Suite Coach Institute and recorded on its register." +
                    (" This is a sample record from the Institute's demonstration data." if c.get("demo") else ""))
        cs.set_text(n["holder"], c["holder"])
        cs.set_text(n["code"], c["code"])
        cs.set_text(n["issued"], cs.date(c["issued"], "long"))
        cs.set_text(n["program"], c["title"])
        self.outcomes_card.visible = bool(c.get("outcomes"))
        self.outcomes_panel.items = c.get("outcomes") or []

    @handle("print_button", "click")
    def print_button_click(self, **event_args):
        window.print()

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        url = cs.verify_url(self.code.upper())
        try:
            window.navigator.clipboard.writeText(url)
            state.toast("Verification link copied", "ok")
        except Exception:
            alert(LinkBox(link=url), buttons=[], role="app-dialog")
