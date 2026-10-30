"""Demo content, so the app never looks empty: a cohort of fictional executives with progress, challenge
attempts and credentials (they appear on the Honour Roll and their codes verify, marked as sample records).
Loaded automatically the first time anyone opens the app (ensure_loaded), removed or reloaded from
Admin -> Demo data. Removing it is remembered: it doesn't come back.

Demo users have is_demo=True and @example.com emails; they can't sign in (no password). Every demo row
is flagged is_demo=True, so remove() deletes exactly what load() added.
"""
import datetime as dt

from anvil.tables import app_tables

from . import common as C

# name, email, job title, credentials [(track, days ago, code)], xp
DEMO_USERS = [
    ("Margaret Okafor", "margaret.demo@example.com", "Chief Financial Officer", [("core", 41, "CSC-EXF-2026-M7KQ2R"), ("cfo", 12, "CSC-CFO-2026-T4WX9N")], 2400),
    ("Daniel Reyes", "daniel.demo@example.com", "Chief Operating Officer", [("core", 33, "CSC-EXF-2026-H3PZ8L"), ("coo", 6, "CSC-COO-2026-R9DF2K"), ("ceo", 2, "CSC-CEO-2026-B6YV4M")], 3900),
    ("Aiko Tanaka", "aiko.demo@example.com", "VP Engineering", [("core", 18, "CSC-EXF-2026-Q2NC7X")], 1300),
    ("Elena Vasquez", "elena.demo@example.com", "Chief People Officer", [("core", 25, "CSC-EXF-2026-J8LM3T"), ("chro", 9, "CSC-CHRO-2026-W5KR6P")], 2100),
    ("Samuel Adeyemi", "samuel.demo@example.com", "Chief Information Security Officer", [("core", 15, "CSC-EXF-2026-F4GT9Z"), ("tech", 4, "CSC-CTO-2026-N2HX8Q")], 1900),
    ("Clara Lindqvist", "clara.demo@example.com", "Chief Marketing Officer", [], 640),
]
FELLOW_CODE = "CSC-FEL-2026-D9RV3C"   # Daniel holds core + 2 role certificates

# Tables that hold demo rows (each has an is_demo column). Children before parents.
DEMO_TABLES = ["credentials", "exams", "attempts", "module_progress", "card_state"]


def state():
    return C.get_setting("demo", "never")  # "never" | "loaded" | "removed"


def ensure_loaded():
    """Call from the app's main data callables: loads the demo once, unless an admin removed it."""
    if state() == "never":
        load()


def load():
    from . import Curriculum as K
    remove(remember=False)
    now = C.now()
    for name, email, title, creds, xp in DEMO_USERS:
        u = app_tables.users.get(email=email) or app_tables.users.add_row(email=email, enabled=False)
        u.update(display_name=name, is_demo=True, signed_up=now - dt.timedelta(days=60), job_title=title, honour_roll=True,
                 xp=xp, streak=3, last_study=now.date())
        if creds:
            mods = [mid for track, _d, _c in creds for mid in K.TRACK_BY_ID[track]["modules"]]
        else:
            mods = K.TRACK_BY_ID["core"]["modules"][:3]
        for mid in mods:
            app_tables.module_progress.add_row(user=u, module=mid, read_at=now - dt.timedelta(days=50), challenge_score=80,
                                               completed_at=now - dt.timedelta(days=45), is_demo=True)
            ch = K.MODULES[mid]["challenge"]
            app_tables.attempts.add_row(user=u, challenge=ch["id"], module=mid, score=80, created=now - dt.timedelta(days=45),
                                        answer="(Sample answer from a demo learner.)", points=[True, True, True, True, False], is_demo=True)
            for item in K.module_items(mid):
                app_tables.card_state.add_row(user=u, item=item, module=mid, box=3, due=(now + dt.timedelta(days=4)).date(),
                                              reviews=4, lapses=0, last=now - dt.timedelta(days=3), is_demo=True)
        for track, days, code in creds:
            when = now - dt.timedelta(days=days)
            app_tables.exams.add_row(user=u, track=track, started=when - dt.timedelta(minutes=40), finished=when, card_score=92,
                                     scenario_score=80, passed=True, detail={"items": []}, is_demo=True)
            app_tables.credentials.add_row(user=u, track=track, code=code, holder=name, issued=when, score=86, revoked=False, is_demo=True)
        if name == "Daniel Reyes":
            app_tables.credentials.add_row(user=u, track="fellow", code=FELLOW_CODE, holder=name, issued=now - dt.timedelta(days=1),
                                           score=100, revoked=False, is_demo=True)
    C.set_setting("demo", "loaded")
    return counts()


def remove(remember=True):
    for name in DEMO_TABLES:
        for r in getattr(app_tables, name).search(is_demo=True):
            r.delete()
    for u in app_tables.users.search(is_demo=True):
        u.delete()
    if remember:
        C.set_setting("demo", "removed")
    return counts()


def counts():
    out = {"users": len(app_tables.users.search(is_demo=True))}
    for name in DEMO_TABLES:
        out[name] = len(getattr(app_tables, name).search(is_demo=True))
    return out
