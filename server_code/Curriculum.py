"""The curriculum: programs (tracks) -> modules -> drill items (cards + advice calls) and challenges.

Content lives in content_core.py, content_roles_a.py, content_roles_b.py and the Casebook in content_cases.py.
This module assembles it into lookups and serves the public catalogue pages (no sign-in needed to browse).

Ids: track "cfo"; module "cfo-risk"; drill item "cfo-risk:c3" (card) / "cfo-risk:a1" (advice call);
challenge "ch-cfo-risk"; capstone "cap-cfo".
"""
import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import content_core, content_roles_a, content_roles_b
from .content_cases import CASES, CASE_BY_ID

PASS_CHALLENGE = 70        # % of the rubric to pass a module challenge or the exam scenario
PASS_EXAM_DRILL = 80       # % "Got it" in the exam's recall round
EXAM_ITEMS = 12            # recall items in a final examination

FELLOW = {"id": "fellow", "code": "FEL", "order": 99, "title": "Fellowship of the Institute",
          "credential": "Fellow of the C-Suite Coach Institute (FCSCI)", "photo": "ph-boardroom",
          "blurb": "Awarded automatically to holders of Executive Foundations and two role certificates."}

TRACKS = []          # ordered list of track dicts (with "modules": [ids], "capstone": {...})
TRACK_BY_ID = {}
MODULES = {}         # id -> module dict (+ "track", "n")
ITEMS = {}           # drill item id -> {"id","kind","module","track", ...}
CHALLENGES = {}      # challenge id -> challenge dict (+ "module" or "capstone_of")


def _add_track(track, modules, capstone):
    t = dict(track)
    t["modules"] = [m["id"] for m in modules]
    t["capstone"] = dict(capstone, capstone_of=t["id"])
    TRACKS.append(t)
    TRACK_BY_ID[t["id"]] = t
    CHALLENGES[t["capstone"]["id"]] = t["capstone"]
    for n, m in enumerate(modules, 1):
        m = dict(m, track=t["id"], n=n)
        MODULES[m["id"]] = m
        for i, (q, a, note) in enumerate(m["cards"], 1):
            ITEMS["%s:c%d" % (m["id"], i)] = {"id": "%s:c%d" % (m["id"], i), "kind": "card", "module": m["id"], "track": t["id"],
                                             "q": q, "a": a, "note": note}
        for i, (text, sound, why) in enumerate(m["advice"], 1):
            ITEMS["%s:a%d" % (m["id"], i)] = {"id": "%s:a%d" % (m["id"], i), "kind": "advice", "module": m["id"], "track": t["id"],
                                             "q": text, "sound": bool(sound), "a": why, "note": ""}
        ch = dict(m["challenge"], module=m["id"])
        CHALLENGES[ch["id"]] = ch


_add_track(content_core.TRACK, content_core.MODULES, content_core.CAPSTONE)
for _pack in content_roles_a.TRACKS + content_roles_b.TRACKS:
    _add_track(_pack["track"], _pack["modules"], _pack["capstone"])
TRACKS.sort(key=lambda t: t["order"])


def module_items(module_id):
    m = MODULES[module_id]
    return ["%s:c%d" % (module_id, i) for i in range(1, len(m["cards"]) + 1)] + \
           ["%s:a%d" % (module_id, i) for i in range(1, len(m["advice"]) + 1)]


def track_items(track_id):
    out = []
    for mid in TRACK_BY_ID[track_id]["modules"]:
        out += module_items(mid)
    return out


def track_title(track_id):
    return FELLOW["title"] if track_id == "fellow" else TRACK_BY_ID[track_id]["title"]


def credential_name(track_id):
    return FELLOW["credential"] if track_id == "fellow" else TRACK_BY_ID[track_id]["credential"]


# ------------------------------------------------------------------------------------------- serialising
def item_public(item_id):
    it = ITEMS[item_id]
    m = MODULES[it["module"]]
    out = {"id": it["id"], "kind": it["kind"], "q": it["q"], "a": it["a"], "note": it["note"],
           "module": m["id"], "module_title": m["title"], "track": it["track"], "track_code": TRACK_BY_ID[it["track"]]["code"]}
    if it["kind"] == "advice":
        out["sound"] = it["sound"]
    return out


def challenge_public(ch):
    return {"id": ch["id"], "title": ch["title"], "photo": ch.get("photo") or "ph-boardroom", "situation": ch["situation"],
            "ask": ch["ask"], "model": ch["model"], "rubric": list(ch["rubric"]), "module": ch.get("module"),
            "capstone_of": ch.get("capstone_of")}


def case_brief(c):
    return {"id": c["id"], "title": c["title"], "company": c["company"], "year": c["year"], "role": c["role"],
            "tone": c["tone"], "summary": c["summary"]}


def track_brief(t):
    mods = [MODULES[mid] for mid in t["modules"]]
    return {"id": t["id"], "code": t["code"], "title": t["title"], "role": t["role"], "credential": t["credential"],
            "photo": t["photo"], "blurb": t["blurb"], "outcomes": t["outcomes"],
            "modules": [{"id": m["id"], "n": m["n"], "title": m["title"], "minutes": m["minutes"]} for m in mods],
            "minutes": sum(m["minutes"] for m in mods) + 30,
            "items": sum(len(module_items(m["id"])) for m in mods), "challenges": len(mods) + 1}


