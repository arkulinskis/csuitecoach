import anvil.server
from anvil import *
from anvil.js import window

from ._anvil_designer import LandingTemplate
from ... import router, state

# The app's video on the Addanapp YouTube channel (APP_MAKER/youtube/manifest.json), shown in the Watch section.
YT_VIDEO = "Z5MC3w_B89A"
SAMPLE = {"holder": "Margaret Okafor", "credential": "Certificate in Chief Financial Leadership", "code": "CSC-CFO-2026-T4WX9N",
          "track": "cfo", "demo": True,
          "modules": ["The four faces of the CFO", "Liquidity, rates and risk", "Investors, guidance and integrity"]}
SHOWN_CASES = ["tylenol", "redslide", "svb"]


class Landing(LandingTemplate):
    """#landing (Persuade): the institute's front door. The certificate itself is the hero (a centred pitch over the
    boardroom photo, then the full sample certificate with its verification line), the Watch section, how
    certification works, the programs (get_catalog), the Casebook, good vs bad advice, a credential lookup, the Honour
    Roll (get_honour_roll) and questions. Static copy lives in the template."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        me = state.me()
        self.guest_cta.visible, self.member_cta.visible = not me, bool(me)
        self.band_guest.visible, self.band_member.visible = not me, bool(me)
        self.sample_cert.cert = dict(SAMPLE, issued=str(window.Date().toISOString()))
        state.set_control_attr(self.code_box, "aria-label", "Credential ID")
        self.dom_nodes["yt_cover"].addEventListener("click", self._play)
        cat = state.call("get_catalog")
        if cat:
            self.programs_panel.items = cat["tracks"]
            n = self.dom_nodes
            n["n_tracks"].textContent = str(len(cat["tracks"]))
            n["n_cases"].textContent = str(cat["cases"])
            n["n_items"].textContent = str(cat["totals"]["items"])
            n["n_challenges"].textContent = str(cat["totals"]["challenges"])
        cases = anvil.server.call_s("get_cases")
        self.cases_panel.items = [c for c in cases["cases"] if c["id"] in SHOWN_CASES]
        honour = anvil.server.call_s("get_honour_roll")["items"][:6]
        self.honour_panel.items = honour
        self.no_honour.visible = not honour
        self.honour_panel.visible = bool(honour)

    def _play(self, event):
        """Swap the video's cover for YouTube's player (privacy-enhanced); nothing loads from YouTube before this click."""
        self.dom_nodes["yt_frame"].innerHTML = (
            '<iframe src="https://www.youtube-nocookie.com/embed/' + YT_VIDEO + '?autoplay=1&rel=0&playsinline=1" '
            'title="C-Suite Coach video" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen '
            'referrerpolicy="strict-origin-when-cross-origin"></iframe>')

    @handle("code_box", "pressed_enter")
    def code_box_pressed_enter(self, **event_args):
        self.verify_button_click()

    @handle("verify_button", "click")
    def verify_button_click(self, **event_args):
        code = (self.code_box.text or "").strip()
        if code:
            router.go("verify", code.upper())
