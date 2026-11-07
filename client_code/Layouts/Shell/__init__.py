import datetime

from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import ShellTemplate
from ... import auth, router, state

THEMES = ["auto", "light", "dark"]
LEGAL_LINE = ("© %d C-Suite Coach Institute. A private executive-education program: its credentials are issued on its own "
              "authority and are not accredited academic qualifications. Case studies are drawn from public reporting. "
              "Photography: Pexels.")


class Shell(ShellTemplate):
    """The frame around every page: the institute bar (members: menu + account button; visitors: Programs, Casebook,
    Verify and Sign in / Enrol), the account menu, the footer (three columns, the seal, the legal line) and the phone
    tab bar. Pages use it with <anvil-form layout="C_Suite_Coach.Layouts.Shell">.

    Anvil keeps ONE Shell while pages come and go (open_form only swaps the "content" slot when the layout matches),
    so everything that depends on who is signed in or which page is open is drawn in refresh(), which router.show()
    calls after every page change. Never only in __init__."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.copyright_label.text = LEGAL_LINE % datetime.date.today().year
        self._outside = anvil.js.report_exceptions(self._close_menu_outside)
        self._keys = anvil.js.report_exceptions(self._key)
        self.refresh("")

    def refresh(self, page):
        me = state.me()
        self.classes.update({"signed-in": bool(me), "signed-out": not me})
        self.member_actions.visible = bool(me)
        self.guest_actions.visible = not me and page != "auth"
        self.tabbar.visible = bool(me)
        self.menu.visible = False
        state.set_attr(self.brand, "href", "#home" if me else "#landing")
        header = (router.NAV + router.NAV_MORE) if me else router.GUEST_NAV
        self.nav_panel.items = [{"page": p, "label": label, "icon": icon, "on": p == page} for p, label, icon in header]
        self.tab_panel.items = [{"page": p, "label": label, "icon": icon, "on": p == page}
                                for p, label, icon in router.NAV] if me else []
        self.tab_profile.classes["on"] = page == "profile"
        self.ft_mine.visible = bool(me)
        self.ft_how.visible = not me
        if me:
            self.avatar_button.text = state.initials(me.get("name"))
            self.menu_name.text = me.get("name") or ""
            self.menu_email.text = me.get("email") or ""
            self.menu_rank.text = "%s · %d XP" % (me.get("rank"), me.get("xp") or 0) if me.get("rank") else ""
            self.menu_rank.visible = bool(me.get("rank"))
            self.admin_link.visible = bool(me.get("is_admin"))
        self._show_theme()

    # ---- account menu
    @handle("avatar_button", "click")
    def avatar_button_click(self, **event_args):
        self.menu.visible = not self.menu.visible
        state.set_control_attr(self.avatar_button, "aria-expanded", "true" if self.menu.visible else "false")

    def _close_menu_outside(self, event):
        if self.menu.visible and not event.target.closest(".anvil-role-avatar, .ui-menu .ui-seg"):
            self.menu.visible = False

    def _key(self, event):
        if event.key == "Escape":
            self.menu.visible = False

    @handle("", "show")
    def form_show(self, **event_args):
        state.set_control_attr(self.avatar_button, "aria-label", "Your account")
        state.set_control_attr(self.avatar_button, "aria-haspopup", "true")
        window.document.addEventListener("click", self._outside, True)
        window.document.addEventListener("keydown", self._keys)

    @handle("", "hide")
    def form_hide(self, **event_args):
        window.document.removeEventListener("click", self._outside, True)
        window.document.removeEventListener("keydown", self._keys)

    def theme_click(self, event):
        state.set_theme(event.currentTarget.getAttribute("data-theme-set"))
        self._show_theme()

    def _show_theme(self):
        t = state.theme()
        for name, el in zip(THEMES, [self.theme_auto, self.theme_light, self.theme_dark]):
            el.classes["on"] = name == t

    def feedback_click(self, event):
        self.menu.visible = False
        state.feedback()

    def sign_out_click(self, event):
        auth.sign_out()
        state.toast("Signed out. See you soon.")
        router.go("landing")
