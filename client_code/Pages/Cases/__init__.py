import anvil.server
from anvil import *

from ._anvil_designer import CasesTemplate
from ... import cs, state

FILTERS = ["all", "exemplary", "cautionary", "mixed"]


class Cases(CasesTemplate):
    """#cases: the Casebook with a filter by lesson type (get_cases). #cases/<id>: one case file with its story, the
    lesson, the modules that study it, sources, previous / next (get_case). Public."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.list_part.visible = self.one_part.visible = self.missing_part.visible = False
        self._filter = "all"
        self._cases: list = []
        if args:
            self._one(args[0])
        else:
            self._list()

    # ---- the Casebook
    def _list(self):
        d = state.call("get_cases")
        if not d:
            return
        self._cases = d["cases"]
        c = self._cases
        self.hero.set(photo="ph-podium", title="The Casebook: decisions that made and broke companies",
                      lead="Documented situations from public reporting, each with the lesson it teaches. Exemplary cases show "
                           "what to do; cautionary cases show what it costs when it goes wrong.",
                      meta=[["book", "%d case files" % len(c)], ["check", "%d exemplary" % len([x for x in c if x["tone"] == "exemplary"])],
                            ["alert", "%d cautionary" % len([x for x in c if x["tone"] == "cautionary"])]])
        self.list_part.visible = True
        self._draw()

    def _draw(self):
        self.cases_panel.items = [c for c in self._cases if self._filter == "all" or c["tone"] == self._filter]
        for f, b in zip(FILTERS, [self.f_all, self.f_exemplary, self.f_cautionary, self.f_mixed]):
            b.role = ["seg", "on"] if f == self._filter else ["seg"]
            state.set_control_attr(b, "aria-pressed", "true" if f == self._filter else "false")

    def _set(self, f):
        self._filter = f
        self._draw()

    @handle("f_all", "click")
    def f_all_click(self, **event_args):
        self._set("all")

    @handle("f_exemplary", "click")
    def f_exemplary_click(self, **event_args):
        self._set("exemplary")

    @handle("f_cautionary", "click")
    def f_cautionary_click(self, **event_args):
        self._set("cautionary")

    @handle("f_mixed", "click")
    def f_mixed_click(self, **event_args):
        self._set("mixed")

    # ---- one case file
    def _one(self, case_id):
        r = anvil.server.call("get_case", case_id)
        if not r.get("ok"):
            self.hero.set(photo="ph-podium", title="Case not found", crumbs=[["#cases", "The Casebook"], [None, "Not found"]])
            self.missing_part.visible = True
            return
        c = r["case"]
        cs.title(c["title"])
        tone = c["tone"]
        self.hero.set(photo="ph-podium" if tone == "cautionary" else "ph-board-table", title=c["title"], lead=c["summary"],
                      crumbs=[["#cases", "The Casebook"], [None, c["company"]]],
                      meta=[["calendar", "%s · %s" % (c["company"], c["year"])], ["briefcase", "Seat: " + c["role"]],
                            ["alert" if tone == "cautionary" else "check", tone[:1].upper() + tone[1:]]])
        self.story_panel.items = c["story"]
        cs.set_text(self.dom_nodes["lesson"], c["lesson"])
        self.mods_sec.visible = bool(c["modules"])
        self.mods_panel.items = c["modules"]
        self.sources_panel.items = c["sources"]
        n = self.dom_nodes
        n["prev"].hidden, n["next"].hidden = not c.get("prev"), not c.get("next")
        if c.get("prev"):
            n["prev"].setAttribute("href", "#cases/" + c["prev"])
        if c.get("next"):
            n["next"].setAttribute("href", "#cases/" + c["next"])
        self.one_part.visible = True
