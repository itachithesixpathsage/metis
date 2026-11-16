"""Configurable FX session calendar for expected-bar classification."""

from datetime import datetime, time, timezone
from typing import Protocol


class SessionCalendar(Protocol):
    def is_open(self, timestamp: datetime) -> bool: ...


class FXSessionCalendar:
    """Weekly FX session with explicit UTC open/close, holidays and overrides.

    Defaults model Sunday 22:00 UTC through Friday 22:00 UTC. Supply known
    holiday dates or an adapter-specific calendar for venue-specific schedules.
    """

    def __init__(self, *, open_weekday: int = 6, open_time: time = time(22),
                 close_weekday: int = 4, close_time: time = time(22),
                 holidays: set = frozenset()):
        self.open_weekday = open_weekday
        self.open_time = open_time
        self.close_weekday = close_weekday
        self.close_time = close_time
        self.holidays = frozenset(holidays)

    def is_open(self, timestamp: datetime) -> bool:
        value = timestamp.astimezone(timezone.utc)
        if value.date() in self.holidays:
            return False
        weekday, clock = value.weekday(), value.time().replace(tzinfo=None)
        if weekday == 5:
            return False
        if self.close_weekday < self.open_weekday:
            if weekday > self.close_weekday and weekday < self.open_weekday:
                return False
            if weekday == self.close_weekday:
                return clock < self.close_time
            if weekday == self.open_weekday:
                return clock >= self.open_time
            return True
        # Sessions spanning year-end/week boundaries with close day after open day.
        return not (weekday > self.close_weekday or weekday < self.open_weekday)
