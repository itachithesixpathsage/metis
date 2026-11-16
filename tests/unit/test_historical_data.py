from datetime import datetime, timedelta, timezone

from pydantic import ValidationError
import pytest

from metis.data.schemas import OHLCObservation
from metis.data.validation import validate_observations


def bar(at, open_=1.1, side="unspecified", timeframe="M15"):
    return OHLCObservation(symbol="eur/usd", timestamp=at, timeframe=timeframe, price_side=side, open=open_,
                           high=open_ + .001, low=open_ - .001, close=open_, source="test")


def test_normalizes_symbol_timestamp_and_checks_duplicates_and_gaps():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    result = validate_observations([bar(start), bar(start), bar(start + timedelta(minutes=30))])
    assert result.accepted[0].symbol == "EURUSD"
    assert len(result.duplicates) == 1
    assert len(result.missing) == 1


def test_flags_suspicious_move_without_silently_accepting():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    result = validate_observations([bar(start), bar(start + timedelta(minutes=15), 1.3)])
    assert len(result.suspicious) == 1
    assert len(result.accepted) == 1


def test_rejects_naive_timestamps_and_invalid_prices():
    with pytest.raises(ValidationError):
        bar(datetime(2024, 1, 1), -1)


def test_weekend_gap_is_classified_as_closure():
    friday = datetime(2024, 1, 5, 21, 45, tzinfo=timezone.utc)
    sunday_before_open = datetime(2024, 1, 7, 21, 45, tzinfo=timezone.utc)
    result = validate_observations([bar(friday), bar(sunday_before_open)])
    assert result.closures
    assert not result.missing


def test_out_of_order_observations_are_reported():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    result = validate_observations([bar(start + timedelta(minutes=15)), bar(start)])
    assert len(result.out_of_order) == 1


def test_bid_and_ask_at_same_timestamp_are_distinct_bars():
    at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    result = validate_observations([bar(at, side="bid"), bar(at, side="ask")])
    assert len(result.accepted) == 2
    assert not result.duplicates


def test_m1_timeframe_is_supported_and_has_one_minute_gap_interval():
    at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    result = validate_observations([
        bar(at, timeframe="M1"), bar(at + timedelta(minutes=2), timeframe="M1"),
    ])
    assert len(result.missing) == 1


def test_duplicates_are_scoped_to_price_side():
    at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    result = validate_observations([bar(at, side="bid"), bar(at, side="bid")])
    assert len(result.duplicates) == 1
