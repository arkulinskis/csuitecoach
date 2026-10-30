"""Credentials: a member's certificates, public certificate pages and verification, and admin revocation.

A certificate page shows the holder's name (as it was when issued), the credential, the date and its status.
Anyone with the code can verify it; that's the point of a credential. Nothing else about the holder is shown.
"""
import anvil.server
from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C
from . import Curriculum as K


def cred_public(r):
    track = r["track"]
    t = K.FELLOW if track == "fellow" else K.TRACK_BY_ID.get(track, {})
    return {"code": r["code"], "holder": r["holder"], "track": track, "title": K.track_title(track),
            "credential": K.credential_name(track), "track_code": t.get("code", ""), "issued": C.iso(r["issued"]),
            "status": "revoked" if r["revoked"] else "valid", "demo": bool(r["is_demo"]),
            "outcomes": t.get("outcomes", []), "modules": [K.MODULES[m]["title"] for m in t.get("modules", [])]}


def _find(code):
    code = C.text(code, 40).upper().replace(" ", "")
    if not code:
        return None
    return app_tables.credentials.get(code=code)


@anvil.server.callable(require_user=True)
def my_credentials():
    me = C.require_user()
    rows = sorted(app_tables.credentials.search(user=me), key=lambda r: r["issued"])
    have = {r["track"] for r in rows if not r["revoked"]}
    roles = [t for t in have if t not in ("core", "fellow")]
    return {"items": [cred_public(r) for r in rows], "honour_roll": bool(me["honour_roll"]),
            "fellow": {"have": "fellow" in have, "core": "core" in have, "roles": len(roles), "need_roles": 2},
            "tracks": [{"id": t["id"], "title": t["title"], "credential": t["credential"], "have": t["id"] in have} for t in K.TRACKS]}


@anvil.server.callable
def get_credential(code):
    """Public: verify a credential code. Returns the certificate details, or found=False."""
    if C.rate_limited("verify", 60, 600):
        return C.fail("Too many lookups. Please wait a few minutes.")
    r = _find(code)
    if r is None:
        return {"found": False}
    out = cred_public(r)
    out["found"] = True
    me = C.me()
    out["mine"] = me is not None and r["user"] == me
    return out


# ------------------------------------------------------------------------------------------- admin
@anvil.server.callable(require_user=True)
def admin_credentials(query=None):
    C.require_admin()
    q = C.text(query, 60).lower()
    rows = list(app_tables.credentials.search(tables.order_by("issued", ascending=False)))
    if q:
        rows = [r for r in rows if q in (r["code"] or "").lower() or q in (r["holder"] or "").lower()]
    out = []
    for r in rows[:300]:
        d = cred_public(r)
        d["email"] = r["user"]["email"] if r["user"] is not None else ""
        out.append(d)
    return {"items": out, "total": len(rows)}


@anvil.server.callable(require_user=True)
def admin_set_revoked(code, flag):
    C.require_admin()
    r = _find(code)
    if r is None:
        return C.fail("No credential with that code.")
    r["revoked"] = bool(flag)
    return C.ok(item=cred_public(r))
