import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from metis.data.dukascopy import (
    CommandResult,
    DukascopyIncompleteDataError,
    DukascopyProvider,
)
from metis.data.provider import fetch_with_retries


def candle(stamp: datetime, *, close: float = 1.1) -> dict:
    return {"timestamp": int(stamp.timestamp() * 1000), "open": close,
            "high": close, "low": close, "close": close, "volume": 1.0}


def daily_stamps(start: datetime, minutes: int) -> list[datetime]:
    return [start + timedelta(minutes=offset) for offset in range(minutes)]


@pytest.mark.asyncio
async def test_fetches_both_sides_and_records_provenance(tmp_path):
    calls = []
    start = datetime(2024, 1, 1, tzinfo=UTC)
    expected = daily_stamps(start, 2)

    async def runner(args):
        calls.append(args)
        return CommandResult(
            payload=json.dumps([candle(stamp) for stamp in expected]),
            stderr="dukascopy-node:cli:version 1.51.1",
        )

    provider = DukascopyProvider(cache_directory=tmp_path, runner=runner, retries=0)
    rows = [row async for row in provider.fetch_range(
        "EUR/USD", "M1", start, start + timedelta(minutes=2))]

    assert [(row.price_side, row.timestamp) for row in rows] == [
        (side, stamp) for side in ("bid", "ask") for stamp in expected
    ]
    assert all(row.volume_type for row in rows)
    assert calls[0][:2] == ["npx", "dukascopy-node"]
    assert calls[0][calls[0].index("-t") + 1] == "m1"
    assert calls[0][calls[0].index("-p") + 1] == "bid"
    assert "--retry-on-empty" in calls[0]
    assert calls[0][calls[0].index("--retries") + 1] == "0"
    assert "--cache" not in calls[0]
    assert "-fl" in calls[0]

    metadata = rows[0].source_metadata
    assert metadata["cli_version"] == "1.51.1"
    assert metadata["instrument"] == "eurusd"
    assert metadata["timeframe"] == "M1"
    assert metadata["requested_start_utc"] == start.isoformat()
    assert metadata["requested_end_utc_exclusive"] == (start + timedelta(minutes=2)).isoformat()
    assert metadata["request_count"] == 1
    assert metadata["retry_count"] == 0
    assert metadata["downloaded_observation_count"] == 2
    assert metadata["expected_observation_count"] == 2
    assert metadata["missing_timestamps"] == []
    assert metadata["validation_status"] == "passed"
    artifact = metadata["raw_artifacts"][0]
    assert Path(artifact["raw_artifact_location"]).is_file()
    assert artifact["sha256"] == hashlib.sha256(
        Path(artifact["raw_artifact_location"]).read_bytes()).hexdigest()


@pytest.mark.asyncio
async def test_empty_response_retries_and_successful_retry_is_recorded(tmp_path):
    start = datetime(2024, 1, 1, tzinfo=UTC)
    expected = daily_stamps(start, 2)
    attempts = {"bid": 0, "ask": 0}

    async def runner(args):
        side = args[args.index("-p") + 1]
        attempts[side] += 1
        if attempts[side] == 1:
            return "[]"
        return json.dumps([candle(stamp) for stamp in expected])

    provider = DukascopyProvider(cache_directory=tmp_path, runner=runner, retries=1)
    rows = [row async for row in provider.fetch_range(
        "EURUSD", "M1", start, start + timedelta(minutes=2))]

    assert attempts == {"bid": 2, "ask": 2}
    assert len(rows) == 4
    provenance = rows[0].source_metadata
    assert provenance["request_count"] == 2
    assert provenance["retry_count"] == 1
    assert provenance["raw_artifacts"][0]["outcome"] == "incomplete"
    assert provenance["raw_artifacts"][1]["outcome"] == "complete"
    assert provenance["raw_artifacts"][1]["comparison_with_previous"]["added_timestamps"] == [
        stamp.isoformat() for stamp in expected
    ]
    assert all(Path(item["raw_artifact_location"]).exists()
               for item in provenance["raw_artifacts"])


