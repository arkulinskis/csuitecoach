"""Second opinion links (2026-11-20): a member sends ONE challenge answer to a mentor, coach or manager, who marks it
against the rubric without an account.

The member presses "Ask for a second opinion" on a result or a past attempt: create_review_link makes a private link
(#review/<token>, at most MAX_OPEN open links per attempt). The reviewer sees the scenario, the answer and the rubric
(not the model answer), ticks the criteria, types a name and an optional comment, and sends the verdict once; only then
do they see the model answer. The member sees "Dana: 60% (you: 80%)" with the comment, and Home shows how reviewers'
marks compare with their own on average (calibration).

Privacy: get_review shows the member's first name only, never an email. Links can be revoked; a revoked or unknown
link reads "no longer active". The team plan rule holds: managers see answers only when a member sends them a link.

Table reviews: attempt -> attempts, owner -> users, challenge, token, created, reviewer, points, score, comment,
reviewed, revoked, is_demo.
"""
import secrets as _secrets

import anvil.server
from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C
from . import Curriculum as K

MAX_OPEN = 5          # open (unused, not revoked) links per attempt
NAME_MAX, COMMENT_MAX = 60, 1000


def _token():
    return _secrets.token_urlsafe(16)


def _find(token):
    if not isinstance(token, str) or not 8 <= len(token) <= 64:
        return None
    return app_tables.reviews.get(token=token)


def _first_name(user):
    return C.name_of(user).split(" ")[0]


def _view(r):
    """A review as its owner sees it (the token only while the link is open, so it can be copied again)."""
    open_ = r["reviewed"] is None and not r["revoked"]
    return {"id": r.get_id(), "attempt_id": r["attempt"].get_id() if r["attempt"] is not None else None,
            "created": C.iso(r["created"]), "reviewed": C.iso(r["reviewed"]), "revoked": bool(r["revoked"]),
            "open": open_, "token": r["token"] if open_ else None, "reviewer": r["reviewer"] or "",
            "score": int(r["score"] or 0) if r["reviewed"] else None, "comment": r["comment"] or "",
            "own_score": int(r["attempt"]["score"] or 0) if r["attempt"] is not None else None}


def calibration(user):
    """{n, diff}: how reviewers' scores compare with the member's own marks on the same answers (average points), or None."""
    diffs = [int(r["score"] or 0) - int(r["attempt"]["score"] or 0)
             for r in app_tables.reviews.search(owner=user, revoked=False)
             if r["reviewed"] is not None and r["attempt"] is not None]
    if not diffs:
        return None
    return {"n": len(diffs), "diff": int(round(sum(diffs) / float(len(diffs))))}


# ------------------------------------------------------------------------------------------- the member
@anvil.server.callable(require_user=True)
def create_review_link(attempt_id):
    me = C.require_user()
    att = C.row_by_id(app_tables.attempts, attempt_id)
    if att is None or att["user"] != me:
        return C.fail("That answer isn't yours.")
    if not K.CHALLENGES.get(att["challenge"] or ""):
        return C.fail("That challenge doesn't exist any more.")
    open_links = [r for r in app_tables.reviews.search(attempt=att, revoked=False) if r["reviewed"] is None]
    if len(open_links) >= MAX_OPEN:
        return C.fail("This answer already has %d open links. Revoke one, or wait for a reviewer." % MAX_OPEN)
    if C.rate_limited("review_link", 20, 3600):
        return C.fail("That's a lot of links in one hour. Try again later.")
    r = app_tables.reviews.add_row(attempt=att, owner=me, challenge=att["challenge"], token=_token(), created=C.now(),
                                   reviewer=None, points=None, score=None, comment=None, reviewed=None, revoked=False,
                                   is_demo=False)
    return C.ok(review=_view(r), token=r["token"])


@anvil.server.callable(require_user=True)
def my_reviews(challenge_id):
    """The member's second opinions on one challenge, newest first."""
    me = C.require_user()
    rows = sorted(app_tables.reviews.search(owner=me, challenge=challenge_id), key=lambda r: r["created"], reverse=True)
    return {"ok": True, "items": [_view(r) for r in rows if not r["revoked"]][:20], "calibration": calibration(me)}


@anvil.server.callable(require_user=True)
def revoke_review(review_id):
    me = C.require_user()
    r = C.row_by_id(app_tables.reviews, review_id)
    if r is None or r["owner"] != me:
        return C.fail("That link isn't yours.")
    r["revoked"] = True
    return C.ok()


# ------------------------------------------------------------------------------------------- the reviewer (no account)
@anvil.server.callable
def get_review(token):
    """Public: what a second-opinion link shows. The member's first name only (never an email), the scenario, the answer
    and the rubric; no model answer. found=False when the link is unknown or revoked; used=True once marked."""
    r = _find(token)
    if r is None or r["revoked"] or r["attempt"] is None:
        return {"ok": True, "found": False}
    ch = K.CHALLENGES.get(r["challenge"] or "")
    if ch is None:
        return {"ok": True, "found": False}
    out = {"ok": True, "found": True, "used": r["reviewed"] is not None, "owner": _first_name(r["owner"]),
           "challenge": {"id": ch["id"], "title": ch["title"], "photo": ch.get("photo") or "ph-boardroom"}}
    if out["used"]:
        return out
    m = K.MODULES[ch["module"]]
    out["challenge"].update(situation=ch["situation"], ask=ch["ask"], rubric=list(ch["rubric"]))
    out.update(answer=r["attempt"]["answer"] or "", module={"title": m["title"], "track": K.TRACK_BY_ID[m["track"]]["title"]})
    return out


@anvil.server.callable
def submit_review(token, reviewer, points, comment=None):
    """Public: the reviewer's verdict, once per link. Returns the model answer so the reviewer can compare."""
    from . import Learning as L
    if C.rate_limited("review_submit", 20, 3600):
        return C.fail("That's a lot of reviews in one hour. Try again later.")
    reviewer = C.text(reviewer, NAME_MAX)
    if len(reviewer) < 2:
        return C.fail("Add your name, so they know whose opinion it is.")
    comment = C.text(comment, COMMENT_MAX, multiline=True)
    ch = None
    with tables.Transaction():
        r = _find(token)
        if r is None or r["revoked"] or r["attempt"] is None:
            return C.fail("This link is no longer active.")
        if r["reviewed"] is not None:
            return C.fail("This link has already been used.")
        ch = K.CHALLENGES.get(r["challenge"] or "")
        if ch is None:
            return C.fail("This link is no longer active.")
        clean, score = L.score_points(points, len(ch["rubric"]))
        r.update(reviewer=reviewer, points=clean, score=score, comment=comment, reviewed=C.now())
    return C.ok(score=score, model=ch["model"], owner=_first_name(r["owner"]))
