from anvil import *

from ._anvil_designer import LinkBoxTemplate
from ... import state


class LinkBox(LinkBoxTemplate):
    """Shows a link to copy by hand (when the browser doesn't allow copying to the clipboard)."""

    def __init__(self, link="", **properties):
        super().__init__(**properties)
        self.link_box.text = link

    @handle("", "show")
    def form_show(self, **event_args):
        state.control(self.link_box).select()

    @handle("close_button", "click")
    def close_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)
