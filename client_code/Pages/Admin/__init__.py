from anvil import *

from ._anvil_designer import AdminTemplate
from ... import state

TABS = ["overview", "credentials", "feedback", "users", "demo"]


class Admin(AdminTemplate):
    """#admin/<tab>: overview numbers (people, learning, examinations, credentials), the credentials register with
    revoke / reinstate, the old feedback inbox, users (admin / active switches) and the demo data.
    Each tab is its own address, so the browser's back button works."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.tab = args[0] if args and args[0] in TABS else "overview"
        self._filter = "new"
        parts = {"overview": self.overview_part, "credentials": self.credentials_part, "feedback": self.feedback_part,
                 "users": self.users_part, "demo": self.demo_part}
        tabs = {"overview": self.tab_overview, "credentials": self.tab_credentials, "feedback": self.tab_feedback,
                "users": self.tab_users, "demo": self.tab_demo}
        for name in TABS:
            parts[name].visible = name == self.tab
            tabs[name].classes["on"] = name == self.tab
            state.set_attr(tabs[name], "aria-current", "page" if name == self.tab else None)
        state.set_control_attr(self.search_box, "aria-label", "Search people")
        state.set_control_attr(self.cred_search_box, "aria-label", "Search credentials")
        self.feedback_panel.add_event_handler("x-changed", self._feedback_changed)
        getattr(self, "_" + self.tab)()

    # ---- overview
    def _overview(self):
        d = state.call("admin_overview")
        if not d:
            return
        self.s_users.text, self.s_admins.text = str(d["users"]), str(d["admins"])
        self.s_admins_label.text = "admin" if d["admins"] == 1 else "admins"
        self.s_feedback.text, self.s_learners.text = str(d["feedback_new"]), str(d["learners"])
        self.s_modules.text, self.s_attempts.text = str(d["modules_done"]), str(d["attempts"])
        self.s_exams.text, self.s_creds.text = str(d["exams"]), str(d["credentials"])
        self.demo_line.text = "Demo data is %s (%d demo people). Manage it in the Demo data tab." % (
            d["demo"]["state"], d["demo"]["counts"].get("users", 0))

    # ---- credentials register
    def _credentials(self, query=None):
        d = state.call("admin_credentials", query or None)
        if not d:
            return
        self.creds_panel.items = d["items"]
        self.creds_count.text = state.plural(d["total"], "credential")
        self.no_creds.visible = not d["items"]
        self.creds_head.visible = bool(d["items"])

    @handle("cred_search_box", "pressed_enter")
    def cred_search_box_pressed_enter(self, **event_args):
        self._credentials(self.cred_search_box.text)

    @handle("cred_search_button", "click")
    def cred_search_button_click(self, **event_args):
        self._credentials(self.cred_search_box.text)

    # ---- feedback
    def _feedback(self):
        d = state.call("list_feedback", None)
        if not d:
            return
        items = [i for i in d["items"] if self._filter == "all" or i["status"] == self._filter]
        self.feedback_panel.items = items
        self.no_feedback.visible = not items
        labels = {"new": "New", "read": "Read", "done": "Done", "all": "All"}
        for key, el in (("new", self.f_new), ("read", self.f_read), ("done", self.f_done), ("all", self.f_all)):
            n = len(d["items"]) if key == "all" else d["counts"].get(key, 0)
            el.text = "%s (%d)" % (labels[key], n)
            el.role = ["seg", "on"] if key == self._filter else ["seg"]

    def _set_filter(self, value):
        self._filter = value
        self._feedback()

    @handle("f_new", "click")
    def f_new_click(self, **event_args):
        self._set_filter("new")

    @handle("f_read", "click")
    def f_read_click(self, **event_args):
        self._set_filter("read")

    @handle("f_done", "click")
    def f_done_click(self, **event_args):
        self._set_filter("done")

    @handle("f_all", "click")
    def f_all_click(self, **event_args):
        self._set_filter("all")

    def _feedback_changed(self, **event_args):
        self._feedback()

    # ---- users
    def _users(self, query=None):
        d = state.call("list_users", query or None)
        if not d:
            return
        self.users_panel.items = d["users"]
        self.users_count.text = state.plural(d["total"], "person", "people")

    @handle("search_box", "pressed_enter")
    def search_box_pressed_enter(self, **event_args):
        self._users(self.search_box.text)

    @handle("search_button", "click")
    def search_button_click(self, **event_args):
        self._users(self.search_box.text)

    # ---- demo data
    def _demo(self):
        d = state.call("admin_overview")
        if not d:
            return
        demo = d["demo"]
        counts = ", ".join("%s %s" % (v, k) for k, v in demo["counts"].items())
        self.demo_status.text = "Status: %s · %s" % (demo["state"], counts)
        self.demo_load_button.text = "Reload demo data" if demo["state"] == "loaded" else "Load demo data"

    @handle("demo_load_button", "click")
    def demo_load_button_click(self, **event_args):
        if confirm("Demo people and content are added (any old demo rows are replaced).", title="Load the demo data?",
                   buttons=[("Cancel", False), ("Load", True)], role="app-dialog"):
            if state.call("demo_load"):
                state.toast("Done", "ok")
                self._demo()

    @handle("demo_remove_button", "click")
    def demo_remove_button_click(self, **event_args):
        if confirm("Every demo row is deleted. Real data stays.", title="Remove the demo data?",
                   buttons=[("Cancel", False), ("Remove", True)], role="app-dialog"):
            if state.call("demo_remove"):
                state.toast("Done", "ok")
                self._demo()
