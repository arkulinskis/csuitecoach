"""Server tests against the strict mock of Anvil (tools/testing/mock).

    python tools/testing/test_server.py          -> prints ALL OK, or the first failure

call(name, ...) runs a server function the way the browser does: by name, with require_user enforced,
and the reply must be JSON (a datetime or a row in a reply fails here, like it would break the page).
Add tests for every new server function: the happy path, bad input, and someone who isn't allowed.
"""
import datetime as dt
import importlib
import json
import os
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
_tmp = pathlib.Path(tempfile.mkdtemp())
shutil.copytree(PROJECT / "server_code", _tmp / "app")
(_tmp / "app" / "__init__.py").write_text("")
os.environ["ANVIL_APP_YAML"] = str(PROJECT / "anvil.yaml")  # the mock's tables follow the app's own schema
sys.path[:0] = [str(HERE / "mock"), str(_tmp)]
import anvil.server  # noqa: E402
import anvil.users  # noqa: E402
from anvil.tables import app_tables as T  # noqa: E402

M = {p.stem: importlib.import_module("app." + p.stem) for p in sorted((PROJECT / "server_code").glob("*.py"))}
now = dt.datetime.now(dt.timezone.utc)


def call(name, *args):
    r = anvil.server.call(name, *args)
    json.dumps(r)  # strict: must be JSON-able
    return r


def as_user(row):
    anvil.users.CURRENT[0] = row
    anvil.server.session.use(row.get_id() if row is not None else None)


def denied(name, *args):
    try:
        call(name, *args)
    except anvil.server.PermissionDenied:
        return True
    return False


def ok(r, msg=""):
    assert isinstance(r, dict) and r.get("ok"), (msg, r)
    return r


def bad(r, msg=""):
    assert isinstance(r, dict) and r.get("ok") is False and r.get("error"), (msg, r)
    return r


def person(email, name=None, **kw):
    return T.users.add_row(email=email, enabled=True, signed_up=now, display_name=name, **kw)


# ---------------------------------------------------------------------------------- accounts
admin = person("arkulinskis@gmail.com", "The Admin")
ana = person("ana@example.com", "Ana")
bob = person("bob@example.com")

as_user(None)
assert call("get_me") is None
assert denied("update_profile", "X")
as_user(admin)
assert call("get_me")["is_admin"] is True, "ADMIN_EMAILS become admins on first sign-in"
as_user(ana)
me = call("get_me")
assert me["name"] == "Ana" and me["is_admin"] is False
assert ana["last_seen"] is not None
as_user(bob)
assert call("get_me")["name"] == "Bob", "a name comes from the email when none is set"
bad(call("update_profile", " x "))
assert ok(call("update_profile", "  Bob   Stone "))["me"]["name"] == "Bob Stone"

# ---------------------------------------------------------------------------------- feedback
as_user(None)
bad(call("submit_feedback", "bug", "hi"))
ok(call("submit_feedback", "bug", "The button is broken", "guest@example.com", {"page": "#home", "evil": "x" * 9999}))
fb = T.feedback.search()[0]
assert fb["name"] == "Guest" and fb["email"] == "guest@example.com" and "evil" not in fb["context"] and fb["status"] == "new"
for i in range(4):
    ok(call("submit_feedback", "idea", "Idea number %d" % i))
bad(call("submit_feedback", "idea", "One too many this hour"), "rate limit")
as_user(ana)
ok(call("submit_feedback", "nonsense-kind", "Signed-in feedback"))
assert T.feedback.get(message="Signed-in feedback")["kind"] == "other"
assert denied("list_feedback")
as_user(admin)
lst = call("list_feedback")
assert lst["counts"]["new"] == 6 and len(lst["items"]) == 6
fid = lst["items"][0]["id"]
ok(call("set_feedback_status", fid, "done", "Fixed it"))
assert call("list_feedback", "done")["items"][0]["note"] == "Fixed it"
bad(call("set_feedback_status", fid, "weird"))
bad(call("set_feedback_status", "nope", "done"))
ok(call("delete_feedback", fid))
assert len(call("list_feedback")["items"]) == 5

