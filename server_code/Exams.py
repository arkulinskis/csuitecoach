"""Final examinations and credentials.

A program's final examination opens when all its modules are complete. It has two parts, both self-assessed
under an honour code: a recall round of EXAM_ITEMS random drill items from the whole program (pass: 80% "Got it"),
and the program's capstone scenario scored against its rubric (pass: 70%). Passing issues a credential with a
public verification code (CSC-<CODE>-<YEAR>-<6 chars>). Holding Executive Foundations plus two role certificates
also issues the Fellowship. A failed attempt can be retaken after RETAKE_MINUTES.
"""
import datetime as dt
import random

import anvil.server
from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C
from . import Curriculum as K
from . import Learning as L

RETAKE_MINUTES = 30
EXAM_XP = 200
CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_code(track_code, when=None):
    year = (when or C.now()).year
    while True:
        code = "CSC-%s-%d-%s" % (track_code, year, "".join(random.choice(CODE_CHARS) for _ in range(6)))
        if app_tables.credentials.get(code=code) is None:
            return code


def issue(user, track_id, score, is_demo=False, when=None):
    """Create a credential row (idempotent per user + track)."""
    old = app_tables.credentials.get(user=user, track=track_id, revoked=False)
    if old is not None:
        return old
    code_part = K.FELLOW["code"] if track_id == "fellow" else K.TRACK_BY_ID[track_id]["code"]
    return app_tables.credentials.add_row(user=user, track=track_id, code=new_code(code_part, when), holder=C.name_of(user),
                                          issued=when or C.now(), score=score, revoked=False, is_demo=is_demo)


def maybe_fellow(user):
    creds = K.user_credentials(user)
    roles = [t for t in creds if t not in ("core", "fellow")]
    if "core" in creds and len(roles) >= 2 and "fellow" not in creds:
        return issue(user, "fellow", 100)
    return None


def _open_exam(user, track_id):
    for r in app_tables.exams.search(user=user, track=track_id, finished=None):
        return r
    return None


@anvil.server.callable(require_user=True)
def get_exam(track_id):
    """Eligibility, past attempts, and (if allowed) a fresh examination paper."""
    me = C.require_user()
    t = K.TRACK_BY_ID.get(track_id)
    if t is None:
        return C.fail("That program doesn't exist.")
    states, prog, creds = K.user_states(me), K.user_progress(me), K.user_credentials(me)
    st = K.track_status(track_id, states, prog, creds)
    past = sorted([r for r in app_tables.exams.search(user=me, track=track_id) if r["finished"]], key=lambda r: r["finished"], reverse=True)
    history = [{"finished": C.iso(r["finished"]), "drill": int(r["card_score"] or 0), "scenario": int(r["scenario_score"] or 0),
                "passed": bool(r["passed"])} for r in past[:8]]
    out = {"track": K.track_brief(t), "status": st, "history": history, "pass_drill": K.PASS_EXAM_DRILL,
           "pass_scenario": K.PASS_CHALLENGE, "items_count": K.EXAM_ITEMS, "retake_minutes": RETAKE_MINUTES}
    if st["certified"]:
        return C.ok(state="certified", **out)
    if not st["exam_ready"]:
        missing = [{"id": mid, "title": K.MODULES[mid]["title"]} for mid in t["modules"]
                   if not K.module_status(mid, states, prog)["complete"]]
        return C.ok(state="locked", missing=missing, **out)
    if past and not past[0]["passed"]:
        wait = past[0]["finished"] + dt.timedelta(minutes=RETAKE_MINUTES) - C.now()
        if wait.total_seconds() > 0:
            return C.ok(state="cooldown", minutes=int(wait.total_seconds() // 60) + 1, **out)
    ex = _open_exam(me, track_id)
    if ex is None:
        ids = K.track_items(track_id)
        pick = random.sample(ids, min(K.EXAM_ITEMS, len(ids)))
        ex = app_tables.exams.add_row(user=me, track=track_id, started=C.now(), finished=None, card_score=0, scenario_score=0,
                                      passed=False, detail={"items": pick}, is_demo=False)
    pick = (ex["detail"] or {}).get("items") or []
    return C.ok(state="ready", exam_id=ex.get_id(), items=[K.item_public(i) for i in pick if i in K.ITEMS],
                capstone=K.challenge_public(t["capstone"]), **out)


@anvil.server.callable(require_user=True)
def submit_exam(exam_id, ratings, answer, points, honour, client_day=None):
    me = C.require_user()
    ex = C.row_by_id(app_tables.exams, exam_id)
    if ex is None or ex["user"] != me:
        return C.fail("That examination isn't yours.")
    if ex["finished"]:
        return C.fail("This examination was already submitted.")
    if not honour:
        return C.fail("Please confirm the honour code before submitting.")
    track_id = ex["track"]
    t = K.TRACK_BY_ID[track_id]
    pick = (ex["detail"] or {}).get("items") or []
    if not isinstance(ratings, dict) or any(i not in ratings for i in pick):
        return C.fail("Rate every recall item before submitting.")
    answer = C.text(answer, 8000, multiline=True)
    if len(answer) < 80:
        return C.fail("Write your answer to the scenario: at least a short paragraph (80 characters).")
    got = sum(1 for i in pick if ratings.get(i) is True)
    drill = int(round(100.0 * got / len(pick))) if pick else 0
    clean, scenario = L.score_points(points, len(t["capstone"]["rubric"]))
    passed = drill >= K.PASS_EXAM_DRILL and scenario >= K.PASS_CHALLENGE
    ex.update(finished=C.now(), card_score=drill, scenario_score=scenario, passed=passed,
              detail={"items": pick, "ratings": {i: bool(ratings.get(i)) for i in pick}, "answer": answer, "points": clean})
    day = L.today(client_day)
    # the recall round also counts as review for spaced repetition
    for i in pick:
        r = app_tables.card_state.get(user=me, item=i)
        if r is not None and ratings.get(i) is False:
            r.update(box=0, due=day, lapses=(r["lapses"] or 0) + 1, last=C.now())
    cred = fellow = None
    if passed:
        cred = issue(me, track_id, int(round((drill + scenario) / 2.0)))
        L.add_xp(me, EXAM_XP, day)
        fellow = maybe_fellow(me)
    else:
        L.add_xp(me, 10, day)
    return C.ok(passed=passed, drill=drill, scenario=scenario, code=cred["code"] if cred else None,
                fellow=fellow["code"] if fellow else None, retake_minutes=RETAKE_MINUTES)
