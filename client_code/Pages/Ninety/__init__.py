import anvil.server
from anvil import *
from anvil.js import window

from ._anvil_designer import NinetyTemplate
from ... import cs, router, state

DEFAULT = ("cfo", "turnaround", "external")


class Ninety(NinetyTemplate):
    """#ninety[/role/situation/origin]: Your First 90 Days (Transition.py). Anyone picks a role, the situation they
    inherit (Watkins's STARS), promotion or outside hire and a start date, and sees 13 week cards in three phases
    (get_transition_plan); the address keeps the choices, so a plan can be shared. Guests read and print it. Members
    press "Start my 90 days" (start_transition: one plan each, starting again replaces it), tick steps (tick_step) and
    see "Week 3 of 13" here and on Home. Print = window.print() with the print CSS (no header, footer or tab bar)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.hero.set(photo="ph-window", title="Your first 90 days",
                      lead="A 13-week plan built for your role, the situation you inherit and where you come from. Not a "
                           "generic 30-60-90 template: every step says why, and where the evidence comes from.",
                      crumbs=[["#tracks", "Programs"], [None, "First 90 days"]],
                      meta=[["calendar", "13 weeks, 3 phases"], ["book", "Every step sourced"], ["clock", "Free"]])
        self.error_box.visible = False
        o = state.call("get_transition_options", cs.today()) or {}
        self.opts = o
        self.mine = o.get("mine")
        self.member = bool(state.me())
        self.role_dd.items = [(r["name"], r["key"]) for r in o.get("roles") or []]
        self.situation_dd.items = [(s["name"], s["key"]) for s in o.get("situations") or []]
        self.origin_dd.items = [(x["name"], x["key"]) for x in o.get("origins") or []]
        for dd, label in ((self.role_dd, "Your role"), (self.situation_dd, "The situation you inherit"),
                          (self.origin_dd, "Promoted from inside or hired from outside")):
            state.set_control_attr(dd, "aria-label", label)
        start_input = state.control(self.start_box)
        start_input.setAttribute("type", "date")
        start_input.setAttribute("aria-label", "Your start date")
        m = self.mine
        keys = list(args[:3]) if len(args) >= 3 else ([m["role"], m["situation"], m["origin"]] if m else list(DEFAULT))
        self._set(keys, (m or {}).get("start") or cs.today())
        for dd in (self.role_dd, self.situation_dd, self.origin_dd, self.start_box):
            dd.add_event_handler("change", self._changed)
        self._draw()

    def _set(self, keys, start):
        for dd, key, fallback in zip((self.role_dd, self.situation_dd, self.origin_dd), keys, DEFAULT):
            values = [v for _label, v in dd.items]
            dd.selected_value = key if key in values else fallback
        self.start_box.text = start

    def _keys(self):
        return self.role_dd.selected_value, self.situation_dd.selected_value, self.origin_dd.selected_value

    def _is_mine(self):
        m = self.mine
        return bool(m and (m["role"], m["situation"], m["origin"]) == tuple(self._keys()))

    def _changed(self, **event_args):
        self._draw()

    # ---------------------------------------------------------------- drawing
    def _draw(self):
        role, situation, origin = self._keys()
        line = [s["line"] for s in self.opts.get("situations") or [] if s["key"] == situation]
        cs.set_text(self.dom_nodes["sit_line"], line[0] if line else "")
        try:
            r = anvil.server.call("get_transition_plan", role, situation, origin)
        except Exception:
            r = None
        if not r or not r.get("ok"):
            self.error_box.visible, self.weeks_panel.visible = True, False
            return
        self.error_box.visible, self.weeks_panel.visible = False, True
        mine = self._is_mine()
        done = set(self.mine["done"]) if mine else set()
        now = self.mine["week"] if mine else 0
        weeks = []
        for w in r["weeks"]:
            steps = [dict(s, tickable=mine, done=s["id"] in done, host=self) for s in w["steps"]]
            weeks.append(dict(w, steps=steps, now=w["n"] == now, tickable=mine))
        self.weeks_panel.items = weeks
        names = [self.role_dd.items, self.situation_dd.items, self.origin_dd.items]
        labels = [dict((v, k) for k, v in items).get(key, "") for items, key in zip(names, (role, situation, origin))]
        cs.set_text(self.dom_nodes["plan_title"], "Your first 90 days: " + labels[0])
        cs.set_text(self.dom_nodes["plan_sub"], "%s · %s · %d steps over 13 weeks%s" % (
            labels[1], labels[2], r["total"], (" · from " + cs.date(self.start_box.text, "long")) if self.start_box.text else ""))
        router.replace("ninety", role, situation, origin)
        self._status()

    def _status(self):
        m, mine = self.mine, self._is_mine()
        self.guest_note.visible = not self.member
        self.stop_button.visible = bool(self.member and m)
        self.status_box.visible = bool(self.member and m)
        if not self.member:
            self.start_button.text = "Create a free account to save it"
        elif m and mine:
            self.start_button.text = "Restart from this date"
        elif m:
            self.start_button.text = "Switch to this plan"
        else:
            self.start_button.text = "Start my 90 days"
        if not (self.member and m):
            return
        n = self.dom_nodes
        if not mine:
            cs.set_text(n["status_head"], "You're looking at a different plan.")
            cs.set_text(n["status_text"], "Your saved plan: %s, %s, %s. Switch only if your situation changed: ticks start again."
                        % (m["role_name"], m["situation_name"], m["origin_name"].lower()))
            return
        cs.set_text(n["status_head"], _week_line(m))
        bits = ["%d of %d steps done" % (len(m["done"]), m["total"])]
        if m.get("behind"):
            bits.append(state.plural(m["behind"], "earlier step") + " still open")
        cs.set_text(n["status_text"], " · ".join(bits))

    # ---------------------------------------------------------------- actions
    def tick(self, step_id, done):
        """Called by Items/PlanStep. Returns False when the tick couldn't be saved (the box goes back)."""
        r = state.call("tick_step", step_id, done, cs.today())
        if not r:
            return False
        self.mine = r["mine"]
        self._status()
        return True

    @handle("start_button", "click")
    def start_button_click(self, **event_args):
        role, situation, origin = self._keys()
        if not self.member:
            router.remember_after(router.href("ninety", role, situation, origin))
            router.go("auth", "signup")
            return
        start = (self.start_box.text or "").strip()
        if not start:
            state.toast("Pick your start date.", "error")
            return
        if self.mine and not confirm("This replaces your saved plan and clears its ticks.", title="Start again?",
                                     buttons=[("Cancel", False), ("Start again", True)]):
            return
        self.start_button.enabled = False
        r = state.call("start_transition", role, situation, origin, start, cs.today())
        self.start_button.enabled = True
        if r:
            self.mine = r["mine"]
            state.toast("Your 90 days are saved. Tick steps off as you go.", "ok")
            self._draw()

    @handle("stop_button", "click")
    def stop_button_click(self, **event_args):
        if not confirm("Remove your 90-day plan and its ticks? You can build a new one any time.", title="Remove the plan",
                       buttons=[("Keep it", False), ("Remove", True)]):
            return
        if state.call("stop_transition"):
            self.mine = None
            self._draw()

    @handle("print_button", "click")
    def print_button_click(self, **event_args):
        window.print()


def _week_line(m):
    if m["week"] <= 0:
        return "Your plan starts in %s." % state.plural(max(m.get("days_to_start") or 0, 1), "day")
    if m["week"] > m["weeks"]:
        return "All 13 weeks done. Keep the rhythm going."
    return "Week %d of %d: %s left this week" % (m["week"], m["weeks"], state.plural(m["left"], "step"))