@pytest.mark.asyncio
async def test_failed_command_retries_and_preserves_failure_log(tmp_path):
    start = datetime(2024, 1, 1, tzinfo=UTC)
    expected = daily_stamps(start, 1)
    attempts = {"bid": 0, "ask": 0}

    async def runner(args):
        side = args[args.index("-p") + 1]
        attempts[side] += 1
        if side == "bid" and attempts[side] == 1:
            return CommandResult(payload="", stderr="HTTP 503", returncode=1)
        return json.dumps([candle(stamp) for stamp in expected])

    provider = DukascopyProvider(cache_directory=tmp_path, runner=runner, retries=1)
    rows = [row async for row in provider.fetch_range(
        "EURUSD", "M1", start, start + timedelta(minutes=1))]

    assert attempts == {"bid": 2, "ask": 1}
    provenance = rows[0].source_metadata
    assert provenance["request_count"] == 2
    assert provenance["retry_count"] == 1
    failed_attempt = provenance["raw_artifacts"][0]
    assert failed_attempt["outcome"] == "failed"
    assert "HTTP 503" in Path(failed_attempt["log_location"]).read_text()
    assert len(failed_attempt["sha256"]) == 64


@pytest.mark.asyncio
async def test_partial_daily_response_retries_and_uses_complete_retry(tmp_path):
    start = datetime(2024, 1, 1, tzinfo=UTC)
    expected = daily_stamps(start, 3)
    calls = 0

    async def runner(_args):
        nonlocal calls
        calls += 1
        stamps = expected[:2] if calls == 1 else expected
        return json.dumps([candle(stamp) for stamp in stamps])

    provider = DukascopyProvider(cache_directory=tmp_path, runner=runner, retries=1)
    rows = [row async for row in provider.fetch_range(
        "EURUSD", "M1", start, start + timedelta(minutes=3))]

    assert len(rows) == 6
    assert calls == 3  # bid retries; ask succeeds on its first attempt
    provenance = rows[0].source_metadata
    assert provenance["downloaded_observation_count"] == 3
    assert provenance["expected_observation_count"] == 3
    assert provenance["raw_artifacts"][0]["validation"]["missing_timestamps"] == [
        expected[-1].isoformat()
    ]
    assert provenance["raw_artifacts"][1]["comparison_with_previous"]["added_timestamps"] == [
        expected[-1].isoformat()
    ]


@pytest.mark.asyncio
async def test_only_incomplete_daily_artifact_is_retried(tmp_path):
    start = datetime(2024, 1, 1, 23, 59, tzinfo=UTC)
    end = start + timedelta(minutes=2)
    expected = [start, start + timedelta(minutes=1)]
    attempts = {}

    async def runner(args):
        side = args[args.index("-p") + 1]
        day = args[args.index("-from") + 1][:10]
        key = (side, day)
        attempts[key] = attempts.get(key, 0) + 1
        if key == ("bid", "2024-01-02") and attempts[key] == 1:
            return "[]"
        stamps = [stamp for stamp in expected if stamp.date().isoformat() == day]
        return json.dumps([candle(stamp) for stamp in stamps])

    provider = DukascopyProvider(cache_directory=tmp_path, runner=runner, retries=1)
    rows = [row async for row in provider.fetch_range("EURUSD", "M1", start, end)]

    assert len(rows) == 4
    assert attempts == {
        ("bid", "2024-01-01"): 1,
        ("bid", "2024-01-02"): 2,
        ("ask", "2024-01-01"): 1,
        ("ask", "2024-01-02"): 1,
    }
    bid_metadata = rows[0].source_metadata
    assert bid_metadata["request_count"] == 3
    assert bid_metadata["retry_count"] == 1
    assert len(bid_metadata["raw_artifacts"]) == 3


@pytest.mark.asyncio
async def test_persistent_incompleteness_raises_before_yielding_any_observations(tmp_path):
    start = datetime(2024, 1, 1, tzinfo=UTC)
    expected = daily_stamps(start, 3)
    calls = 0

    async def runner(_args):
        nonlocal calls
        calls += 1
        return json.dumps([candle(stamp) for stamp in expected[:2]])

    provider = DukascopyProvider(cache_directory=tmp_path, runner=runner, retries=1)
    stream = provider.fetch_range("EURUSD", "M1", start, start + timedelta(minutes=3))
    with pytest.raises(DukascopyIncompleteDataError, match="remained incomplete") as exc:
        await anext(stream)

    assert calls == 2  # bid response and its retry; ask is never requested
    assert expected[-1].isoformat() in str(exc.value)
    artifacts = [path for path in tmp_path.glob("raw/*/cli-output/*.json")
                 if ".provenance." not in path.name]
    assert len(artifacts) == 2
    assert all(json.loads(path.read_text()) for path in artifacts)
    manifests = list(tmp_path.glob("raw/*/cli-output/*.provenance.json"))
    assert len(manifests) == 2
    final_manifest = json.loads(max(manifests, key=lambda path: path.name).read_text())
    assert final_manifest["final_validation_status"] == "incomplete"
    assert final_manifest["missing_timestamps"] == [expected[-1].isoformat()]


