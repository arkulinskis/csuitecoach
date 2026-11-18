"""Team plan: a company enrols its leaders and follows their progress.

One person (the team manager) creates a team, then invites leaders by name and email with the programs they should
complete. Each invite is a personal link (#join/<token>), emailed and also shown to copy. The invited person opens it,
creates an account or signs in, and joins: from then on the manager sees their progress.

What a manager sees about a member: the name and email the manager typed on the invite, the member's profile name,
per assigned program the modules done, progress and certificate, their certificates, drills learned, streak and the
last day they studied. Never their written answers or exam details. Members can leave at any time (Profile / #team).

Tables: teams (one per manager), team_members (an invite, then a membership: status invited | active | left | removed).
A person belongs to at most one team at a time; joining another leaves the old one.
"""
import secrets as _secrets

import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import Curriculum as K

MAX_INVITES = 200        # rows per team (members + open invites)
BATCH = 50               # invites per click
EMAIL_LIMIT = (60, 3600)  # invite emails per browser session per hour


def _token():
    return _secrets.token_urlsafe(18)


def _valid_email(s):
    return "@" in s and "." in s.split("@")[-1] and " " not in s and len(s) <= 200


def _clean_tracks(tracks):
    ids = [t for t in (tracks or []) if isinstance(t, str) and t in K.TRACK_BY_ID]
    return [t["id"] for t in K.TRACKS if t["id"] in ids]  # catalogue order, no duplicates


def my_team(user):
    """The team this user manages, or None."""
    return app_tables.teams.get(owner=user) if user is not None else None


def my_membership(user):
    if user is None:
        return None
    for r in app_tables.team_members.search(user=user, status="active"):
        return r
    return None


def _origin():
    try:
        return anvil.server.get_app_origin()
    except Exception:
        return ""


def join_url(row):
    return "%s/#join/%s" % (_origin(), row["token"])


def _esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _send_invite(row, manager):
    """Email one invite. Returns True when it went out."""
    team = row["team"]
    who = C.name_of(manager)
    titles = [K.TRACK_BY_ID[t]["title"] for t in (row["tracks"] or []) if t in K.TRACK_BY_ID]
    url = join_url(row)
    subject = "%s invited you to %s's leadership training" % (who, team["name"])
    progs = ("<p style=\"margin:0 0 14px;font:15px/1.6 Georgia,serif;color:#14213d\">Programs to complete: <b>%s</b>.</p>"
             % _esc(", ".join(titles))) if titles else ""
    html = ("<div style=\"max-width:560px;margin:0 auto;padding:28px 24px;background:#f7f4ec;border-top:4px solid #b08d57\">"
            "<p style=\"margin:0 0 6px;font:22px Georgia,serif;color:#14213d\">You're invited</p>"
            "<p style=\"margin:0 0 14px;font:15px/1.6 Georgia,serif;color:#14213d\">Hello %s,</p>"
            "<p style=\"margin:0 0 14px;font:15px/1.6 Georgia,serif;color:#14213d\">%s has enrolled you in <b>%s</b> on "
            "C-Suite Coach, an executive-education program with real business cases, boardroom challenges and certificates.</p>%s"
            "<p style=\"margin:0 0 14px;font:15px/1.6 Georgia,serif;color:#14213d\">Open your personal link, create your account "
            "(or sign in) and join the team. Your manager will then see your progress and certificates, never your written answers.</p>"
            "<p style=\"margin:22px 0\"><a href=\"%s\" style=\"display:inline-block;background:#14213d;color:#ffffff;"
            "text-decoration:none;padding:12px 22px;border-radius:6px;font:600 15px Arial,sans-serif\">Join the team</a></p>"
            "<p style=\"margin:0;font:12px/1.5 Arial,sans-serif;color:#5a6274\">Or paste this link into your browser: %s<br>"
            "If you weren't expecting this, you can ignore this email.</p></div>"
            % (_esc(row["name"] or "there"), _esc(who), _esc(team["name"]), progs, _esc(url), _esc(url)))
    text = ("Hello %s,\n\n%s has enrolled you in %s on C-Suite Coach.\n%s\nJoin the team with your personal link:\n%s\n\n"
            "Your manager will see your progress and certificates, never your written answers.\n"
            "If you weren't expecting this, you can ignore this email."
            % (row["name"] or "there", who, team["name"], ("Programs: %s\n" % ", ".join(titles)) if titles else "", url))
    try:
        import anvil.email
        anvil.email.send(to=row["email"], subject=subject, text=text, html=html, from_name="C-Suite Coach")
        row["last_sent"] = C.now()
        return True
    except Exception as e:
        print("invite email failed:", e)
        return False


