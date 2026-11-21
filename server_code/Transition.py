"""Your First 90 Days (2026-11-20): a 13-week transition plan built from role x situation (STARS) x origin.

Anyone can build, read and print a plan (#ninety, get_transition_plan). Members press "Start my 90 days": one plan per
member (starting again replaces it), steps ticked with tick_step, and Home shows "Week 3 of 13: 4 steps this week"
(dashboard_card, read by Learning.get_dashboard inside a guard so it works before the schema is accepted).
Content: content_transition.py. Table transitions: user, role, situation, origin, start (date), done (step ids),
created, is_demo.
"""
import datetime as dt

import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import Curriculum as K
from . import content_transition as T

WEEKS = 13
ROLE_KEYS = [k for k, _ in T.ROLES]
SITUATION_KEYS = [k for k, _n, _d in T.SITUATIONS]
ORIGIN_KEYS = [k for k, _ in T.ORIGINS]
ROLE_TAG = {"ceo": "CEO", "cfo": "CFO", "coo": "COO", "chro": "CHRO", "tech": "Technology", "cmo": "CMO"}


def _phase(week):
    for first, last, name, line in T.PHASES:
        if first <= week <= last:
            return {"name": name, "line": line, "first": week == first}
    return {"name": "", "line": "", "first": False}


def _link_label(link):
    kind, _, ref = link.lstrip("#").partition("/")
    if kind == "module" and ref in K.MODULES:
        return "Module: " + K.MODULES[ref]["title"]
    if kind == "cases" and ref in K.CASE_BY_ID:
        return "Case: " + K.CASE_BY_ID[ref]["title"]
    return "Read more"


def valid(role, situation, origin):
    return role in ROLE_KEYS and situation in SITUATION_KEYS and origin in ORIGIN_KEYS


def steps_for(role, situation, origin):
    """Every step of one plan, in week order: base first, then role, situation and origin steps that week."""
    sit = dict((k, n) for k, n, _d in T.SITUATIONS)[situation]
    org = dict(T.ORIGINS)[origin]
    tagged = [(s, "") for s in T.BASE] + [(s, ROLE_TAG[role]) for s in T.ROLE_STEPS[role]] + \
             [(s, sit) for s in T.SITUATION_STEPS[situation]] + [(s, org) for s in T.ORIGIN_STEPS[origin]]
    out = []
    for (sid, week, text, why, src, link), tag in tagged:
        label, url = T.SOURCES[src]
        out.append({"id": sid, "week": week, "text": text, "why": why, "source": {"label": label, "url": url},
                    "link": link, "link_label": _link_label(link), "tag": tag})
    out.sort(key=lambda s: (s["week"], s["tag"] != ""))
    return out


def plan(role, situation, origin):
    steps = steps_for(role, situation, origin)
    weeks = []
    for n in range(1, WEEKS + 1):
        weeks.append({"n": n, "phase": _phase(n), "steps": [s for s in steps if s["week"] == n]})
    return weeks


def options():
    return {"roles": [{"key": k, "name": n} for k, n in T.ROLES],
            "situations": [{"key": k, "name": n, "line": d} for k, n, d in T.SITUATIONS],
            "origins": [{"key": k, "name": n} for k, n in T.ORIGINS],
            "phases": [{"first": a, "last": b, "name": n, "line": d} for a, b, n, d in T.PHASES], "weeks": WEEKS}


def _today(client_day=None):
    return K._day(client_day)


def week_of(start, day):
    """1-13 during the plan, 0 before it starts, 14+ after week 13."""
    if start is None:
        return 0
    if day < start:
        return 0
    return (day - start).days // 7 + 1


def _mine(user):
    return app_tables.transitions.get(user=user) if user is not None else None


