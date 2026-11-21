import anvil.server
from anvil import *

from ._anvil_designer import ReviewTemplate
from ... import cs, state


class Review(ReviewTemplate):
    """#review/<token>: a second-opinion link (Reviews.get_review / submit_review), public, no account. The reviewer
    sees the scenario, the member's answer and the rubric (no model answer), ticks criteria, adds a name and an
    optional comment and sends the verdict once; then the model answer and "Try this week's Boardroom Call" appear.
    Unknown or revoked links: "This link is no longer active"; used links say so."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self._token = args[0] if args else ""
        d: dict = anvil.server.call("get_review", self._token) if self._token else {"found": False}
        self._d = d
        self.model_part.visible = self.done_part.visible = False
        if not d.get("found") or d.get("used"):
            self.ready_part.visible, self.gone_part.visible = False, True
            self.hero.set(photo="ph-meeting", title="A second opinion", lead="")
            if d.get("used"):
                cs.set_text(self.dom_nodes["gone_head"], "This link has already been used")
                cs.set_text(self.dom_nodes["gone_text"], "A verdict was already sent with it, so %s has your opinion. Each link "
                            "works once." % (d.get("owner") or "the person who asked"))
            return
        self.ready_part.visible, self.gone_part.visible = True, False
        c, who = d["challenge"], d["owner"]
        cs.title("A second opinion for " + who)
        self.hero.set(photo=c["photo"], title="Would you mark %s's answer?" % who,
                      lead="%s practises boardroom decisions on C-Suite Coach and would value your honest view. About 3 minutes, "
                           "no account." % who,
                      meta=[["target", c["title"]], ["columns", "%s · %s" % (d["module"]["track"], d["module"]["title"])]])
        n = self.dom_nodes
        cs.set_text(n["intro"], "Read the situation and %s's answer, then tick each criterion the answer really covers. Be "
                    "candid: an honest outside view is the point." % who)
        cs.set_text(n["situation"], c["situation"])
        cs.set_text(n["ask"], c["ask"])
        cs.set_text(n["answer_head"], "%s's answer" % who)
        cs.set_text(n["answer"], d.get("answer") or "")
        self.rubric.items = c["rubric"]
        state.set_control_attr(self.name_box, "maxlength", "60")
        state.set_control_attr(self.name_box, "autocomplete", "name")
        state.set_control_attr(self.comment_box, "maxlength", "1000")

    @handle("send_button", "click")
    def send_button_click(self, **event_args):
        name = (self.name_box.text or "").strip()
        if len(name) < 2:
            state.toast("Add your name, so they know whose opinion it is.", "error")
            state.focus(self.name_box)
            return
        self.send_button.enabled = False
        r = state.call("submit_review", self._token, name, self.rubric.value(), self.comment_box.text or "")
        if not r:
            self.send_button.enabled = True
            return
        self.rubric.lock()
        self.form_part.visible = False
        self.done_part.visible = True
        n = self.dom_nodes
        cs.set_text(n["done_pct"], "%d%%" % r["score"])
        cs.set_text(n["done_text"], "%s will see your score and comment next to their own marks. Here is the examiners' model "
                    "answer, so you can compare." % r["owner"])
        cs.set_text(n["model"], r["model"])
        self.model_part.visible = True
        self.done_part.scroll_into_view(smooth=True)
