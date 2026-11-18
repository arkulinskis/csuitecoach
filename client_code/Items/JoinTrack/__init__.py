from anvil import *

from ._anvil_designer import JoinTrackTemplate


class JoinTrack(JoinTrackTemplate):
    """A program on a team invite page. item = {id, title, blurb}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.dom_nodes["title"].textContent = self.item["title"]
        self.dom_nodes["blurb"].textContent = self.item.get("blurb") or ""
