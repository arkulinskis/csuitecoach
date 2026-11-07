from anvil import *

from ._anvil_designer import ExamReadyTemplate


class ExamReady(ExamReadyTemplate):
    """"Examination open" card on the dashboard. item = a track from get_dashboard."""

    def __init__(self, **properties):
        super().__init__(**properties)
        t = self.item
        self.dom_nodes["title"].textContent = "Examination open: " + t["title"]
        self.dom_nodes["text"].textContent = ("You've completed every module. Sit the final examination for your %s."
                                              % t["credential"])
        self.dom_nodes["a"].setAttribute("href", "#exam/" + t["id"])