# ------------------------------------------------------------------------------------------- what a manager sees
def _member_view(row, catalog_states=None):
    u = row["user"]
    out = {"id": row.get_id(), "name": row["name"] or "", "email": row["email"] or "", "status": row["status"],
           "invited": C.iso(row["invited"]), "joined": C.iso(row["joined"]), "last_sent": C.iso(row["last_sent"]),
           "tracks": [], "credentials": [], "display_name": "", "last_study": None, "streak": 0, "learned": 0,
           "pct": 0, "certified": 0, "assigned": len(row["tracks"] or []), "demo": bool(row["is_demo"])}
    if row["status"] == "invited":
        out["link"] = join_url(row)
    if u is None or row["status"] != "active":
        out["tracks"] = [{"id": t, "title": K.TRACK_BY_ID[t]["title"], "pct": 0, "modules_done": 0,
                          "modules": len(K.TRACK_BY_ID[t]["modules"]), "certified": False}
                         for t in (row["tracks"] or []) if t in K.TRACK_BY_ID]
        return out
    states, prog, creds = K.user_states(u), K.user_progress(u), K.user_credentials(u)
    for t in (row["tracks"] or []):
        if t not in K.TRACK_BY_ID:
            continue
        s = K.track_status(t, states, prog, creds)
        out["tracks"].append({"id": t, "title": K.TRACK_BY_ID[t]["title"], "pct": s["pct"], "modules_done": s["modules_done"],
                              "modules": s["modules"], "certified": s["certified"]})
    out["display_name"] = C.name_of(u)
    out["last_study"] = C.iso(u["last_study"])
    out["streak"] = u["streak"] or 0
    out["learned"] = sum(1 for r in states.values() if (r["box"] or 0) >= 1)
    out["credentials"] = [{"track": k, "credential": K.credential_name(k), "code": v["code"], "issued": v["issued"]}
                          for k, v in sorted(creds.items(), key=lambda kv: kv[1]["issued"] or "")]
    if out["tracks"]:
        out["pct"] = int(round(sum(x["pct"] for x in out["tracks"]) / float(len(out["tracks"]))))
        out["certified"] = sum(1 for x in out["tracks"] if x["certified"])
    return out


def _team_view(team):
    rows = [r for r in app_tables.team_members.search(team=team) if r["status"] in ("invited", "active", "left")]
    order = {"active": 0, "invited": 1, "left": 2}
    rows.sort(key=lambda r: (order.get(r["status"], 3), (r["name"] or r["email"] or "").lower()))
    members = [_member_view(r) for r in rows]
    active = [m for m in members if m["status"] == "active"]
    return {"id": team.get_id(), "name": team["name"], "created": C.iso(team["created"]),
            "tracks": _clean_tracks(team["tracks"]), "members": members,
            "stats": {"active": len(active), "invited": sum(1 for m in members if m["status"] == "invited"),
                      "avg": int(round(sum(m["pct"] for m in active) / float(len(active)))) if active else 0,
                      "certificates": sum(len(m["credentials"]) for m in active),
                      "done": sum(1 for m in active if m["assigned"] and m["certified"] == m["assigned"])}}


def _membership_view(row):
    team = row["team"]
    return {"id": row.get_id(), "team": team["name"], "manager": C.name_of(team["owner"]), "joined": C.iso(row["joined"]),
            "tracks": [{"id": t, "title": K.TRACK_BY_ID[t]["title"]} for t in (row["tracks"] or []) if t in K.TRACK_BY_ID]}


def team_for_dashboard(user):
    """{team, manager, tracks: [ids]} for the member's dashboard, or None."""
    row = my_membership(user)
    if row is None:
        return None
    v = _membership_view(row)
    return {"team": v["team"], "manager": v["manager"], "tracks": [t["id"] for t in v["tracks"]]}


def _catalog():
    return [{"id": t["id"], "title": t["title"], "code": t["code"]} for t in K.TRACKS]