# ---------------------------------------------------------------------------------- admin
as_user(ana)
for fn, args in [("admin_overview", ()), ("list_users", ()), ("set_admin", (bob.get_id(), True)), ("demo_load", ()), ("demo_remove", ())]:
    assert denied(fn, *args), fn
as_user(admin)
ov = call("admin_overview")
assert ov["users"] == 3 and ov["admins"] == 1 and ov["feedback_new"] == 5 and ov["learners"] == 0
assert len(call("list_users")["users"]) == 3 and len(call("list_users", "bob")["users"]) == 1
ok(call("set_admin", bob.get_id(), True))
assert bob["is_admin"] is True
bad(call("set_admin", admin.get_id(), False), "can't remove your own admin")
ok(call("set_enabled", bob.get_id(), False))
assert bob["enabled"] is False
bad(call("set_enabled", admin.get_id(), False))
ok(call("set_enabled", bob.get_id(), True))
ok(call("set_admin", bob.get_id(), False))
assert bob["is_admin"] is False

# ---------------------------------------------------------------------------------- demo data
K = M["Curriculum"]
as_user(None)
hon = call("get_honour_roll")
assert M["DemoData"].state() == "loaded", "demo loads on first visit"
assert len(hon["items"]) == 5 and all(i["demo"] for i in hon["items"])
as_user(admin)
ok(call("demo_remove"))
assert M["DemoData"].state() == "removed" and not T.users.search(is_demo=True) and not T.credentials.search()
as_user(None)
call("get_honour_roll")
assert M["DemoData"].state() == "removed", "removed demo data doesn't come back by itself"
as_user(admin)
ok(call("demo_load"))
n_creds = len(T.credentials.search())
ok(call("demo_load"))
assert len(T.credentials.search()) == n_creds, "reloading replaces the demo instead of doubling it"
assert call("get_credential", M["DemoData"].FELLOW_CODE)["title"] == "Fellowship of the Institute"

# ---------------------------------------------------------------------------------- curriculum (public)
assert len(K.TRACKS) == 7 and len(K.MODULES) == 24
for mid, m in K.MODULES.items():
    assert len(m["cards"]) >= 5 and len(m["advice"]) == 3 and len(m["challenge"]["rubric"]) >= 4, mid
    assert all(c in M["content_cases"].CASE_BY_ID for c in m["cases"]), mid
    assert m["photo"] and m["challenge"]["photo"], mid
for t in K.TRACKS:
    assert len(t["capstone"]["rubric"]) >= 4 and t["photo"]
assert len(set(K.CHALLENGES)) == 24 + 7
as_user(None)
cat = call("get_catalog")
assert len(cat["tracks"]) == 7 and "status" not in cat["tracks"][0] and cat["totals"]["items"] == len(K.ITEMS)
tr = ok(call("get_track", "cfo"))["track"]
assert tr["code"] == "CFO" and len(tr["modules"]) == 3 and "status" not in tr
bad(call("get_track", "nope"))
mod = ok(call("get_module", "core-decide"))["module"]
assert mod["briefing"] and mod["sources"] and mod["next"]["id"] == "core-direction" and "status" not in mod
bad(call("get_module", "nope"))
cs = call("get_cases")["cases"]
assert len(cs) >= 20 and any(c["modules"] for c in cs)
case = ok(call("get_case", "tylenol"))["case"]
assert case["story"] and case["sources"] and case["next"]
bad(call("get_case", "nope"))
for fn, args in [("get_dashboard", ()), ("get_study", ("review",)), ("rate_item", ("core-decide:c1", True)), ("mark_read", ("core-decide",)),
                 ("get_challenge", ("ch-core-decide",)), ("submit_challenge", ("ch-core-decide", "x" * 50, [True])), ("get_exam", ("core",)),
                 ("submit_exam", ("x", {}, "y", [], True)), ("my_credentials", ()), ("admin_credentials", ()), ("admin_set_revoked", ("x", True))]:
    assert denied(fn, *args), fn
nf = call("get_credential", "CSC-NOPE-0000-AAAAAA")
assert nf["found"] is False

