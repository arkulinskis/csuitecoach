"""Page addresses: #name/arg1/arg2 -> a page Form (open_form), with sign-in rules. The addresses are the same as the
JavaScript version's, so links people shared (certificates, verification, cases, modules) keep working.

Links in templates are plain <a href="#home">; code calls router.go("module", id).

    PAGES[name] = (who may open it, browser-tab title)   who: None = anyone, "guest" = signed out only, "user", "admin"
    NAV = the main menu for members (header + phone tab bar): (page, label, icon). At most 4 (the tab bar).
    NAV_MORE = extra header links for members; GUEST_NAV = the header links for visitors.
New page: add it to PAGES, to _form() and (if it belongs in the menu) to NAV.
"""
import anvil
import anvil.js
from anvil.js import window

from . import state

PAGES = {
    "landing": (None, "Executive certification"),
    "auth": ("guest", "Sign in"),
    "home": ("user", "Dashboard"),
    "tracks": (None, "Programs"),
    "module": (None, "Module"),
    "study": ("user", "Review"),
    "challenge": ("user", "Challenge"),
    "exam": ("user", "Final examination"),
    "credentials": ("user", "Credentials"),
    "certificate": (None, "Certificate"),
    "verify": (None, "Verify a credential"),
    "cases": (None, "The Casebook"),
    "profile": ("user", "Your profile"),
    "admin": ("admin", "Admin"),
}
NAV = [("home", "Home", "home"), ("tracks", "Programs", "columns"), ("study", "Review", "cards"),
       ("credentials", "Credentials", "award")]
NAV_MORE = [("cases", "Casebook", "book")]
GUEST_NAV = [("tracks", "Programs", "columns"), ("cases", "Casebook", "book"), ("verify", "Verify", "shield")]
APP_NAME = "C-Suite Coach"
_r: dict = {"after": "", "listening": False}


def _form(name):
    """The page's Form class (imported when first needed, so start-up stays quick)."""
    if name == "landing":
        from .Pages.Landing import Landing
        return Landing
    if name == "auth":
        from .Pages.Auth import Auth
        return Auth
    if name == "home":
        from .Pages.Home import Home
        return Home
    if name == "tracks":
        from .Pages.Tracks import Tracks
        return Tracks
    if name == "module":
        from .Pages.Module import Module
        return Module
    if name == "study":
        from .Pages.Study import Study
        return Study
    if name == "challenge":
        from .Pages.Challenge import Challenge
        return Challenge
    if name == "exam":
        from .Pages.Exam import Exam
        return Exam
    if name == "credentials":
        from .Pages.Credentials import Credentials
        return Credentials
    if name == "certificate":
        from .Pages.Certificate import Certificate
        return Certificate
    if name == "verify":
        from .Pages.Verify import Verify
        return Verify
    if name == "cases":
        from .Pages.Cases import Cases
        return Cases
    if name == "profile":
        from .Pages.Profile import Profile
        return Profile
    from .Pages.Admin import Admin
    return Admin


def parse(hash_text):
    h = (hash_text or "").lstrip("#").lstrip("!").lstrip("/").split("?")[0]
    parts = [window.decodeURIComponent(p) for p in h.split("/") if p]
    return (parts[0] if parts else ""), parts[1:]


def href(name, *args):
    """'#name/arg1/arg2' with every part URL-encoded."""
    return "#" + "/".join([name] + [window.encodeURIComponent(str(a)) for a in args if a not in (None, "")])


def home_page():
    return "home" if state.me() else "landing"


def show():
    """Open the page for the current address."""
    name, args = parse(window.location.hash)
    if name not in PAGES:
        name, args = home_page(), []
    who = PAGES[name][0]
    if who == "guest" and state.me():
        name, args = "home", []
    elif who in ("user", "admin") and not state.me():
        _r["after"] = window.location.hash
        name, args = "auth", []
    elif who == "admin" and not state.is_admin():
        state.toast("That page is for admins only.", "error")
        name, args = "home", []
    window.document.title = PAGES[name][1] + " · " + APP_NAME
    window.UI_READY = False
    page = _form(name)(args=args)
    anvil.open_form(page)
    shell = getattr(page, "layout", None)
    if shell is not None and hasattr(shell, "refresh"):
        shell.refresh(name)  # Anvil reuses the layout between pages: tell it who is signed in and which page is open
    window.scrollTo(0, 0)
    window.UI_READY = True  # tests and screenshots wait for this


def go(name, *args):
    """Go to a page. Same address again = reload the page."""
    target = href(name, *args)
    if window.location.hash == target:
        show()
    else:
        window.location.hash = target


def replace(name, *args):
    """Change the address without opening anything (a page that switches its own view)."""
    window.history.replaceState(None, "", href(name, *args))


def after_sign_in():
    """Where to go once someone signs in: the page they were heading for, or home."""
    target = _r["after"]
    _r["after"] = ""
    if target and target != window.location.hash:
        window.location.hash = target
    else:
        go("home")


def remember_after(target):
    _r["after"] = target


def _on_hash(event):
    show()


def start():
    if not _r["listening"]:
        window.addEventListener("hashchange", anvil.js.report_exceptions(_on_hash))
        _r["listening"] = True
    show()
