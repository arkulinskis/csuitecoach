from anvil import *

from ._anvil_designer import ProfileTemplate
from ... import auth, router, state


class Profile(ProfileTemplate):
    """#profile: your name (printed on certificates you earn from now on), job title and Honour Roll opt-in, rank and
    XP, light/dark, a password reset link, Privacy & Terms, feedback, sign out."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        state.heading(self.name_title, 1)
        state.set_control_attr(self.name_box, "autocomplete", "name")
        state.set_control_attr(self.name_box, "maxlength", "60")
        state.set_control_attr(self.title_box, "autocomplete", "organization-title")
        state.set_control_attr(self.title_box, "maxlength", "80")
        self._show_me()
        self._show_theme()

    def _show_me(self):
        me = state.me()
        self.initials.text = state.initials(me.get("name"))
        self.name_title.text = me.get("name") or ""
        self.rank_line.text = "%s · %d XP" % (me.get("rank") or "", me.get("xp") or 0)
        joined = state.month_year(me.get("joined"))
        self.email_line.text = (me.get("email") or "") + (" · member since " + joined if joined else "")
        self.name_box.text = me.get("name") or ""
        self.title_box.text = me.get("title") or ""
        self.honour_box.checked = bool(me.get("honour_roll"))
        self.admin_link.visible = bool(me.get("is_admin"))

    def _show_theme(self):
        t = state.theme()
        for name, el in (("auto", self.theme_auto), ("light", self.theme_light), ("dark", self.theme_dark)):
            el.classes["on"] = name == t

    def theme_click(self, event):
        state.set_theme(event.currentTarget.getAttribute("data-theme-pick"))
        self._show_theme()

    @handle("name_box", "pressed_enter")
    def name_box_pressed_enter(self, **event_args):
        self.save_button_click()

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        name = (self.name_box.text or "").strip()
        if len(name) < 2:
            state.toast("Please tell us your name.", "error")
            return
        r = state.call("update_profile", name, self.title_box.text or "", bool(self.honour_box.checked))
        if r:
            state.set_me(r["me"])
            self._show_me()
            state.toast("Saved", "ok")

    @handle("reset_button", "click")
    def reset_button_click(self, **event_args):
        r = auth.reset(state.me()["email"])
        state.toast(r["message"], "ok")

    def feedback_click(self, event):
        state.feedback()

    def sign_out_click(self, event):
        auth.sign_out()
        state.toast("Signed out. See you soon.")
        router.go("landing")
