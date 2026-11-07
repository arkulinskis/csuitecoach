from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import DrillTemplate
from ... import state


class Drill(DrillTemplate):
    """The flashcard engine (the CAF Guide method: reveal, then rate yourself honestly).

    Card: question -> Reveal -> answer -> "Still learning" / "Got it".
    Advice call: statement -> "Sound advice, or a trap?" -> Reveal verdict + why -> "I missed it" / "I called it".
    Outside exams, "Still learning" items come back once at the end of the session. Keys: Space/Enter reveal, 1 / 2 rate.
    start(items, exam, rate, done): rate(item, knew) may call the server (it runs before the next card shows);
    done(stats) gets {got, missed, ratings: {item id: knew}} once every card is rated."""

    def __init__(self, **properties):
        self._queue: list = []
        self._i, self._revealed, self._busy, self._exam = 0, False, False, False
        self._again: dict = {}
        self._stats: dict = {"got": 0, "missed": 0, "ratings": {}}
        self._total = 0
        self._rate = None
        self._done = None
        self._listening = False
        super().__init__(**properties)
        self._key_fn = anvil.js.report_exceptions(self._key)
        self.card.visible = False  # nothing to press until start() deals the first card

    # ---- public
    def start(self, items, exam=False, rate=None, done=None):
        self._queue = list(items or [])
        self._i, self._revealed, self._busy, self._exam = 0, False, False, bool(exam)
        self._again, self._stats = {}, {"got": 0, "missed": 0, "ratings": {}}
        self._total = len(self._queue)
        self._rate, self._done = rate, done
        self.card.visible = True
        self._listen(True)
        self._draw()

    # ---- drawing
    def _cur(self):
        return self._queue[self._i] if self._i < len(self._queue) else None

    def _draw(self):
        it = self._cur()
        if it is None:
            self._listen(False)
            if self._done is not None:
                self._done(self._stats)
            return
        answered = len(self._stats["ratings"])
        adv = it.get("kind") == "advice"
        self.bar.pct = 100.0 * answered / max(1, self._total)
        extra = len(self._queue) - self._total
        self.dom_nodes["count"].textContent = "%d / %d%s" % (min(answered + 1, self._total), self._total,
                                                             (" · +%d again" % extra) if extra > 0 else "")
        self.card.classes["advice"] = adv
        self.b_advice.visible, self.b_recall.visible = adv, not adv
        self.dom_nodes["b_mod"].textContent = "%s · %s" % (it.get("track_code") or "", it.get("module_title") or "")
        box = it.get("box")
        self.b_box.visible = box is not None and box > 0
        self.dom_nodes["box_n"].textContent = "Box %s" % box if box else ""
        self.b_new.visible = box is None and not self._exam
        q = self.dom_nodes["q"]
        q.textContent = it.get("q") or ""
        q.className = "q quote" if adv else "q"
        self.dom_nodes["prompt"].textContent = (
            "Sound advice for an executive, or a trap? Decide, then reveal." if adv
            else "Answer from memory, out loud or in your head, then reveal.")
        r = self._revealed
        self.back.visible = r
        if r:
            self.verdict.visible = adv
            if adv:
                sound = bool(it.get("sound"))
                self.verdict.classes["sound"], self.verdict.classes["trap"] = sound, not sound
                self.dom_nodes["verdict_ic"].className = "ic ic-check" if sound else "ic ic-alert"
                self.dom_nodes["verdict_t"].textContent = "Sound advice" if sound else "A trap"
            self.dom_nodes["a"].textContent = it.get("a") or ""
            note = self.dom_nodes["note"]
            note.textContent = it.get("note") or ""
            note.hidden = not it.get("note")
        self.reveal_button.visible = not r
        self.reveal_button.text = "Reveal the verdict" if adv else "Reveal the answer"
        self.no_button.visible = self.yes_button.visible = r
        self.no_button.text = "I missed it" if adv else "Still learning"
        self.yes_button.text = "I called it" if adv else "Got it"
        self.dom_nodes["keys"].textContent = "Space to reveal · 1 %s · 2 %s" % (
            "missed" if adv else "still learning", "called it" if adv else "got it")

    # ---- actions
    def _reveal(self):
        if self._revealed:
            return
        self._revealed = True
        self._draw()
        state.focus(self.yes_button)

    def _rate_it(self, knew):
        if not self._revealed or self._busy:
            return
        it = self._cur()
        if it is None:
            return
        if it["id"] not in self._stats["ratings"]:
            self._stats["ratings"][it["id"]] = bool(knew)
            self._stats["got" if knew else "missed"] += 1
        if not knew and not self._exam and not self._again.get(it["id"]):
            self._again[it["id"]] = 1
            self._queue.append(it)
        self._busy = True
        try:
            if self._rate is not None:
                self._rate(it, bool(knew))
            self._i += 1
            self._revealed = False
        finally:
            self._busy = False
        self._draw()
        if self._cur() is not None:
            state.focus(self.reveal_button)

    @handle("reveal_button", "click")
    def reveal_button_click(self, **event_args):
        self._reveal()

    @handle("no_button", "click")
    def no_button_click(self, **event_args):
        self._rate_it(False)

    @handle("yes_button", "click")
    def yes_button_click(self, **event_args):
        self._rate_it(True)

    # ---- keyboard
    def _listen(self, on):
        if on and not self._listening:
            window.document.addEventListener("keydown", self._key_fn)
            self._listening = True
        elif not on and self._listening:
            window.document.removeEventListener("keydown", self._key_fn)
            self._listening = False

    def _key(self, event):
        tag = str(getattr(event.target, "tagName", "") or "")
        if tag in ("INPUT", "TEXTAREA", "SELECT"):
            return
        k = event.key
        if k in (" ", "Enter"):
            if not self._revealed:
                event.preventDefault()
                self._reveal()
        elif k == "1":
            self._rate_it(False)
        elif k == "2":
            self._rate_it(True)

    @handle("", "hide")
    def form_hide(self, **event_args):
        self._listen(False)

    @handle("", "show")
    def form_show(self, **event_args):
        if self._cur() is not None and self._total:
            self._listen(True)