# ---------------------------------------------------------------------------------- learning
as_user(ana)
today = dt.date.today().isoformat()
d = call("get_dashboard", today)
assert d["due"] == 0 and d["next"]["id"] == "core-decide" and d["me"]["rank"]["rank"] == "Analyst" and len(d["tracks"]) == 7
assert len(d["honour"]) >= 1 and d["case"]["id"]
st = ok(call("get_study", "core-decide", today))
assert len(st["items"]) == len(K.module_items("core-decide")) and all(i["box"] is None for i in st["items"])
assert any(i["kind"] == "advice" and "sound" in i for i in st["items"])
bad(call("get_study", "nope"))
bad(call("rate_item", "nope:c1", True))
r1 = ok(call("rate_item", "core-decide:c1", True, today))
assert r1["box"] == 1 and r1["due"] > today and not r1["module_completed"]
r2 = ok(call("rate_item", "core-decide:c2", False, today))
assert r2["box"] == 0 and r2["due"] == today
assert ok(call("get_study", "review", today))["items"][0]["id"] == "core-decide:c2", "a missed card is due today"
ok(call("rate_item", "core-decide:c1", False, today))
assert T.card_state.get(user=ana, item="core-decide:c1")["lapses"] == 1
bad(call("mark_read", "nope"))
assert ok(call("mark_read", "core-decide", today))["first"] is True
assert ok(call("mark_read", "core-decide", today))["first"] is False
ch = ok(call("get_challenge", "ch-core-decide"))
assert ch["challenge"]["rubric"] and ch["best"] == 0 and ch["module"]["id"] == "core-decide"
bad(call("get_challenge", "cap-core"), "capstones are only in exams")
bad(call("submit_challenge", "ch-core-decide", "too short", [True]))
low = ok(call("submit_challenge", "ch-core-decide", "I would delegate the pricing test and slow down the acquisition.", [True, False, False, False, False], today))
assert low["score"] == 20 and not low["passed"]
hi = ok(call("submit_challenge", "ch-core-decide", "Pricing test delegated this week; acquisition gets diligence and a board date; commissions wait.", [True, True, True, True, "yes"], today))
assert hi["score"] == 100 and hi["passed"] and not hi["module_completed"], "cards are not all learned yet"
for item in K.module_items("core-decide"):
    last = ok(call("rate_item", item, True, today))
assert last["module_completed"] and last["module_title"]
assert T.module_progress.get(user=ana, module="core-decide")["completed_at"] is not None
assert ana["xp"] > 0 and ana["streak"] == 1
assert call("get_me")["xp"] == ana["xp"]
d = call("get_dashboard", today)
assert d["modules_done"] == 1 and d["next"]["id"] == "core-direction"
assert ok(call("get_module", "core-decide"))["module"]["status"]["complete"]
assert ok(call("get_track", "core"))["track"]["status"]["modules_done"] == 1
assert call("get_dashboard", "1999-01-01")["me"]["xp"] == ana["xp"], "a silly client date falls back to UTC"
as_user(bob)
assert call("get_dashboard", today)["modules_done"] == 0, "progress is per person"

# ---------------------------------------------------------------------------------- exams + credentials
as_user(ana)
locked = ok(call("get_exam", "core"))
assert locked["state"] == "locked" and len(locked["missing"]) == 5
bad(call("get_exam", "nope"))
# complete every Foundations module the quick way (read + challenge + learn all)
for mid in K.TRACK_BY_ID["core"]["modules"]:
    ok(call("mark_read", mid, today))
    ok(call("submit_challenge", K.MODULES[mid]["challenge"]["id"], "A considered answer that covers the main points well.", [True] * 6, today))
    for item in K.module_items(mid):
        ok(call("rate_item", item, True, today))
ex = ok(call("get_exam", "core"))
assert ex["state"] == "ready" and len(ex["items"]) == K.EXAM_ITEMS and ex["capstone"]["rubric"]
assert ok(call("get_exam", "core"))["exam_id"] == ex["exam_id"], "an open exam is reused"
ratings = {i["id"]: True for i in ex["items"]}
as_user(bob)
bad(call("submit_exam", ex["exam_id"], ratings, "x" * 100, [True] * 5, True), "someone else's exam")
as_user(ana)
bad(call("submit_exam", ex["exam_id"], ratings, "x" * 100, [True] * 5, False), "honour code")
bad(call("submit_exam", ex["exam_id"], {}, "x" * 100, [True] * 5, True), "every item rated")
bad(call("submit_exam", ex["exam_id"], ratings, "short", [True] * 5, True), "scenario answer")
half = dict(ratings)
for k in list(half)[:4]:
    half[k] = False
