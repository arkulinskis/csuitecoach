from anvil import *

from ._anvil_designer import TeamMemberRowTemplate
from ... import cs, state


class TeamMemberRow(TeamMemberRowTemplate):
    """#team, People: one invited / active / departed person, as the team manager sees them (Teams.get_team).
    Invites: copy the link, email it again, cancel. Members: change their programs, remove. Left: clear.
    Tells the page to reload with self.parent.raise_event("x-team-changed")."""

    def __init__(self, **properties):
        super().__init__(**properties)
        m = self.item
        st = m["status"]
        shown = m.get("display_name") or m.get("name") or m.get("email")
        self.initials.text = state.initials(shown)
        n = self.dom_nodes
        n["name"].textContent = shown
        typed = m.get("name") or ""
        n["email"].textContent = m.get("email") + (" · invited as %s" % typed if typed and typed != shown else "")
        if st == "active":
            self.status_label.text, self.status_label.role = "Member", ["badge", "badge-good"]
            facts = ["Joined %s" % state.short_date(m.get("joined"))]
            facts.append("last studied %s" % cs.date(m["last_study"], "short") if m.get("last_study") else "hasn't studied yet")
            if m.get("streak"):
                facts.append(state.plural(m["streak"], "day") + " streak")
            facts.append(state.plural(m.get("learned") or 0, "drill") + " learned")
        elif st == "invited":
            self.status_label.text, self.status_label.role = "Invite sent", ["badge", "badge-warn"]
            facts = ["Invited %s" % state.short_date(m.get("invited"))]
            if m.get("last_sent"):
                facts.append("emailed %s" % state.short_date(m["last_sent"]))
            else:
                facts.append("not emailed: send the link yourself")
        else:
            self.status_label.text, self.status_label.role = "Left the team", ["badge"]
            facts = ["Their progress is private again"]
        n["facts"].textContent = " · ".join(facts)
        self.tracks_panel.items = m.get("tracks") or []
        self.tracks_panel.visible = st != "left"
        creds = m.get("credentials") or []
        self.creds_line.visible = bool(creds)
        n["creds"].textContent = ", ".join(c["credential"] for c in creds)
        self.copy_button.visible = self.resend_button.visible = st == "invited"
        self.programs_button.visible = st in ("invited", "active")
        self.remove_button.text = {"invited": "Cancel invite", "active": "Remove", "left": "Clear"}[st]
        for b in (self.copy_button, self.resend_button, self.programs_button, self.remove_button):
            state.set_control_attr(b, "aria-label", "%s: %s" % (b.text, shown))

    def _changed(self):
        self.parent.raise_event("x-team-changed")

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        cs.copy(self.item["link"], "Invite link copied. Send it to %s." % (self.item.get("name") or "them"))

    @handle("resend_button", "click")
    def resend_button_click(self, **event_args):
        r = state.call("resend_invite", self.item["id"])
        if r:
            state.toast("Invite emailed to %s" % r["sent_to"], "ok")
            self._changed()

    @handle("programs_button", "click")
    def programs_button_click(self, **event_args):
        from ...Dialogs.PickPrograms import PickPrograms
        m = self.item
        on = [t["id"] for t in (m.get("tracks") or [])]
        tracks = alert(PickPrograms(catalog=m.get("catalog") or [], on=on,
                                    who=m.get("display_name") or m.get("name") or m.get("email")),
                       buttons=[], role="app-dialog")
        if tracks and state.call("set_member_tracks", m["id"], tracks):
            state.toast("Programs updated", "ok")
            self._changed()

    @handle("remove_button", "click")
    def remove_button_click(self, **event_args):
        m = self.item
        who = m.get("display_name") or m.get("name") or m.get("email")
        if m["status"] == "invited":
            ask, yes = "Cancel the invite for %s? Their link will stop working." % who, "Cancel invite"
        elif m["status"] == "active":
            ask, yes = ("Remove %s from the team? They keep their account, progress and certificates; you stop seeing them."
                        % who), "Remove"
        else:
            ask, yes = "", ""
        if ask and not confirm(ask, title=yes, buttons=[("Keep", False), (yes, True)]):
            return
        if state.call("remove_member", m["id"]):
            state.toast("Done", "ok")
            self._changed()
