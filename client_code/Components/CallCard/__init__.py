from anvil import *

from ._anvil_designer import CallCardTemplate
from ... import cs, state


class CallCard(CallCardTemplate):
    """This week's Boardroom Call as a navy card (landing, right after the hero; Home). call = Curriculum.call_summary:
    {id, title, photo, teaser, ask, days_left, done, score}. "Make the call" opens #call (a stable link that always
    shows the week's challenge); Share copies that link; LinkedIn opens LinkedIn's share page with it."""

    def __init__(self, **properties):
        self._call = None
        self._ready = False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        c = self._call
        self.card.visible = bool(c)
        if not self._ready or not c:
            return
        n = self.dom_nodes
        n["ph"].style.backgroundImage = "url(%s)" % cs.photo(c.get("photo"))
        cs.set_text(n["left"], "%s left · a new real decision every Monday" % state.plural(c.get("days_left") or 1, "day"))
        cs.set_text(n["title"], c.get("title"))
        cs.set_text(n["teaser"], c.get("teaser"))
        cs.set_text(n["ask"], c.get("ask"))
        go = n["go"]
        go.setAttribute("href", "#call")
        if c.get("done"):
            go.textContent = "Done this week: %d%%. Open it again" % (c.get("score") or 0)
        else:
            go.textContent = "Make the call: 5 minutes, no account" if not state.me() else "Make the call: 5 minutes"
        n["li"].setAttribute("href", cs.linkedin_share(cs.app_url("#call")))
        n["li"].setAttribute("aria-label", "Share this week's Boardroom Call on LinkedIn (opens LinkedIn)")

    @handle("share_button", "click")
    def share_button_click(self, **event_args):
        cs.copy(cs.app_url("#call"), "Link to this week's Boardroom Call copied")

    @property
    def call(self):
        return self._call

    @call.setter
    def call(self, value):
        self._call = value
        self._draw()