# ------------------------------------------------------------------------------------------- callables
@anvil.server.callable(require_user=True)
def get_team():
    """Everything the #team page needs: the team you manage (with its members' progress), and/or the team you're in."""
    me = C.require_user()
    team = my_team(me)
    mem = my_membership(me)
    return {"managed": _team_view(team) if team else None, "membership": _membership_view(mem) if mem else None,
            "catalog": _catalog(), "max_invites": MAX_INVITES}


@anvil.server.callable(require_user=True)
def create_team(name, tracks=None):
    me = C.require_user()
    name = C.text(name, 80)
    if len(name) < 2:
        return C.fail("Give your team a name (your company's name works well).")
    if my_team(me) is not None:
        return C.fail("You already manage a team.")
    tracks = _clean_tracks(tracks) or ["core"]
    app_tables.teams.add_row(name=name, owner=me, created=C.now(), tracks=tracks, is_demo=False)
    return C.ok(team=_team_view(my_team(me)))


@anvil.server.callable(require_user=True)
def update_team(name=None, tracks=None):
    me = C.require_user()
    team = my_team(me)
    if team is None:
        return C.fail("You don't manage a team.")
    if name is not None:
        name = C.text(name, 80)
        if len(name) < 2:
            return C.fail("Give your team a name.")
        team["name"] = name
    if tracks is not None:
        team["tracks"] = _clean_tracks(tracks) or ["core"]
    return C.ok(team=_team_view(team))


@anvil.server.callable(require_user=True)
def delete_team():
    """Removes the team, its open invites and every membership. Members keep their own progress and certificates."""
    me = C.require_user()
    team = my_team(me)
    if team is None:
        return C.fail("You don't manage a team.")
    for r in app_tables.team_members.search(team=team):
        r.delete()
    team.delete()
    return C.ok()


def _parse_people(text):
    """'Name, email' (or 'Name <email>', or just an email) per line -> [(name, email)], [bad lines]."""
    out, bad = [], []
    for line in (text or "").replace(";", "\n").splitlines():
        line = line.strip()
        if not line:
            continue
        email, name = "", ""
        if "<" in line and line.endswith(">"):
            name, email = line[:line.index("<")], line[line.index("<") + 1:-1]
        elif "," in line or "\t" in line:
            parts = [p.strip() for p in line.replace("\t", ",").split(",") if p.strip()]
            email = next((p for p in parts if "@" in p), "")
            name = " ".join(p for p in parts if p != email)
        else:
            email = line if "@" in line else ""
            name = "" if email else line
        email, name = C.text(email, 200).lower().strip("<>"), C.text(name, 80).strip("\"' ")
        if not _valid_email(email):
            bad.append(line[:80])
            continue
        out.append((name or email.split("@")[0].replace(".", " ").title(), email))
    return out, bad


@anvil.server.callable(require_user=True)
def invite_people(people, tracks, send_email=True):
    """people = text, one person per line ('Name, email'). Creates one personal invite each and emails it (optional).
    An email that already has an open invite or an active membership is skipped."""
    me = C.require_user()
    team = my_team(me)
    if team is None:
        return C.fail("Create your team first.")
    tracks = _clean_tracks(tracks)
    if not tracks:
        return C.fail("Pick at least one program for them to complete.")
    found, bad = _parse_people(C.text(people, 20000, multiline=True))
    if not found:
        return C.fail("Add at least one person as 'Name, email', one per line.")
    if len(found) > BATCH:
        return C.fail("Invite up to %d people at a time." % BATCH)
    rows = list(app_tables.team_members.search(team=team))
    current = {(r["email"] or "").lower() for r in rows if r["status"] in ("invited", "active")}
    open_rows = sum(1 for r in rows if r["status"] in ("invited", "active"))
    made, skipped, sent, unsent = [], [], 0, 0
    for name, email in found:
        if email in current:
            skipped.append(email)
            continue
        if open_rows >= MAX_INVITES:
            return C.fail("A team can have up to %d people. Remove someone first." % MAX_INVITES)
        row = app_tables.team_members.add_row(team=team, name=name, email=email, token=_token(), tracks=tracks,
                                              invited=C.now(), status="invited", is_demo=False)
        current.add(email)
        open_rows += 1
        if send_email:
            if C.rate_limited("team_invite", EMAIL_LIMIT[0], EMAIL_LIMIT[1]) or not _send_invite(row, me):
                unsent += 1
            else:
                sent += 1
        made.append({"name": name, "email": email, "link": join_url(row)})
    team["tracks"] = tracks  # the next invite starts from the same programs
    return C.ok(made=made, skipped=skipped, bad=bad, sent=sent, unsent=unsent, team=_team_view(team))


