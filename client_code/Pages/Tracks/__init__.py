import anvil.server
from anvil import *

from ._anvil_designer import TracksTemplate
from ... import cs, state


class Tracks(TracksTemplate):
    """#tracks: the catalogue of programs (get_catalog) and the Fellowship band.
    #tracks/<id>: one program (get_track): its modules with the member's progress, the final examination, the
    credential, outcomes. Public; members see their progress."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.catalog_part.visible = self.track_part.visible = self.missing_part.visible = False
        if args:
            self._track(args[0])
        else:
            self._catalog()

    def _catalog(self):
        d = state.call("get_catalog")
        if not d:
            return
        self.hero.set(photo="ph-board-table", title="Programs of study",
                      lead="Executive Foundations is the shared core. Each role program builds the judgement a specific seat "
                           "demands. Every program ends in an examination and a verifiable credential.",
                      meta=[["columns", "%d programs" % len(d["tracks"])], ["cards", "%d drills" % d["totals"]["items"]],
                            ["target", "%d challenges" % d["totals"]["challenges"]], ["book", "%d case files" % d["cases"]]])
        self.cards_panel.items = d["tracks"]
        self.fellow_member.visible, self.fellow_guest.visible = d["signed_in"], not d["signed_in"]
        self.catalog_part.visible = True

    def _track(self, track_id):
        r = anvil.server.call("get_track", track_id)
        if not r.get("ok"):
            self.hero.set(photo="ph-board-table", title="Program not found", crumbs=[["#tracks", "Programs"], [None, "Not found"]])
            self.missing_part.visible = True
            return
        t, me = r["track"], state.me()
        s = t.get("status")
        cs.title(t["title"])
        if not me:
            action = {"text": "Enrol to begin", "href": "#auth/signup", "kind": "primary", "size": "lg"}
        elif s["certified"]:
            action = {"text": "View your certificate", "href": "#certificate/" + s["credential"]["code"], "kind": "primary",
                      "size": "lg", "icon": "award"}
        elif s["exam_ready"]:
            action = {"text": "Sit the final examination", "href": "#exam/" + t["id"], "kind": "primary", "size": "lg", "icon": "award"}
        else:
            first = ([m for m in t["modules"] if not (m.get("status") or {}).get("complete")] or t["modules"])[0]
            action = {"text": "Continue" if s["started"] else "Begin module 1", "href": "#module/" + first["id"],
                      "kind": "primary", "size": "lg", "icon": "arrow"}
        self.hero.set(photo=t["photo"], title=t["title"], lead=t["blurb"], crumbs=[["#tracks", "Programs"], [None, t["code"]]],
                      meta=[["user", t["role"]], ["briefcase", "%d modules" % len(t["modules"])], ["cards", "%d drills" % t["items"]],
                            ["target", "%d challenges" % t["challenges"]], ["clock", "~%s hours of study" % cs.hours(t["minutes"])],
                            ["award", t["credential"]]],
                      actions=[action])
        self.modules_panel.items = t["modules"]
        cs.set_text(self.dom_nodes["cap_text"], "A recall round of 12 drills from the whole program and the capstone case, "
                    "\u201c%s\u201d. Pass both to be issued the %s." % (t["capstone"]["title"], t["credential"]))
        self.cap_certified.visible = bool(s and s["certified"])
        self.dom_nodes["cap_begin_a"].hidden = not (s and not s["certified"] and s["exam_ready"])
        self.cap_locked.visible = bool(s and not s["certified"] and not s["exam_ready"])
        self.dom_nodes["cap_begin_a"].setAttribute("href", "#exam/" + t["id"])
        if s:
            cs.set_text(self.dom_nodes["cap_locked_t"], "%d/%d" % (s["modules_done"], s["modules"]))
        self.progress_card.visible = bool(s)
        if s:
            self.ring.pct = s["pct"]
            cs.set_text(self.dom_nodes["prog_done"], "%d of %d modules" % (s["modules_done"], s["modules"]))
            note = ("Certified " + cs.date(s["credential"]["issued"])) if s["certified"] else (
                "Examination open" if s["exam_ready"] else "Complete every module to unlock the examination")
            cs.set_text(self.dom_nodes["prog_note"], note)
        self.outcomes_panel.items = t["outcomes"]
        self.track_part.visible = True