def _view(row, day):
    role, situation, origin = row["role"], row["situation"], row["origin"]
    if not valid(role, situation, origin):
        return None
    steps = steps_for(role, situation, origin)
    ids = set(s["id"] for s in steps)
    done = [s for s in (row["done"] or []) if s in ids]
    week = week_of(row["start"], day)
    this_week = [s for s in steps if s["week"] == min(max(week, 1), WEEKS)]
    left = [s for s in this_week if s["id"] not in done]
    late = [s for s in steps if s["week"] < min(week, WEEKS + 1) and s["id"] not in done and week >= 1]
    return {"role": role, "situation": situation, "origin": origin, "start": C.iso(row["start"]), "week": week,
            "weeks": WEEKS, "done": done, "total": len(steps), "this_week": len(this_week), "left": len(left),
            "behind": len(late),
            "days_to_start": (row["start"] - day).days if row["start"] and day < row["start"] else 0,
            "role_name": dict(T.ROLES)[role], "situation_name": dict((k, n) for k, n, _d in T.SITUATIONS)[situation],
            "origin_name": dict(T.ORIGINS)[origin]}


def dashboard_card(user, day):
    """For Home: the member's plan in one line, or None."""
    row = _mine(user)
    return _view(row, day) if row is not None else None


# ------------------------------------------------------------------------------------------- callables
@anvil.server.callable
def get_transition_options(client_day=None):
    """Public: the choices for #ninety and, for a member with a saved plan, that plan's state."""
    out = dict(options(), ok=True, signed_in=C.me() is not None, mine=None)
    me = C.me()
    if me is not None:
        try:
            out["mine"] = dashboard_card(me, _today(client_day))
        except Exception:
            out["mine"] = None  # the transitions table isn't in the database yet (Schema Mismatch not accepted)
    return out


@anvil.server.callable
def get_transition_plan(role, situation, origin):
    """Public: the 13 weeks of one plan."""
    if not valid(role, situation, origin):
        return C.fail("Pick a role, a situation and where you're coming from.")
    weeks = plan(role, situation, origin)
    return C.ok(weeks=weeks, total=sum(len(w["steps"]) for w in weeks))


@anvil.server.callable(require_user=True)
def start_transition(role, situation, origin, start, client_day=None):
    """Save the member's plan (one per member: starting again replaces the old one and clears its ticks)."""
    me = C.require_user()
    if not valid(role, situation, origin):
        return C.fail("Pick a role, a situation and where you're coming from.")
    day = _today(client_day)
    try:
        start_day = dt.date.fromisoformat(str(start)[:10])
    except Exception:
        return C.fail("Pick your start date.")
    if abs((start_day - day).days) > 366:
        return C.fail("Pick a start date within a year of today.")
    row = _mine(me)
    if row is None:
        row = app_tables.transitions.add_row(user=me, role=role, situation=situation, origin=origin, start=start_day,
                                             done=[], created=C.now(), is_demo=False)
    else:
        row.update(role=role, situation=situation, origin=origin, start=start_day, done=[], created=C.now())
    return C.ok(mine=_view(row, day))


@anvil.server.callable(require_user=True)
def tick_step(step_id, done, client_day=None):
    me = C.require_user()
    row = _mine(me)
    if row is None:
        return C.fail("Start your 90 days first.")
    ids = [s["id"] for s in steps_for(row["role"], row["situation"], row["origin"])] if valid(row["role"], row["situation"], row["origin"]) else []
    if step_id not in ids:
        return C.fail("That step isn't in your plan.")
    cur = [s for s in (row["done"] or []) if s in ids and s != step_id]
    if done:
        cur.append(step_id)
    row["done"] = cur
    return C.ok(mine=_view(row, _today(client_day)))


@anvil.server.callable(require_user=True)
def my_transition(client_day=None):
    me = C.require_user()
    row = _mine(me)
    return C.ok(mine=_view(row, _today(client_day)) if row is not None else None)


@anvil.server.callable(require_user=True)
def stop_transition():
    me = C.require_user()
    row = _mine(me)
    if row is not None:
        row.delete()
    return C.ok()