@pytest.mark.asyncio
async def test_exhausted_daily_gap_is_not_retried_by_shared_range_wrapper(tmp_path):
    start = datetime(2024, 1, 1, tzinfo=UTC)
    expected = daily_stamps(start, 2)
    calls = 0

    async def runner(_args):
        nonlocal calls
        calls += 1
        return json.dumps([candle(expected[0])])

    provider = DukascopyProvider(cache_directory=tmp_path, runner=runner, retries=0)
    with pytest.raises(DukascopyIncompleteDataError):
        _ = [row async for row in fetch_with_retries(
            provider, "EURUSD", "M1", start, start + timedelta(minutes=2), attempts=3)]

    assert calls == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("rows", "validation_key"),
    [
        ("duplicate", "duplicate_timestamps"),
        ("out_of_order", "out_of_order_pairs"),
    ],
)
async def test_duplicate_and_out_of_order_responses_are_retried(
    tmp_path, rows, validation_key
):
    start = datetime(2024, 1, 1, tzinfo=UTC)
    expected = daily_stamps(start, 2)
    calls = 0

    async def runner(_args):
        nonlocal calls
        calls += 1
        if rows == "duplicate":
            result = [candle(expected[0]), candle(expected[0]), candle(expected[1])]
        else:
            result = [candle(expected[1]), candle(expected[0])]
        return json.dumps(result)

    provider = DukascopyProvider(cache_directory=tmp_path, runner=runner, retries=1)
    stream = provider.fetch_range("EURUSD", "M1", start, start + timedelta(minutes=2))
    with pytest.raises(DukascopyIncompleteDataError) as exc:
        await anext(stream)
    assert calls == 2
    assert validation_key in str(exc.value)
    preserved = [path for path in tmp_path.glob("raw/*/cli-output/*.json")
                 if ".provenance." not in path.name]
    assert len(preserved) == 2
    assert all(json.loads(path.read_text()) for path in preserved)


def test_expected_forex_grid_respects_weekly_session_boundaries_and_dst():
    winter_start = datetime(2026, 11, 8, 21, 59, tzinfo=UTC)
    winter_end = datetime(2026, 11, 9, 0, 2, tzinfo=UTC)
    winter = DukascopyProvider.expected_timestamps(winter_start, winter_end, "M1")
    assert len(winter) == 122
    assert winter[0] == datetime(2026, 11, 8, 22, 0, tzinfo=UTC)
    assert winter[-1] == datetime(2026, 11, 9, 0, 1, tzinfo=UTC)

    summer_start = datetime(2026, 3, 29, 20, 59, tzinfo=UTC)
    summer_end = datetime(2026, 3, 29, 21, 3, tzinfo=UTC)
    summer = DukascopyProvider.expected_timestamps(summer_start, summer_end, "M1")
    assert summer == [
        datetime(2026, 3, 29, 21, 0, tzinfo=UTC),
        datetime(2026, 3, 29, 21, 1, tzinfo=UTC),
        datetime(2026, 3, 29, 21, 2, tzinfo=UTC),
    ]

    friday_close = DukascopyProvider.expected_timestamps(
        datetime(2026, 11, 13, 21, 58, tzinfo=UTC),
        datetime(2026, 11, 13, 22, 2, tzinfo=UTC), "M1")
    assert friday_close == [
        datetime(2026, 11, 13, 21, 58, tzinfo=UTC),
        datetime(2026, 11, 13, 21, 59, tzinfo=UTC),
    ]


@pytest.mark.asyncio
async def test_rejects_unsupported_instrument_and_timeframe(tmp_path):
    provider = DukascopyProvider(cache_directory=tmp_path, runner=lambda _: "[]")
    start = datetime(2024, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError):
        _ = [row async for row in provider.fetch_range("AUDUSD", "M1", start,
                                                       start + timedelta(days=1))]
    with pytest.raises(ValueError):
        _ = [row async for row in provider.fetch_range("EURUSD", "M5", start,
                                                       start + timedelta(days=1))]
