from anvil import *
import anvil.media

from ._anvil_designer import TeamTemplate
from ... import router, state
from ...Items.TrackPick import picked


def _csv_cell(v):
    s = str(v if v is not None else "")
    if s[:1] in ("=", "+", "-", "@"):
        s = "'" + s  # spreadsheets must not run a formula from someone's name
    return '"%s"' % s.replace('"', '""')


class Team(TeamTemplate):
    """#team: the team plan (Teams.py). A team manager invites leaders, assigns programs and follows their progress;
    a member sees which team they're in and can leave; anyone else can create a team."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.members_panel.add_event_handler("x-team-changed", self._reload)
        state.set_control_attr(self.people_box, "aria-label", "People to invite, one per line: name, email")
        self._d: dict = {}
        if not state.me():
            self.hero.set(photo="ph-team", title="Team plan",
                          lead="Enrol your company's leaders, assign programs and see everyone's progress in one place.",
                          meta=[["users", "For leadership teams"], ["columns", "Assign any program"]])
            self.manage_part.visible = self.membership_part.visible = self.create_card.visible = False
            return
        self.guest_card.visible = False
        self._reload()

    def _reload(self, **event_args):
        d = state.call("get_team")
        if not d:
            return
        self._d = d
        t, mem = d["managed"], d["membership"]
        if t:
            s = t["stats"]
            self.hero.set(photo="ph-team", title=t["name"],
                          lead="Invite your leaders, choose their programs and follow their progress.",
                          meta=[["users", state.plural(s["active"], "member")], ["mail", state.plural(s["invited"], "invite") + " waiting"],
                                ["award", state.plural(s["certificates"], "certificate")]])
        elif mem:
            self.hero.set(photo="ph-team", title=mem["team"], lead="Your team manager, %s, follows your progress here." % mem["manager"],
                          meta=[["columns", state.plural(len(mem["tracks"]), "program") + " assigned"]])
        else:
            self.hero.set(photo="ph-team", title="Team plan",
                          lead="Enrol your company's leaders, assign programs and see everyone's progress in one place.",
                          meta=[["users", "For leadership teams"], ["columns", "Assign any program"]])
        self.manage_part.visible = bool(t)
        self.start_part.visible = not t and not mem
        self.membership_part.visible = bool(mem)
        if mem:
            self.dom_nodes["mem_line"].textContent = (
                "You're a member of %s, managed by %s, since %s." % (mem["team"], mem["manager"], state.short_date(mem["joined"])))
            self.mem_tracks_panel.items = [{"text": x["title"], "href": "#tracks/" + x["id"], "kind": "", "size": "sm", "icon": "columns"}
                                           for x in mem["tracks"]]
        if t:
            self._draw_team(t, d["catalog"])

    def _draw_team(self, t, catalog):
        s = t["stats"]
        self.s_active.text = str(s["active"])
        self.s_invited.text = str(s["invited"])
        self.s_avg.text = "%d%%" % s["avg"]
        self.s_certs.text = str(s["certificates"])
        if not self.people_box.text:
            self.picks_panel.items = [dict(c, on=c["id"] in t["tracks"]) for c in catalog]
        self.members_panel.items = [dict(m, catalog=catalog) for m in t["members"]]
        self.no_members.visible = not t["members"]
        self.members_panel.visible = bool(t["members"])
        self.csv_button.visible = bool(t["members"])
        self.name_box.text = t["name"]

    def guest_click(self, event):
        router.remember_after("#team")  # after signing up / in, come back here to create the team

    def _say(self, text, error=False):
        self.invite_msg.text = text
        self.invite_msg.role = "msg-error" if error else "msg-note"
        self.invite_msg.visible = bool(text)

    @handle("create_button", "click")
    def create_button_click(self, **event_args):
        r = state.call("create_team", self.new_name_box.text, ["core"])
        if r:
            state.toast("Your team is ready. Invite your first leaders.", "ok")
            self._reload()

    @handle("new_name_box", "pressed_enter")
    def new_name_box_pressed_enter(self, **event_args):
        self.create_button_click()

    @handle("invite_button", "click")
    def invite_button_click(self, **event_args):
        tracks = picked(self.picks_panel)
        if not self.people_box.text.strip():
            self._say("Add at least one person: their name, a comma, then their email.", True)
            return
        if not tracks:
            self._say("Pick at least one program for them to complete.", True)
            return
        self.invite_button.enabled = False
        try:
            r = state.call("invite_people", self.people_box.text, tracks, self.email_box.checked)
        finally:
            self.invite_button.enabled = True
        if not r:
            return
        bits = ["%s created" % state.plural(len(r["made"]), "invite")]
        if self.email_box.checked:
            bits.append("%d emailed" % r["sent"])
            if r["unsent"]:
                bits.append("%d couldn't be emailed: copy their links below" % r["unsent"])
        else:
            bits.append("copy each link below and send it yourself")
        if r["skipped"]:
            bits.append("already invited: %s" % ", ".join(r["skipped"]))
        if r["bad"]:
            bits.append("not an email address, so skipped: %s" % "; ".join(r["bad"]))
        self._say("; ".join(bits) + ".", bool(r["bad"] or r["unsent"]))
        self.people_box.text = ""
        self._draw_team(r["team"], self._d.get("catalog") or [])

    @handle("csv_button", "click")
    def csv_button_click(self, **event_args):
        t = self._d.get("managed")
        if not t:
            return
        rows = [["Name", "Email", "Status", "Joined", "Last studied", "Program", "Modules done", "Modules", "Progress %", "Certified"]]
        for m in t["members"]:
            for x in (m["tracks"] or [{}]):
                rows.append([m.get("display_name") or m["name"], m["email"], m["status"], (m.get("joined") or "")[:10],
                             m.get("last_study") or "", x.get("title", ""), x.get("modules_done", ""), x.get("modules", ""),
                             x.get("pct", ""), "yes" if x.get("certified") else "no"])
        text = "\r\n".join(",".join(_csv_cell(v) for v in r) for r in rows)
        anvil.media.download(BlobMedia("text/csv", ("﻿" + text).encode("utf-8"), name="team-progress.csv"))

    @handle("rename_button", "click")
    def rename_button_click(self, **event_args):
        if state.call("update_team", self.name_box.text):
            state.toast("Team name saved", "ok")
            self._reload()

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        if not confirm("Delete the team? Open invites stop working and you stop seeing everyone's progress. "
                       "Members keep their own accounts, progress and certificates.",
                       title="Delete the team", buttons=[("Keep it", False), ("Delete", True)]):
            return
        if state.call("delete_team"):
            state.toast("Team deleted", "ok")
            self._reload()

    @handle("leave_button", "click")
    def leave_button_click(self, **event_args):
        mem = self._d.get("membership")
        if not mem or not confirm("Leave %s? Your manager stops seeing your progress. You keep everything you've earned." % mem["team"],
                                  title="Leave the team", buttons=[("Stay", False), ("Leave", True)]):
            return
        if state.call("leave_team"):
            state.toast("You've left the team", "ok")
            router.go("team")
