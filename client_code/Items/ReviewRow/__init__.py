from anvil import *

from ._anvil_designer import ReviewRowTemplate
from ... import cs, state


class ReviewRow(ReviewRowTemplate):
    """A second opinion on the Challenge page (Reviews.my_reviews). Marked: "Dana: 60% (you: 80%)" + the comment.
    Open link: "Waiting for a reviewer" with Copy link / Revoke (raise x-copy / x-revoke on the panel).
    item = {id, open, token, created, reviewer, score, own_score, comment}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        r, n = self.item, self.dom_nodes
        self.open_actions.visible = bool(r.get("open"))
        self.box.classes["open"] = bool(r.get("open"))
        if r.get("open"):
            cs.set_text(n["who"], "Waiting for a reviewer")
            cs.set_text(n["score"], "link made " + state.ago(r.get("created")))
            n["score"].className = "muted small"
            n["comment"].hidden = True
            state.set_control_attr(self.copy_button, "aria-label", "Copy the review link again")
            state.set_control_attr(self.revoke_button, "aria-label", "Revoke the review link")
            return
        own = r.get("own_score")
        cs.set_text(n["who"], r.get("reviewer") or "Reviewer")
        cs.set_text(n["score"], "%d%%%s" % (r.get("score") or 0, (" (you: %d%%)" % own) if own is not None else ""))
        n["score"].className = "ch-rev-score"
        cs.set_text(n["comment"], r.get("comment") or "No comment.")
        n["comment"].hidden = False

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        if self.parent is not None:
            self.parent.raise_event("x-copy", token=self.item.get("token"))

    @handle("revoke_button", "click")
    def revoke_button_click(self, **event_args):
        if self.parent is not None:
            self.parent.raise_event("x-revoke", review_id=self.item.get("id"))
