from anvil import *

from ._anvil_designer import WeekDayTemplate
from ... import cs


class WeekDay(WeekDayTemplate):
    """One day of the dashboard's week strip. item = {day (YYYY-MM-DD), active}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        d = self.dom_nodes["d"]
        d.textContent = cs.weekday(self.item["day"])
        d.className = "wd on" if self.item.get("active") else "wd"
        d.setAttribute("title", cs.date(self.item["day"], "long") + (": studied" if self.item.get("active") else ""))
