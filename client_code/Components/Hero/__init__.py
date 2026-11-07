from anvil import *

from ._anvil_designer import HeroTemplate
from ... import cs


class Hero(HeroTemplate):
    """The photo band at the top of most pages (the old CS.hero). Set its properties from the page's Python."""

    def __init__(self, **properties):
        self._p: dict = {"photo": "ph-boardroom", "title": "", "lead": "", "crumbs": [], "meta": [], "actions": []}
        self._ready = False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def set(self, **values):
        """Several properties at once, drawn once."""
        self._p.update(values)
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        p = self._p
        self.dom_nodes["ph"].style.backgroundImage = "url(%s)" % cs.photo(p.get("photo"))
        cs.set_text(self.dom_nodes["h1"], p.get("title"))
        lead = self.dom_nodes["lead"]
        cs.set_text(lead, p.get("lead"))
        lead.hidden = not p.get("lead")
        crumbs = list(p.get("crumbs") or [])
        self.crumbs_panel.items = [{"href": c[0], "label": c[1], "first": i == 0} for i, c in enumerate(crumbs)]
        self.crumbs_box.visible = bool(crumbs)
        meta = list(p.get("meta") or [])
        self.meta_panel.items = [{"icon": m[0], "text": m[1]} for m in meta]
        self.meta_box.visible = bool(meta)
        actions = list(p.get("actions") or [])
        self.actions_panel.items = actions
        self.actions_box.visible = bool(actions)

    def _put(self, name, value):
        self._p[name] = value
        self._draw()

    @property
    def photo(self):
        return self._p["photo"]

    @photo.setter
    def photo(self, value):
        self._put("photo", value)

    @property
    def title(self):
        return self._p["title"]

    @title.setter
    def title(self, value):
        self._put("title", value)

    @property
    def lead(self):
        return self._p["lead"]

    @lead.setter
    def lead(self, value):
        self._put("lead", value)

    @property
    def crumbs(self):
        return self._p["crumbs"]

    @crumbs.setter
    def crumbs(self, value):
        self._put("crumbs", value)

    @property
    def meta(self):
        return self._p["meta"]

    @meta.setter
    def meta(self, value):
        self._put("meta", value)

    @property
    def actions(self):
        return self._p["actions"]

    @actions.setter
    def actions(self, value):
        self._put("actions", value)
