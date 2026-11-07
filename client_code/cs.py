"""C-Suite Coach helpers on top of state.py: the JavaScript engines in theme/assets/cs-cert.js (seal, certificate,
progress ring, confetti), dates in the browser's language, photos, and small text helpers the pages share.

    cs.today()                the member's local date (YYYY-MM-DD): streaks and due dates follow their day
    cs.photo(name)            '_/theme/<name>.jpg' (the Pexels photos of people in suits)
    cs.date(iso, style)       'short' | 'long' | 'month' | 'time'
    cs.confetti()             gold confetti for a pass (nothing under reduced motion)
    cs.verify_url(code)       the public verification address of a credential
    cs.js(value)              a Python dict/list as a real JS object (for the engines)
    cs.set_text(node, text)   textContent on an anvil:dom-node
    cs.title(text)            the browser tab title: "<text> · C-Suite Coach"
"""
import json

from anvil.js import window

APP_NAME = "C-Suite Coach"
INSTITUTE = "C-Suite Coach Institute"


def today():
    return str(window.CS.today())


def photo(name):
    return "_/theme/%s.jpg" % (name or "ph-boardroom")


def date(iso, style="short"):
    return str(window.CS.fmtDate(iso or "", style)) if iso else ""


def ago(iso):
    from . import state
    return state.ago(iso)


def confetti():
    window.CS.confetti()


def verify_url(code):
    return str(window.CS.verifyUrl(code))


def weekday(day):
    return str(window.CS.weekday(day))


def js(value):
    return window.JSON.parse(json.dumps(value))


def set_text(node, text):
    node.textContent = "" if text is None else str(text)


def title(text):
    window.document.title = "%s · %s" % (text, APP_NAME)


def hours(minutes):
    """'~1.5' hours from minutes, like the JavaScript version (one decimal)."""
    return "%g" % (round((minutes or 0) / 6.0) / 10.0)


def tone_badge(tone):
    """(text, badge roles) for a case's lesson type."""
    if tone == "exemplary":
        return "Exemplary", ["badge", "badge-good"]
    if tone == "cautionary":
        return "Cautionary", ["badge", "badge-bad"]
    return "Mixed lessons", ["badge", "badge-warn"]
