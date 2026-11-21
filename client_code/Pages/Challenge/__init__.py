import json

import anvil.server
from anvil import *
from anvil.js import window

from ._anvil_designer import ChallengeTemplate
from ... import cs, router, state

PENDING = "pending_call"     # a visitor's scored answer, kept in this browser until they create an account
DAY_MS = 24 * 3600 * 1000    # pending answers older than this are ignored


class Challenge(ChallengeTemplate):
    """#challenge/<id>: a module's boardroom scenario. Write a decision, then the examiners' model answer and rubric
    appear (reveal_challenge: never before the answer is written); tick what the answer covered (self-assessed, 70% to
    pass).

    Members: get_challenge, submit_challenge, their attempts and second opinions (Reviews: create_review_link,
    my_reviews, revoke_review). Visitors (no account, 2026-11-20): get_challenge_preview opens every program's first
    module challenge and this week's Boardroom Call (#call); others show "Enrol free". A visitor's score is worked out
    here, and the attempt waits in this browser (PENDING) until they create an account: back on this page signed in,
    it is submitted for them (nothing to retype). No visitor data goes to the server before that."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.id = args[0] if args else ""
        self.answer = ""
        self.member = bool(state.me())
        self.revealed = None
        self.attempt_id = None
        self.attempts_panel.add_event_handler("x-ask", self._ask_event)
        self.reviews_panel.add_event_handler("x-copy", self._copy_event)
        self.reviews_panel.add_event_handler("x-revoke", self._revoke_event)
        self._load()
        if self.member:
            self._save_pending()

    # ---------------------------------------------------------------- loading
    def _load(self):
        fn = "get_challenge" if self.member else "get_challenge_preview"
        r = anvil.server.call(fn, self.id, cs.today())
        if not r.get("ok"):
            self.hero.set(title="Challenge not found", crumbs=[["#tracks", "Programs"], [None, "Not found"]])
            self.body.visible, self.locked_part.visible, self.missing_part.visible = False, False, True
            return
        self.missing_part.visible = False
        self.d = r
        c, m = r["challenge"], r["module"]
        cs.title(c["title"])
        crumbs = [["#tracks/" + m["track_id"], m["track"]], ["#module/" + m["id"], "Module %d: %s" % (m["n"], m["title"])],
                  [None, "Challenge"]]
        if not self.member and not r.get("allowed"):
            self.hero.set(photo=c["photo"], title=c["title"], crumbs=crumbs, meta=[["lock", "Members' challenge"]])
            cs.set_text(self.dom_nodes["locked_text"], "“%s” is part of module %d of %s. Create a free account to "
                        "take every challenge, keep your scores and work towards a certificate." % (c["title"], m["n"], m["track"]))
            self.body.visible, self.locked_part.visible = False, True
            return
        self.body.visible, self.locked_part.visible = True, False
        meta = [["target", "%d%% of the rubric to pass" % r["pass_mark"]]]
        if self.member:
            meta.append(["star", ("Your best: %d%%" % r["best"]) if r["best"] else "First attempt"])
        else:
            meta.append(["clock", "About 5 minutes, no account"])
        if r.get("is_call"):
            meta.insert(0, ["calendar", "This week's Boardroom Call · %s left" % state.plural(r["days_left"], "day")])
        self.hero.set(photo=c["photo"], title=c["title"], crumbs=crumbs, meta=meta)
        n = self.dom_nodes
        cs.set_text(n["situation"], c["situation"])
        cs.set_text(n["ask"], c["ask"])
        cs.set_text(n["how"], "After you submit, you'll see the examiners' model answer and %d criteria. Tick each one your "
                    "answer genuinely covered. Be strict: the drill is for you." % c["rubric_count"])
        self.call_card.visible = bool(r.get("is_call"))
        if r.get("is_call"):
            cs.set_text(n["call_text"], "A new real decision every Monday. Anyone can make the call in five minutes, without "
                        "an account. %s left on this one: send it to a colleague and compare." % state.plural(r["days_left"], "day"))
            n["li_share"].setAttribute("href", cs.linkedin_share(cs.app_url("#call")))
        self.guest_card.visible = not self.member
        self.attempts_card.visible = self.reviews_card.visible = self.member
        if self.member:
            self.attempts_panel.items = [dict(a, pass_mark=r["pass_mark"], member=True) for a in r["attempts"]]
            self.no_attempts.visible = not r["attempts"]
            self.attempts_panel.visible = bool(r["attempts"])
            self._reviews()
        state.set_control_attr(self.answer_box, "maxlength", "6000")
        self.answer_box.text = self.answer
        self.write_part.visible, self.model_part.visible = True, False

    def _reviews(self):
        try:
            r = anvil.server.call_s("my_reviews", self.id)
        except Exception:
            self.reviews_card.visible = False  # the reviews table isn't in the database yet (Schema Mismatch)
            return
        items = r.get("items") or []
        self.reviews_panel.items = items
        self.reviews_panel.visible = bool(items)
        self.no_reviews.visible = not items
        cal = r.get("calibration")
        node = self.dom_nodes["calib_text"]
        node.hidden = not cal
        if cal:
            cs.set_text(node, _calibration_line(cal))

    # ---------------------------------------------------------------- writing and marking
    @handle("submit_button", "click")
    def submit_button_click(self, **event_args):
        self.answer = (self.answer_box.text or "").strip()
        if len(self.answer) < 40:
            state.toast("Write a few sentences first (at least 40 characters).", "error")
            return
        if self.revealed is None:
            self.submit_button.enabled = False
            r = state.call("reveal_challenge", self.id, cs.today())
            self.submit_button.enabled = True
            if not r:
                return
            self.revealed = r
        cs.set_text(self.dom_nodes["mine"], self.answer)
        cs.set_text(self.dom_nodes["model"], self.revealed["model"])
        self.rubric.items = self.revealed["rubric"]
        self.write_part.visible, self.model_part.visible = False, True
        self.score_actions.visible, self.result_box.visible = True, False
        self.record_button.enabled = True
        self.model_part.scroll_into_view(smooth=True)

    @handle("edit_button", "click")
    def edit_button_click(self, **event_args):
        self.write_part.visible, self.model_part.visible = True, False

    @handle("record_button", "click")
    def record_button_click(self, **event_args):
        if not self.member:
            self._guest_score()
            return
        self.record_button.enabled = False
        r = state.call("submit_challenge", self.id, self.answer, self.rubric.value(), cs.today())
        if not r:
            self.record_button.enabled = True
            return
        self.attempt_id = r.get("attempt_id")
        if r["passed"]:
            text = "Module complete. Well done." if r["module_completed"] else "Challenge passed. Finish the drills to complete the module."
        else:
            text = "You need %d%%. Study the model answer and try again." % self.d["pass_mark"]
        self._result(r["score"], r["passed"], "%s +%d XP" % (text, r["xp_gained"]))
        self._refresh_attempts()

    def _guest_score(self):
        points = self.rubric.value()
        score = int(round(100.0 * sum(1 for p in points if p) / len(points))) if points else 0
        passed = score >= self.d["pass_mark"]
        state.store_set(PENDING, json.dumps({"challenge": self.id, "answer": self.answer, "points": points, "score": score,
                                             "saved_at": window.Date.now()}))
        self._result(score, passed, "You covered %d of %d criteria. Create a free account to keep this score and the XP: "
                     "your answer is saved in this browser, nothing to retype." % (sum(1 for p in points if p), len(points)))

    def _result(self, score, passed, text):
        self.rubric.lock()
        self.score_actions.visible = False
        n = self.dom_nodes
        self.result_box.visible = True
        self.result_box.classes["pass"], self.result_box.classes["fail"] = passed, not passed
        cs.set_text(n["res_head"], "Passed" if passed else "Not yet")
        cs.set_text(n["res_pct"], "%d%%" % score)
        cs.set_text(n["res_text"], text)
        n["res_back"].setAttribute("href", "#module/" + self.d["module"]["id"])
        self.guest_actions.visible = not self.member
        self.ask_result_button.visible = bool(self.member and self.attempt_id)
        self.retry_button.visible = not passed
        if passed:
            cs.confetti()

    def _refresh_attempts(self):
        r = anvil.server.call_s("get_challenge", self.id, cs.today())
        if r and r.get("ok"):
            self.attempts_panel.items = [dict(a, pass_mark=r["pass_mark"], member=True) for a in r["attempts"]]
            self.no_attempts.visible = not r["attempts"]
            self.attempts_panel.visible = bool(r["attempts"])

    @handle("retry_button", "click")
    def retry_button_click(self, **event_args):
        self.answer = ""
        self.attempt_id = None
        self._load()

    # ---------------------------------------------------------------- visitor -> member
    def _to_signup(self):
        router.remember_after(router.href("challenge", self.id))
        router.go("auth", "signup")

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        self._to_signup()

    @handle("enrol_button", "click")
    def enrol_button_click(self, **event_args):
        self._to_signup()

    def _save_pending(self):
        """Signed in now, with a visitor's answer to this challenge waiting in the browser: save it (once)."""
        raw = state.store_get(PENDING)
        if not raw:
            return
        try:
            p = json.loads(str(raw))
        except Exception:
            state.store_set(PENDING, None)
            return
        if p.get("challenge") != self.id:
            return  # it belongs to another challenge's page
        state.store_set(PENDING, None)
        if window.Date.now() - (p.get("saved_at") or 0) > DAY_MS:
            return
        r = state.call("submit_challenge", self.id, p.get("answer") or "", p.get("points") or [], cs.today())
        if r:
            state.toast("Your answer is saved: %d%%, +%d XP." % (r["score"], r["xp_gained"]), "ok")
            self.answer = ""
            self._load()

    # ---------------------------------------------------------------- sharing
    @handle("share_button", "click")
    def share_button_click(self, **event_args):
        cs.copy(cs.app_url("#call"), "Link to this week's Boardroom Call copied")

    @handle("ask_result_button", "click")
    def ask_result_button_click(self, **event_args):
        self._ask(self.attempt_id)

    def _ask_event(self, attempt_id=None, **event_args):
        self._ask(attempt_id)

    def _ask(self, attempt_id):
        if not attempt_id:
            return
        r = state.call("create_review_link", attempt_id)
        if not r:
            return
        _copy_review(r["token"])
        self._reviews()

    def _copy_event(self, token=None, **event_args):
        if token:
            _copy_review(token)

    def _revoke_event(self, review_id=None, **event_args):
        if not confirm("Revoke this link? Whoever has it won't be able to open it any more.", title="Revoke the link",
                       buttons=[("Keep it", False), ("Revoke", True)]):
            return
        if state.call("revoke_review", review_id):
            state.toast("Link revoked", "ok")
            self._reviews()


def _copy_review(token):
    link = cs.app_url("#review/" + token)
    cs.copy("Would you mark my answer to a boardroom case? 3 minutes, no account needed: " + link,
            "Link and a short note copied: paste them to your mentor, coach or manager")


def _calibration_line(cal):
    d = cal["diff"]
    who = "Your reviewer scores" if cal["n"] == 1 else "Reviewers score"
    if d == 0:
        return "%s you the same as your own marks on average." % who
    return "%s you %s %s your own marks on average." % (who, state.plural(abs(d), "point"), "below" if d < 0 else "above")