res = ok(call("submit_exam", ex["exam_id"], half, "My plan for the first ninety days covers safety, guidance, the product line and the team." * 2, [True] * 5, True, today))
assert not res["passed"] and res["drill"] == 67 and res["code"] is None
bad(call("submit_exam", ex["exam_id"], ratings, "x" * 100, [True] * 5, True), "already submitted")
assert ok(call("get_exam", "core"))["state"] == "cooldown"
assert T.card_state.get(user=ana, item=list(half)[0])["box"] == 0, "missed exam items go back to box 0"
for r in T.exams.search(user=ana):  # pretend the cooldown has passed
    r["finished"] = r["finished"] - dt.timedelta(hours=1)
ex2 = ok(call("get_exam", "core"))
assert ex2["state"] == "ready" and ex2["exam_id"] != ex["exam_id"]
res = ok(call("submit_exam", ex2["exam_id"], {i["id"]: True for i in ex2["items"]}, "A complete answer to the capstone scenario with priorities and order." * 2, [True] * 5, True, today))
assert res["passed"] and res["code"].startswith("CSC-EXF-") and res["fellow"] is None
assert ok(call("get_exam", "core"))["state"] == "certified"
mine = call("my_credentials")
assert len(mine["items"]) == 1 and mine["fellow"]["core"] and not mine["fellow"]["have"]
pub = call("get_credential", res["code"].lower())
assert pub["found"] and pub["holder"] == "Ana" and pub["status"] == "valid" and pub["mine"] and pub["modules"]
assert "email" not in pub
as_user(None)
assert call("get_credential", res["code"])["mine"] is False
# Fellowship: core + two role certificates
for track in ("cfo", "coo"):
    Ex = M["Exams"]
    Ex.issue(ana, track, 90)
assert Ex.maybe_fellow(ana) is not None and K.user_credentials(ana).get("fellow")
assert Ex.maybe_fellow(ana) is None, "only one fellowship"
# honour roll is opt-in
as_user(ana)
assert all(i["name"] != "Ana" for i in call("get_honour_roll")["items"])
me2 = ok(call("update_profile", "Ana Lima", "VP Finance", True))["me"]
assert me2["title"] == "VP Finance" and me2["honour_roll"]
assert any(i["name"] == "Ana" for i in call("get_honour_roll")["items"]), "holder name is kept as issued"
# admin: list and revoke
as_user(ana)
assert denied("admin_credentials")
as_user(admin)
lst = call("admin_credentials", "ana")
assert lst["total"] >= 4 and lst["items"][0]["email"] == "ana@example.com"
ok(call("admin_set_revoked", res["code"], True))
assert call("get_credential", res["code"])["status"] == "revoked"
bad(call("admin_set_revoked", "nope", True))
ok(call("admin_set_revoked", res["code"], False))
ov = call("admin_overview")
assert ov["credentials"] >= 4 and ov["attempts"] >= 7 and ov["exams"] == 2 and ov["modules_done"] == 6

# ---------------------------------------------------------------------------------- Privacy & Terms
if "legal_server" in M:
    as_user(ana)
    st = call("legal_state")
    assert st["signedIn"] and st["accepted_version"] is None
    ok(call("legal_accept", st["version"], "signup"))
    assert ana["legal_source"] == "signup" and call("legal_state")["accepted_version"] == st["version"]

# ---------------------------------------------------------------------------------- every callable is covered by a permission check
# A callable that changes data without require_user / a C.require_* check is a security hole. List the public ones here.
PUBLIC = {"get_me", "submit_feedback", "legal_state", "legal_accept", "get_catalog", "get_track", "get_module", "get_cases",
          "get_case", "get_honour_roll", "get_credential"}
for name, (f, need) in sorted(anvil.server.CALLABLES.items()):
    if name in PUBLIC:
        continue
    assert need, "%s is callable by anyone: add require_user=True (or list it in PUBLIC in test_server.py)" % name

print("ALL OK (%d server functions)" % len(anvil.server.CALLABLES))