def _own_row(member_id):
    me = C.require_user()
    team = my_team(me)
    row = C.row_by_id(app_tables.team_members, member_id)
    if team is None or row is None or row["team"] != team:
        return me, None
    return me, row


@anvil.server.callable(require_user=True)
def resend_invite(member_id):
    me, row = _own_row(member_id)
    if row is None or row["status"] != "invited":
        return C.fail("That invite isn't open any more.")
    if C.rate_limited("team_invite", EMAIL_LIMIT[0], EMAIL_LIMIT[1]):
        return C.fail("That's a lot of emails for one hour. Copy the link and send it yourself, or try later.")
    if not _send_invite(row, me):
        return C.fail("The email couldn't be sent. Copy the link and send it yourself.")
    return C.ok(sent_to=row["email"])


@anvil.server.callable(require_user=True)
def set_member_tracks(member_id, tracks):
    me, row = _own_row(member_id)
    if row is None or row["status"] not in ("invited", "active"):
        return C.fail("That person isn't in your team.")
    tracks = _clean_tracks(tracks)
    if not tracks:
        return C.fail("Pick at least one program.")
    row["tracks"] = tracks
    return C.ok(member=_member_view(row))


@anvil.server.callable(require_user=True)
def remove_member(member_id):
    """An open invite is cancelled (its link stops working); a member is removed from the team (their own account,
    progress and certificates stay theirs); a 'left' row is cleared from the list."""
    me, row = _own_row(member_id)
    if row is None:
        return C.fail("That person isn't in your team.")
    if row["status"] == "active":
        row["status"] = "removed"
        row["token"] = None
    else:
        row.delete()
    return C.ok()


@anvil.server.callable
def get_invite(token):
    """Public: what an invite link says (team, who invited, which programs). No emails go back."""
    me = C.me()
    row = app_tables.team_members.get(token=token) if isinstance(token, str) and 8 <= len(token) <= 64 else None
    if row is None or row["status"] not in ("invited", "active"):
        return {"ok": True, "found": False}
    team = row["team"]
    out = {"ok": True, "found": True, "team": team["name"], "manager": C.name_of(team["owner"]), "name": row["name"] or "",
           "tracks": [{"id": t, "title": K.TRACK_BY_ID[t]["title"], "blurb": K.TRACK_BY_ID[t]["blurb"]}
                      for t in (row["tracks"] or []) if t in K.TRACK_BY_ID],
           "used": row["status"] == "active", "signed_in": me is not None, "mine": False, "other_team": None}
    if me is not None:
        out["mine"] = row["user"] == me
        cur = my_membership(me)
        if cur is not None and cur["team"] != team:
            out["other_team"] = cur["team"]["name"]
    return out


@anvil.server.callable(require_user=True)
def accept_invite(token):
    me = C.require_user()
    row = app_tables.team_members.get(token=token) if isinstance(token, str) and 8 <= len(token) <= 64 else None
    if row is None or row["status"] not in ("invited", "active"):
        return C.fail("This invite link isn't valid any more. Ask your team manager for a new one.")
    if row["status"] == "active":
        if row["user"] == me:
            return C.ok(team=row["team"]["name"], already=True)
        return C.fail("This invite has already been used. Ask your team manager for your own link.")
    team = row["team"]
    for old in app_tables.team_members.search(user=me, status="active"):
        if old["team"] != team:
            old["status"] = "left"  # one team at a time
    for dup in app_tables.team_members.search(team=team, user=me, status="active"):
        dup["status"] = "left"
    row["user"], row["status"], row["joined"] = me, "active", C.now()
    return C.ok(team=team["name"], already=False)


@anvil.server.callable(require_user=True)
def leave_team():
    me = C.require_user()
    row = my_membership(me)
    if row is None:
        return C.fail("You're not in a team.")
    row["status"] = "left"
    row["token"] = None
    return C.ok()


def counts():
    """For Admin -> Overview."""
    return {"teams": len(app_tables.teams.search()), "team_members": len(app_tables.team_members.search(status="active"))}

