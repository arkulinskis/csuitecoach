from anvil import *

from ._anvil_designer import LinkButtonTemplate


class LinkButton(LinkButtonTemplate):
    """A link that looks like a button. item = {text, href, kind ('primary', 'gold', 'ghost', 'ghostl' or ''),
    size ('sm', 'lg' or ''), icon, after (icon after the text), block, external}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        a = self.dom_nodes["a"]
        a.setAttribute("href", i.get("href") or "#")
        if i.get("external"):
            a.setAttribute("target", "_blank")
            a.setAttribute("rel", "noopener")
        a.className = " ".join(c for c in ["ui-btn", i.get("kind") or "", i.get("size") or "",
                                            "block" if i.get("block") else ""] if c)
        self.dom_nodes["text"].textContent = i.get("text") or ""
        icon = i.get("icon")
        slot = self.dom_nodes["ic2" if i.get("after") else "ic1"]
        if icon:
            slot.className = "ic ic-" + icon
            slot.hidden = False
