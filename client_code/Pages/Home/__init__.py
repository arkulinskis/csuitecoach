from anvil import *
from anvil.js import window

from ._anvil_designer import HomeTemplate
from ... import cs, state


def _greeting():
    h = window.Date().getHours()
    return "Good morning" if h < 12 else "Good afternoon" if h < 18 else "Good evening"


class Home(HomeTemplate):
    """#home (Operate): the member's dashboard from get_dashboard: rank, XP and streak; today's review with the week
    strip; examinations ready; continue where you left off; programs; credentials; case of the day; Honour Roll."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        d = state.call("get_dashboard", cs.today())
        if d:
            self._draw(d)

    def _draw(self, d):
        me, n = d["me"], self.dom_nodes
        r = me["rank"]
        first = ((state.me() or {}).get("name") or "").split(" ")[0]
        cs.set_text(n["greeting"], "%s, %s" % (_greeting(), first) if first else _greeting())
        bits = [me["title"]] if me.get("title") else []
        bits += ["%d of %d drills learned" % (d["learned"], d["total_items"]),
                 "%d of %d modules complete" % (d["modules_done"], d["modules_total"]),
                 state.plural(len(d["credentials"]), "credential")]
        cs.set_text(n["sub"], " · ".join(bits))
        cs.set_text(n["rank"], r["rank"])
        cs.set_text(n["xp"], "%d XP" % me["xp"])
        into = 100 if not r["next_at"] else int(round(100.0 * (me["xp"] - r["floor"]) / (r["next_at"] - r["floor"])))
        self.rank_bar.pct = into
        cs.set_text(n["next_rank"], "%d XP to %s" % (r["next_at"] - me["xp"], r["next"]) if r["next"] else "The highest rank")
        cs.set_text(n["streak"], state.plural(me["streak"], "day"))
        # today's review
        due = d["due"]
        cs.set_text(n["due"], due)
        cs.set_text(n["due_title"], "Drills due for review today" if due else "You're up to date")
        cs.set_text(n["due_text"], "A few minutes of recall keeps it for months." if due
                    else "New drills come due as your memory needs them. Keep going with a module.")
        self.week_panel.items = d["week"]
        self.review_link.visible, self.programs_link.visible = bool(due), not due
        tracks = {t["id"]: t for t in d["tracks"]}
        team = d.get("team")
        self.team_panel.visible = bool(team and team["tracks"])
        if team:
            cs.set_text(n["team_title"], "Assigned by %s" % team["team"])
            cs.set_text(n["team_line"], "%s, your team manager, follows your progress in these programs." % team["manager"])
            self.team_tracks_panel.items = [tracks[i] for i in team["tracks"] if i in tracks]
        self.exams_panel.items = [tracks[i] for i in d["ready_exam"] if i in tracks]
        self.exams_panel.visible = bool(d["ready_exam"])
        # continue / up next
        nx = d.get("next")
        self.next_card.visible, self.all_done.visible = bool(nx), not nx
        if nx:
            st = nx["status"]
            n["next_img"].style.backgroundImage = "url(%s)" % cs.photo(nx.get("photo"))
            cs.set_text(n["next_title"], nx["title"])
            cs.set_text(n["next_where"], "%s · %s · Module %d" % ("Continue" if st["pct"] else "Up next", nx["track"], nx["n"]))
            cs.set_text(n["next_summary"], nx["summary"])
            self._step(n["st_read"], st["read"], "Briefing")
            self._step(n["st_drill"], st["learned"] == st["total"], "Drills %d/%d" % (st["learned"], st["total"]))
            self._step(n["st_ch"], st["challenge_passed"], "Challenge")
            go = n["next_go"]
            go.setAttribute("href", "#module/" + nx["id"])
            go.innerHTML = '<i class="ic ic-arrow"></i>' + ("Continue" if st["pct"] else "Begin")
        self.tracks_panel.items = d["tracks"]
        self.creds_panel.items = d["credentials"]
        self.no_creds.visible = not d["credentials"]
        self.creds_panel.visible = bool(d["credentials"])
        c = d["case"]
        self.case_tone.text, self.case_tone.role = cs.tone_badge(c["tone"])
        cs.set_text(n["case_where"], "%s · %s" % (c["company"], c["year"]))
        cs.set_text(n["case_title"], c["title"])
        cs.set_text(n["case_summary"], c["summary"])
        n["case_link"].setAttribute("href", "#cases/" + c["id"])
        # Boardroom Call, second-opinion calibration and the 90-day plan (2026-11-20)
        self.call_card.call = d.get("call")
        cal = d.get("calibration")
        self.calib_note.visible = bool(cal)
        if cal:
            diff = cal["diff"]
            who = "Your reviewer scores" if cal["n"] == 1 else "Reviewers score"
            if diff == 0:
                line = "%s you the same as your own marks on average." % who
            else:
                line = "%s you %s %s your own marks on average (%s)." % (
                    who, state.plural(abs(diff), "point"), "below" if diff < 0 else "above", state.plural(cal["n"], "second opinion"))
            cs.set_text(n["calib_text"], line)
        tr = d.get("transition")
        self.ninety_panel.visible = bool(tr)
        if tr:
            if tr["week"] <= 0:
                head = "Your first 90 days start in %s" % state.plural(max(tr.get("days_to_start") or 0, 1), "day")
            elif tr["week"] > tr["weeks"]:
                head = "Your first 90 days are done"
            else:
                head = "Week %d of %d: %s this week" % (tr["week"], tr["weeks"], state.plural(tr["left"], "step"))
            cs.set_text(n["ninety_title"], head)
            self.ninety_bar.pct = int(round(100.0 * len(tr["done"]) / tr["total"])) if tr["total"] else 0
            cs.set_text(n["ninety_text"], "%s · %s · %d of %d steps done" % (
                tr["role_name"], tr["situation_name"], len(tr["done"]), tr["total"]))
        self.honour_panel.items = [dict(h, compact=True) for h in d["honour"]]
        self.no_honour.visible = not d["honour"]
        self.honour_panel.visible = bool(d["honour"])

    def _step(self, node, ok, label):
        node.className = "ui-badge good" if ok else "ui-badge"
        node.innerHTML = '<i class="ic ic-%s"></i>' % ("check" if ok else "clock")
        node.appendChild(window.document.createTextNode(label))
