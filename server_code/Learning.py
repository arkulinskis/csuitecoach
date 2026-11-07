"""Learning: the dashboard, drill sessions (Leitner spaced repetition), briefings read, and module challenges.

Spaced repetition (as in CAF Guide): "Got it" moves an item up one box, due again after BOX_DAYS[box] days;
"Still learning" sends it to box 0, due today. Learned = box >= 1, mastered = box >= 4.
A module is complete when the briefing is read, every drill item is learned and the challenge scored >= 70%.
"""
import datetime as dt
import random

import anvil.server
from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C
from . import Curriculum as K
from . import DemoData

BOX_DAYS = [0, 1, 3, 7, 16, 35, 90]
MAX_BOX = len(BOX_DAYS) - 1
SESSION_SIZE = 20
REVIEW_SIZE = 30
RANKS = [(0, "Analyst"), (100, "Associate"), (250, "Manager"), (500, "Director"), (900, "Vice President"),
         (1500, "Senior Vice President"), (2400, "C-Suite"), (3600, "Chair")]
XP_GOT, XP_AGAIN, XP_MODULE = 3, 1, 40


def today(client_day=None):
    """The member's local date if the browser sent a sensible one (within a day of UTC), else UTC today."""
    utc = C.now().date()
    try:
        d = dt.date.fromisoformat(str(client_day)[:10])
        if abs((d - utc).days) <= 1:
            return d
    except Exception:
        pass
    return utc


def rank_for(xp):
    xp = xp or 0
    cur, nxt = RANKS[0], None
    for i, r in enumerate(RANKS):
        if xp >= r[0]:
            cur, nxt = r, (RANKS[i + 1] if i + 1 < len(RANKS) else None)
    return {"rank": cur[1], "floor": cur[0], "next": nxt[1] if nxt else None, "next_at": nxt[0] if nxt else None}


def add_xp(user, n, day):
    """Add XP and keep the daily streak."""
    last = user["last_study"]
    if last != day:
        user["streak"] = (user["streak"] or 0) + 1 if last == day - dt.timedelta(days=1) else 1
        user["last_study"] = day
    user["xp"] = (user["xp"] or 0) + n


def _progress_row(user, module_id):
    r = app_tables.module_progress.get(user=user, module=module_id)
    if r is None:
        r = app_tables.module_progress.add_row(user=user, module=module_id, read_at=None, challenge_score=0, completed_at=None, is_demo=False)
    return r


def check_complete(user, module_id, day):
    """Mark the module complete if all three steps are done. Returns True the first time it completes."""
    states, prog = K.user_states(user), K.user_progress(user)
    st = K.module_status(module_id, states, prog)
    p = prog.get(module_id)
    if p is not None and not p["completed_at"] and st["read"] and st["learned"] == st["total"] and st["challenge_passed"]:
        p["completed_at"] = C.now()
        add_xp(user, XP_MODULE, day)
        return True
    return False


