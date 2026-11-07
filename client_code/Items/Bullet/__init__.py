from anvil import *

from ._anvil_designer import BulletTemplate


class Bullet(BulletTemplate):
    """One line of a bulleted list (outcomes). item = {text} or a plain string."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        self.dom_nodes["text"].textContent = i if isinstance(i, str) else (i.get("text") or "")
