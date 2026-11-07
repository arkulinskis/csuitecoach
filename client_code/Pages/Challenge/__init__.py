import anvil.server
from anvil import *

from ._anvil_designer import ChallengeTemplate
from ... import cs, state


class Challenge(ChallengeTemplate):
    """#challenge/<id>: a module's boardroom scenario. Write a decision, then the examiners' model answer and rubric
    appear; tick what the answer covered (self-assessed, 70% to pass). get_challenge, submit_challenge."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.id = args[0] if args else ""
        self.answer = ""
        self._load()

    def _load(self):
        r = anvil.server.call("get_challenge", self.id)
        if not r.get("ok"):
            self.hero.set(title="Challenge not found", crumbs=[["#tracks", "Programs"], [None, "Not found"]])
            self.body.visible, self.missing_part.visible = False, True
            return
        self.missing_part.visible = False
        self.d = r
        c, m = r["challenge"], r["module"]
        cs.title(c["title"])
        self.hero.set(photo=c["photo"], title=c["title"],
                      crumbs=[["#tracks/" + m["track_id"], m["track"]], ["#module/" + m["id"], "Module %d: %s" % (m["n"], m["title"])],
                              [None, "Challenge"]],
                      meta=[["target", "%d%% of the rubric to pass" % r["pass_mark"]],
                            ["star", ("Your best: %d%%" % r["best"]) if r["best"] else "First attempt"]])
        n = self.dom_nodes
        cs.set_text(n["situation"], c["situation"])
        cs.set_text(n["ask"], c["ask"])
        cs.set_text(n["how"], "After you submit, you'll see the examiners' model answer and %d criteria. Tick each one your "
                    "answer genuinely covered. Be strict: the drill is for you." % len(c["rubric"]))
        self.attempts_panel.items = [dict(a, pass_mark=r["pass_mark"]) for a in r["attempts"]]
        self.no_attempts.visible = not r["attempts"]
        self.attempts_panel.visible = bool(r["attempts"])
        state.set_control_attr(self.answer_box, "maxlength", "6000")
        self.answer_box.text = self.answer
        self.write_part.visible, self.model_part.visible = True, False

    @handle("submit_button", "click")
    def submit_button_click(self, **event_args):
        self.answer = (self.answer_box.text or "").strip()
        if len(self.answer) < 40:
            state.toast("Write a few sentences first (at least 40 characters).", "error")
            return
        c = self.d["challenge"]
        cs.set_text(self.dom_nodes["mine"], self.answer)
        cs.set_text(self.dom_nodes["model"], c["model"])
        self.rubric.items = c["rubric"]
        self.write_part.visible, self.model_part.visible = False, True
        self.score_actions.visible, self.result_box.visible = True, False
        self.record_button.enabled = True
        self.model_part.scroll_into_view(smooth=True)

    @handle("edit_button", "click")
    def edit_button_click(self, **event_args):
        self.write_part.visible, self.model_part.visible = True, False

    @handle("record_button", "click")
    def record_button_click(self, **event_args):
        self.record_button.enabled = False
        r = state.call("submit_challenge", self.id, self.answer, self.rubric.value(), cs.today())
        if not r:
            self.record_button.enabled = True
            return
        self.rubric.lock()
        self.score_actions.visible = False
        d, n = self.d, self.dom_nodes
        self.result_box.visible = True
        self.result_box.classes["pass"], self.result_box.classes["fail"] = r["passed"], not r["passed"]
        cs.set_text(n["res_head"], "Passed" if r["passed"] else "Not yet")
        cs.set_text(n["res_pct"], "%d%%" % r["score"])
        if r["passed"]:
            text = "Module complete. Well done." if r["module_completed"] else "Challenge passed. Finish the drills to complete the module."
        else:
            text = "You need %d%%. Study the model answer and try again." % d["pass_mark"]
        cs.set_text(n["res_text"], "%s +%d XP" % (text, r["xp_gained"]))
        n["res_back"].setAttribute("href", "#module/" + d["module"]["id"])
        self.retry_button.visible = not r["passed"]
        if r["passed"]:
            cs.confetti()

    @handle("retry_button", "click")
    def retry_button_click(self, **event_args):
        self.answer = ""
        self._load()