# ------------------------------------------------------------------------------------------- dashboard
@anvil.server.callable(require_user=True)
def get_dashboard(client_day=None):
    DemoData.ensure_loaded()
    me = C.require_user()
    day = today(client_day)
    states, prog, creds = K.user_states(me), K.user_progress(me), K.user_credentials(me)
    due = [i for i, r in states.items() if i in K.ITEMS and r["due"] is not None and r["due"] <= day]
    tracks = []
    nxt = None
    for t in K.TRACKS:
        s = K.track_status(t["id"], states, prog, creds)
        tracks.append(dict(K.track_brief(t), status=s))
    # "Continue": the first unfinished module of a started program, else the first module of Foundations.
    started = [t for t in tracks if t["status"]["started"] and not t["status"]["certified"]] or tracks[:1]
    for t in started:
        for mid in K.TRACK_BY_ID[t["id"]]["modules"]:
            st = K.module_status(mid, states, prog)
            if not st["complete"]:
                m = K.MODULES[mid]
                nxt = {"id": mid, "title": m["title"], "summary": m["summary"], "photo": m["photo"], "n": m["n"],
                       "track": t["title"], "track_id": t["id"], "status": st}
                break
        if nxt:
            break
    ready_exam = [t["id"] for t in tracks if t["status"]["exam_ready"] and not t["status"]["certified"]]
    learned = sum(1 for r in states.values() if (r["box"] or 0) >= 1)
    mastered = sum(1 for r in states.values() if (r["box"] or 0) >= 4)
    week = [day - dt.timedelta(days=i) for i in range(6, -1, -1)]
    seen_days = set()
    for r in states.values():
        if r["last"]:
            seen_days.add(r["last"].date())
    case = K.CASES[day.toordinal() % len(K.CASES)]
    return {"me": {"xp": me["xp"] or 0, "streak": me["streak"] if me["last_study"] in (day, day - dt.timedelta(days=1)) else 0,
                   "rank": rank_for(me["xp"]), "title": me["job_title"] or ""},
            "due": len(due), "learned": learned, "mastered": mastered, "total_items": len(K.ITEMS),
            "modules_done": sum(1 for p in prog.values() if p["completed_at"]), "modules_total": len(K.MODULES),
            "next": nxt, "tracks": tracks, "ready_exam": ready_exam,
            "credentials": [{"track": k, "title": K.track_title(k), "credential": K.credential_name(k), "code": v["code"], "issued": v["issued"]}
                            for k, v in sorted(creds.items(), key=lambda kv: kv[1]["issued"] or "")],
            "week": [{"day": d.isoformat(), "active": d in seen_days} for d in week],
            "case": K.case_brief(case), "honour": _honour(6)}


def _honour(limit):
    out, seen = [], set()
    for r in app_tables.credentials.search(tables.order_by("issued", ascending=False)):
        u = r["user"]
        if r["revoked"] or u is None or not u["honour_roll"] or u.get_id() in seen:
            continue
        seen.add(u.get_id())  # one line per person: their latest credential
        out.append({"name": r["holder"], "title": u["job_title"] or "", "credential": K.credential_name(r["track"]),
                    "track": r["track"], "code": r["code"], "issued": C.iso(r["issued"]), "demo": bool(r["is_demo"])})
        if len(out) >= limit:
            break
    return out


@anvil.server.callable
def get_honour_roll():
    """Recently certified members who chose to appear on the public Honour Roll."""
    DemoData.ensure_loaded()
    return {"items": _honour(24)}


# ------------------------------------------------------------------------------------------- drills
@anvil.server.callable(require_user=True)
def get_study(scope, client_day=None):
    """A drill session. scope: 'review' (everything due) or a module id (its whole deck, new and due first)."""
    me = C.require_user()
    day = today(client_day)
    states = K.user_states(me)
    if scope == "review":
        ids = [i for i, r in states.items() if i in K.ITEMS and r["due"] is not None and r["due"] <= day]
        ids.sort(key=lambda i: (states[i]["box"] or 0, states[i]["due"]))
        ids = ids[:REVIEW_SIZE]
        title, sub = "Daily review", "Everything due today, across your programs."
    elif scope in K.MODULES:
        all_ids = K.module_items(scope)

        def order(i):
            r = states.get(i)
            if r is None:
                return (0, 0)
            if r["due"] is not None and r["due"] <= day:
                return (1, r["box"] or 0)
            return (2, r["box"] or 0)
        ids = sorted(all_ids, key=order)[:SESSION_SIZE]
        m = K.MODULES[scope]
        title, sub = m["title"], "Drill · module %d of %s" % (m["n"], K.TRACK_BY_ID[m["track"]]["title"])
    else:
        return C.fail("Unknown study session.")
    items = []
    for i in ids:
        it = K.item_public(i)
        r = states.get(i)
        it["box"] = (r["box"] or 0) if r else None
        items.append(it)
    if scope != "review":
        # mix cards and advice calls a little, but keep new ones first
        new = [x for x in items if x["box"] is None]
        old = [x for x in items if x["box"] is not None]
        random.shuffle(new)
        items = new + old
    return C.ok(scope=scope, title=title, subtitle=sub, items=items, boxes=BOX_DAYS)


