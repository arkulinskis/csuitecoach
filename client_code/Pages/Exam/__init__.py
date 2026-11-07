import anvil.js
import anvil.server
from anvil import *

from ._anvil_designer import ExamTemplate
from ... import cs, state

PARTS = ["intro_part", "part1", "part2", "result_part", "other_part", "hist_part", "missing_part"]


class Exam(ExamTemplate):
    """#exam/<track>: the final examination. get_exam returns a state: locked (modules missing), cooldown (retake
    later), certified, or ready (with the paper). Ready: honour code -> Part I recall round (the Drill in exam mode,
    ratings kept in the page) -> Part II capstone (write, compare, tick the rubric) -> submit_exam -> the result and,
    on a pass, the new certificate. The server checks every rule again (honour code, every item rated, retakes)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.track = args[0] if args else ""
        self.ratings: dict = {}
        self.answer = ""
        self._show()
        self.dom_nodes["honour"].addEventListener("change", anvil.js.report_exceptions(self._honour))
        r = anvil.server.call("get_exam", self.track)
        if not r.get("ok"):
            self.hero.set(photo="ph-signing", title="Examination not found", crumbs=[["#tracks", "Programs"], [None, "Not found"]])
            self._show("missing_part")
            return
        self.d = r
        cs.title("Examination: " + r["track"]["title"])
        self._head()
        self.hist_panel.items = r["history"]
        if r["state"] == "ready":
            self._intro()
        else:
            self._other()

    def _show(self, *names):
        for p in PARTS:
            getattr(self, p).visible = p in names

    def _head(self, sub=None):
        t = self.d["track"]
        self.hero.set(photo="ph-signing", title="Final examination: " + t["title"], lead=sub or ("For the %s." % t["credential"]),
                      crumbs=[["#tracks", "Programs"], ["#tracks/" + t["id"], t["title"]], [None, "Examination"]])

    # ---- ready
    def _intro(self):
        d, n = self.d, self.dom_nodes
        cs.set_text(n["r1n"], len(d["items"]))
        cs.set_text(n["r1"], "Part I: recall drills from the whole program. %d%% \u201cGot it\u201d to pass." % d["pass_drill"])
        cs.set_text(n["r2"], "Part II: the capstone case \u201c%s\u201d. %d%% of the rubric to pass." % (d["capstone"]["title"], d["pass_scenario"]))
        cs.set_text(n["r3n"], "%d\u2032" % d["retake_minutes"])
        cs.set_text(n["r3"], "If you don't pass, you can sit it again after %d minutes." % d["retake_minutes"])
        n["not_now"].setAttribute("href", "#tracks/" + d["track"]["id"])
        self._show("intro_part", *(["hist_part"] if d["history"] else []))

    def _honour(self, event):
        self.begin_button.enabled = bool(self.dom_nodes["honour"].checked)

    @handle("begin_button", "click")
    def begin_button_click(self, **event_args):
        self._head("Part I of II: recall")
        self._show("part1")
        anvil.js.window.scrollTo(0, 0)
        self.drill.start(self.d["items"], exam=True, rate=self._rate, done=self._part2)

    def _rate(self, item, knew):
        self.ratings[item["id"]] = bool(knew)

    def _part2(self, stats):
        c, n = self.d["capstone"], self.dom_nodes
        self._head("Part II of II: the capstone case")
        cs.set_text(n["cap_title"], c["title"])
        cs.set_text(n["cap_sit"], c["situation"])
        cs.set_text(n["cap_ask"], c["ask"])
        state.set_control_attr(self.answer_box, "maxlength", "8000")
        self.answer_box.text = self.answer
        self.write_part.visible, self.mark_part.visible = True, False
        self._show("part2")
        anvil.js.window.scrollTo(0, 0)

    @handle("write_button", "click")
    def write_button_click(self, **event_args):
        self.answer = (self.answer_box.text or "").strip()
        if len(self.answer) < 80:
            state.toast("Write at least a short paragraph (80 characters).", "error")
            return
        c, n = self.d["capstone"], self.dom_nodes
        cs.set_text(n["mine"], self.answer)
        cs.set_text(n["model"], c["model"])
        self.rubric.items = c["rubric"]
        self.write_part.visible, self.mark_part.visible = False, True
        self.mark_part.scroll_into_view(smooth=True)

    @handle("final_button", "click")
    def final_button_click(self, **event_args):
        self.final_button.enabled = False
        r = state.call("submit_exam", self.d["exam_id"], self.ratings, self.answer, self.rubric.value(), True, cs.today())
        if not r:
            self.final_button.enabled = True
            return
        self._result(r)

    def _result(self, r):
        d, n = self.d, self.dom_nodes
        self._head("Congratulations." if r["passed"] else "Not passed this time.")
        cs.set_text(n["res_head"], "The Board of Examiners has issued your credential" if r["passed"] else "Result")
        cs.set_text(n["res_drill"], "%d%%" % r["drill"])
        n["res_drill"].className = "good" if r["drill"] >= d["pass_drill"] else "bad"
        cs.set_text(n["res_drill_l"], "Recall (%d%% to pass)" % d["pass_drill"])
        cs.set_text(n["res_scen"], "%d%%" % r["scenario"])
        n["res_scen"].className = "good" if r["scenario"] >= d["pass_scenario"] else "bad"
        cs.set_text(n["res_scen_l"], "Capstone (%d%% to pass)" % d["pass_scenario"])
        self.passed_box.visible, self.failed_box.visible = r["passed"], not r["passed"]
        if r["passed"]:
            n["open_cert"].setAttribute("href", "#certificate/" + r["code"])
            self.fellow_note.visible = bool(r.get("fellow"))
            if r.get("fellow"):
                n["fellow_a"].setAttribute("href", "#certificate/" + r["fellow"])
            c = anvil.server.call_s("get_credential", r["code"])
            if c and c.get("found"):
                self.new_cert.cert = c
            cs.confetti()
        else:
            cs.set_text(n["fail_text"], "Review the drills you missed (they're due again today) and the capstone criteria. "
                        "You can sit the examination again in %d minutes." % r["retake_minutes"])
            n["back_track"].setAttribute("href", "#tracks/" + d["track"]["id"])
        self._show("result_part")
        anvil.js.window.scrollTo(0, 0)

    # ---- locked / cooldown / certified
    def _other(self):
        d, n = self.d, self.dom_nodes
        st = d["state"]
        self.certified_box.visible = st == "certified"
        self.cooldown_box.visible = st == "cooldown"
        self.locked_box.visible = st == "locked"
        if st == "certified":
            cs.set_text(n["cert_head"], "Already certified: you hold the " + d["track"]["credential"])
            n["cert_link"].setAttribute("href", "#certificate/" + d["status"]["credential"]["code"])
        elif st == "cooldown":
            cs.set_text(n["wait_head"], "Please wait: you can sit the examination again in " + state.plural(d["minutes"], "minute"))
        else:
            cs.set_text(n["locked_text"], "The examination opens when all %d modules are complete. Still to finish:" % d["status"]["modules"])
            self.missing_panel.items = d.get("missing") or []
        self._show("other_part", *(["hist_part"] if d["history"] else []))