def module_full(m):
    t = TRACK_BY_ID[m["track"]]
    idx = t["modules"].index(m["id"])
    nxt = t["modules"][idx + 1] if idx + 1 < len(t["modules"]) else None
    return {"id": m["id"], "n": m["n"], "title": m["title"], "minutes": m["minutes"], "photo": m["photo"], "summary": m["summary"],
            "briefing": m["briefing"], "do": m["do"], "dont": m["dont"], "sources": [{"label": s[0], "url": s[1]} for s in m["sources"]],
            "cases": [case_brief(CASE_BY_ID[c]) for c in m["cases"] if c in CASE_BY_ID],
            "track": {"id": t["id"], "title": t["title"], "code": t["code"], "count": len(t["modules"])},
            "next": {"id": nxt, "title": MODULES[nxt]["title"]} if nxt else None,
            "items": len(module_items(m["id"])), "cards": len(m["cards"]), "advice": len(m["advice"]),
            "challenge": {"id": m["challenge"]["id"], "title": m["challenge"]["title"]}}


# ------------------------------------------------------------------------------------------- progress
def user_states(user):
    """{item_id: card_state row} for one user."""
    return {r["item"]: r for r in app_tables.card_state.search(user=user)}


def user_progress(user):
    return {r["module"]: r for r in app_tables.module_progress.search(user=user)}


def module_status(module_id, states, prog):
    items = module_items(module_id)
    learned = sum(1 for i in items if i in states and (states[i]["box"] or 0) >= 1)
    mastered = sum(1 for i in items if i in states and (states[i]["box"] or 0) >= 4)
    p = prog.get(module_id)
    read = bool(p and p["read_at"])
    best = int(p["challenge_score"] or 0) if p else 0
    done = bool(p and p["completed_at"])
    steps = int(read) + int(learned == len(items)) + int(best >= PASS_CHALLENGE)
    return {"read": read, "learned": learned, "mastered": mastered, "total": len(items), "challenge": best,
            "challenge_passed": best >= PASS_CHALLENGE, "complete": done, "pct": int(round(100 * (
                (1 if read else 0) + learned / float(len(items)) + (1 if best >= PASS_CHALLENGE else 0)) / 3.0)), "steps": steps}


def track_status(track_id, states, prog, creds):
    t = TRACK_BY_ID[track_id]
    mods = [module_status(mid, states, prog) for mid in t["modules"]]
    done = sum(1 for s in mods if s["complete"])
    cred = creds.get(track_id)
    return {"modules_done": done, "modules": len(mods), "pct": int(round(sum(s["pct"] for s in mods) / float(len(mods)))),
            "exam_ready": done == len(mods), "certified": bool(cred), "credential": cred,
            "started": any(s["pct"] > 0 for s in mods)}


def user_credentials(user):
    """{track_id: {code, issued}} for valid (not revoked) credentials."""
    out = {}
    for r in app_tables.credentials.search(user=user):
        if not r["revoked"]:
            out[r["track"]] = {"code": r["code"], "issued": C.iso(r["issued"])}
    return out


# ------------------------------------------------------------------------------------------- public callables
@anvil.server.callable
def get_catalog():
    """All programs, with the signed-in member's progress."""
    me = C.me()
    out = [track_brief(t) for t in TRACKS]
    if me is not None:
        states, prog, creds = user_states(me), user_progress(me), user_credentials(me)
        for t in out:
            t["status"] = track_status(t["id"], states, prog, creds)
    return {"tracks": out, "cases": len(CASES), "signed_in": me is not None,
            "totals": {"modules": len(MODULES), "items": len(ITEMS), "challenges": len(CHALLENGES)}}


@anvil.server.callable
def get_track(track_id):
    t = TRACK_BY_ID.get(track_id)
    if t is None:
        return C.fail("That program doesn't exist.")
    me = C.me()
    out = track_brief(t)
    out["capstone"] = {"id": t["capstone"]["id"], "title": t["capstone"]["title"]}
    out["modules"] = [dict(module_full(MODULES[mid]), summary=MODULES[mid]["summary"]) for mid in t["modules"]]
    if me is not None:
        states, prog, creds = user_states(me), user_progress(me), user_credentials(me)
        for m in out["modules"]:
            m["status"] = module_status(m["id"], states, prog)
        out["status"] = track_status(track_id, states, prog, creds)
    return C.ok(track=out)


@anvil.server.callable
def get_module(module_id):
    m = MODULES.get(module_id)
    if m is None:
        return C.fail("That module doesn't exist.")
    me = C.me()
    out = module_full(m)
    if me is not None:
        out["status"] = module_status(module_id, user_states(me), user_progress(me))
    return C.ok(module=out)


@anvil.server.callable
def get_cases():
    by_case = {}
    for m in MODULES.values():
        for c in m["cases"]:
            by_case.setdefault(c, []).append({"id": m["id"], "title": m["title"]})
    return {"cases": [dict(case_brief(c), modules=by_case.get(c["id"], [])) for c in CASES]}


@anvil.server.callable
def get_case(case_id):
    c = CASE_BY_ID.get(case_id)
    if c is None:
        return C.fail("That case isn't in the Casebook.")
    mods = [{"id": m["id"], "title": m["title"], "track": TRACK_BY_ID[m["track"]]["title"]} for m in MODULES.values() if case_id in m["cases"]]
    ids = [x["id"] for x in CASES]
    i = ids.index(case_id)
    return C.ok(case=dict(case_brief(c), story=c["story"], lesson=c["lesson"], modules=mods,
                          sources=[{"label": s[0], "url": s[1]} for s in c["sources"]],
                          prev=ids[i - 1] if i > 0 else None, next=ids[i + 1] if i + 1 < len(ids) else None))