@anvil.server.callable(require_user=True)
def rate_item(item_id, knew, client_day=None):
    me = C.require_user()
    if item_id not in K.ITEMS:
        return C.fail("Unknown card.")
    day = today(client_day)
    knew = bool(knew)
    r = app_tables.card_state.get(user=me, item=item_id)
    if r is None:
        r = app_tables.card_state.add_row(user=me, item=item_id, module=K.ITEMS[item_id]["module"], box=0, due=day,
                                          reviews=0, lapses=0, last=None, is_demo=False)
    box = r["box"] or 0
    if knew:
        box = min(box + 1, MAX_BOX)
    else:
        if box > 0:
            r["lapses"] = (r["lapses"] or 0) + 1
        box = 0
    r.update(box=box, due=day + dt.timedelta(days=BOX_DAYS[int(box)]), reviews=(r["reviews"] or 0) + 1, last=C.now())
    add_xp(me, XP_GOT if knew else XP_AGAIN, day)
    module_id = K.ITEMS[item_id]["module"]
    done = check_complete(me, module_id, day)
    return C.ok(box=box, due=C.iso(r["due"]), xp=me["xp"], module_completed=done,
                module_title=K.MODULES[module_id]["title"] if done else None)


@anvil.server.callable(require_user=True)
def mark_read(module_id, client_day=None):
    me = C.require_user()
    if module_id not in K.MODULES:
        return C.fail("Unknown module.")
    day = today(client_day)
    p = _progress_row(me, module_id)
    first = not p["read_at"]
    if first:
        p["read_at"] = C.now()
        add_xp(me, 10, day)
    done = check_complete(me, module_id, day)
    return C.ok(first=first, module_completed=done, xp=me["xp"])


# ------------------------------------------------------------------------------------------- challenges
def _attempt(r):
    return {"id": r.get_id(), "answer": r["answer"], "points": r["points"] or [], "score": int(r["score"] or 0),
            "created": C.iso(r["created"])}


@anvil.server.callable(require_user=True)
def get_challenge(challenge_id):
    me = C.require_user()
    ch = K.CHALLENGES.get(challenge_id)
    if ch is None or not ch.get("module"):
        return C.fail("That challenge doesn't exist.")
    m = K.MODULES[ch["module"]]
    rows = sorted(app_tables.attempts.search(user=me, challenge=challenge_id), key=lambda r: r["created"], reverse=True)
    return C.ok(challenge=K.challenge_public(ch), module={"id": m["id"], "title": m["title"], "n": m["n"],
                                                          "track": K.TRACK_BY_ID[m["track"]]["title"], "track_id": m["track"]},
                attempts=[_attempt(r) for r in rows[:10]], best=max([int(r["score"] or 0) for r in rows] or [0]),
                pass_mark=K.PASS_CHALLENGE)


def score_points(points, n):
    """Self-assessed rubric ticks -> (clean list of n bools, percentage)."""
    if not isinstance(points, (list, tuple)):
        points = []
    clean = [bool(points[i]) if i < len(points) else False for i in range(n)]
    return clean, int(round(100.0 * sum(clean) / n)) if n else 0


@anvil.server.callable(require_user=True)
def submit_challenge(challenge_id, answer, points, client_day=None):
    me = C.require_user()
    ch = K.CHALLENGES.get(challenge_id)
    if ch is None or not ch.get("module"):
        return C.fail("That challenge doesn't exist.")
    answer = C.text(answer, 6000, multiline=True)
    if len(answer) < 40:
        return C.fail("Write your decision first: at least a few sentences (40 characters).")
    if C.rate_limited("challenge", 40, 3600):
        return C.fail("That's a lot of attempts in one hour. Take a break and come back.")
    day = today(client_day)
    clean, score = score_points(points, len(ch["rubric"]))
    app_tables.attempts.add_row(user=me, challenge=challenge_id, module=ch["module"], answer=answer, points=clean,
                                score=score, created=C.now(), is_demo=False)
    p = _progress_row(me, ch["module"])
    prev = int(p["challenge_score"] or 0)
    gained = 5 + max(0, score - prev) // 4
    if score > prev:
        p["challenge_score"] = score
    add_xp(me, gained, day)
    done = check_complete(me, ch["module"], day)
    return C.ok(score=score, best=max(score, prev), passed=score >= K.PASS_CHALLENGE, xp_gained=gained, xp=me["xp"],
                module_completed=done, module_title=K.MODULES[ch["module"]]["title"] if done else None)
