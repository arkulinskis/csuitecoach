import anvil.server
from anvil import *

from ._anvil_designer import JoinTemplate
from ... import router, state


class Join(JoinTemplate):
    """#join/<token>: a personal team invite (Teams.get_invite / accept_invite). Visitors create an account or sign in
    and come straight back here (router.remember_after); members join with one click."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self._token = args[0] if args else ""
        d: dict = anvil.server.call("get_invite", self._token) if self._token else {}
        self._d = d
        self.not_found.visible = not d.get("found")
        self.invite_part.visible = bool(d.get("found"))
        if not d.get("found"):
            self.hero.set(photo="ph-meeting", title="Team invite", lead="")
            return
        first = str(d.get("name") or "").split(" ")[0]
        hello = "%s, you're invited" % first if first else "You're invited"
        tracks: list = d.get("tracks") or []
        self.hero.set(photo="ph-meeting", title="Join %s" % d["team"],
                      lead="%s. %s has enrolled you in C-Suite Coach, the executive-education program with real cases, "
                           "boardroom challenges and verifiable certificates." % (hello, d["manager"]),
                      meta=[["users", d["team"]], ["columns", state.plural(len(tracks), "program")]])
        self.tracks_panel.items = tracks
        self.dom_nodes["privacy"].textContent = (
            "%s will see your name, your progress in each program, the certificates you earn and the last day you studied. "
            "Not your written answers or examination details." % d["manager"])
        signed_in = bool(state.me())
        self.guest_actions.visible = not signed_in
        self.member_actions.visible = signed_in and not d.get("mine")
        note = ""
        if d.get("mine"):
            note = "You're already in this team."
        elif d.get("used"):
            note = "This invite has already been used. If that wasn't you, ask your team manager for your own link."
            self.member_actions.visible = self.guest_actions.visible = False
        elif signed_in and d.get("other_team"):
            note = "You're in %s now. Joining %s means leaving it." % (d["other_team"], d["team"])
        self.note.text, self.note.visible = note, bool(note)

    def _auth(self, mode):
        router.remember_after(router.href("join", self._token))
        router.go("auth", mode)

    @handle("signup_button", "click")
    def signup_button_click(self, **event_args):
        self._auth("signup")

    @handle("login_button", "click")
    def login_button_click(self, **event_args):
        self._auth(None)

    @handle("join_button", "click")
    def join_button_click(self, **event_args):
        self.join_button.enabled = False
        r = state.call("accept_invite", self._token)
        self.join_button.enabled = True
        if r:
            state.toast("Welcome to %s" % r["team"], "ok")
            router.go("home")
