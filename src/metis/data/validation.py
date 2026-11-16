"""Quality checks that preserve every received observation."""

from dataclasses import dataclass, field
from datetime import timedelta

from metis.data.calendar import FXSessionCalendar, SessionCalendar
from metis.data.schemas import OHLCObservation


@dataclass
class QualityReport:
    accepted: list[OHLCObservation] = field(default_factory=list)
    suspicious: list[tuple[OHLCObservation, str]] = field(default_factory=list)
    invalid: list[tuple[dict, str]] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    out_of_order: list[str] = field(default_factory=list)
    closures: list[str] = field(default_factory=list)
    coverage_sufficient: bool = True


def validate_observations(records: list[OHLCObservation], *, movement_limit: float = 0.1,
                          minimum_observations: int = 1, calendar: SessionCalendar | None = None) -> QualityReport:
    report = QualityReport()
    session_calendar = calendar or FXSessionCalendar()
    seen: set[tuple[str, str, object]] = set()
    prior: dict[tuple[str, str], OHLCObservation] = {}
    intervals = {"M15": timedelta(minutes=15), "H1": timedelta(hours=1)}
    for record in records:
        key = (record.symbol, record.timeframe, record.timestamp)
        if key in seen:
            report.duplicates.append(f"{record.symbol} {record.timeframe} {record.timestamp.isoformat()}")
            continue
        seen.add(key)
        group = (record.symbol, record.timeframe)
        previous = prior.get(group)
        if previous and record.timestamp < previous.timestamp:
            report.out_of_order.append(f"{record.symbol} {record.timestamp.isoformat()}")
        reason = None
        if previous and record.timestamp > previous.timestamp:
            gap = record.timestamp - previous.timestamp
            if gap > intervals[record.timeframe]:
                # FX is conventionally closed from Friday 22:00 UTC through Sunday 22:00 UTC.
                cursor = previous.timestamp + intervals[record.timeframe]
                while cursor < record.timestamp:
                    if session_calendar.is_open(cursor):
                        report.missing.append(f"{cursor.isoformat()}")
                    else:
                        report.closures.append(f"{cursor.isoformat()}")
                    cursor += intervals[record.timeframe]
            if abs(record.open / previous.close - 1) > movement_limit:
                reason = "suspicious price movement"
        if reason:
            report.suspicious.append((record, reason))
        else:
            report.accepted.append(record)
        if previous is None or record.timestamp >= previous.timestamp:
            prior[group] = record
    report.coverage_sufficient = len(report.accepted) >= minimum_observations
    return report
