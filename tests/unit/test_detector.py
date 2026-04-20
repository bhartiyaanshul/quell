"""Tests for quell.detector — signature, baseline, and Detector."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quell.detector import Detector, RollingBaseline, compute_signature
from quell.memory.db import create_tables, get_engine, get_session_factory
from quell.monitors.base import RawEvent

# ---------------------------------------------------------------------------
# compute_signature
# ---------------------------------------------------------------------------


def _event(text: str, severity: str = "error") -> RawEvent:
    return RawEvent(
        source="test",
        timestamp=datetime.now(UTC),
        raw=text,
        severity=severity,
    )


def test_signature_is_16_char_hex() -> None:
    sig = compute_signature(_event("TypeError: something broke"))
    assert len(sig) == 16
    assert all(c in "0123456789abcdef" for c in sig)


def test_signature_stable_across_repeats() -> None:
    a = compute_signature(_event("TypeError: oops"))
    b = compute_signature(_event("TypeError: oops"))
    assert a == b


def test_signature_ignores_memory_addresses() -> None:
    a = compute_signature(_event("Segfault at 0x7ffe12345678"))
    b = compute_signature(_event("Segfault at 0xdeadbeef"))
    assert a == b


def test_signature_ignores_uuids() -> None:
    a = compute_signature(_event("request 550e8400-e29b-41d4-a716-446655440000 failed"))
    b = compute_signature(_event("request 123e4567-e89b-12d3-a456-426614174000 failed"))
    assert a == b


def test_signature_ignores_timestamps() -> None:
    a = compute_signature(_event("2026-01-01T12:00:00Z Oops"))
    b = compute_signature(_event("2025-12-31T03:14:15Z Oops"))
    assert a == b


def test_signature_distinguishes_different_errors() -> None:
    a = compute_signature(_event("TypeError: foo"))
    b = compute_signature(_event("KeyError: bar"))
    assert a != b


def test_signature_ignores_whitespace_variation() -> None:
    a = compute_signature(_event("Oops   many   spaces"))
    b = compute_signature(_event("Oops many spaces"))
    assert a == b


# ---------------------------------------------------------------------------
# RollingBaseline
# ---------------------------------------------------------------------------


def test_baseline_record_increments_count() -> None:
    rb = RollingBaseline()
    rb.record(datetime.now(UTC))
    rb.record(datetime.now(UTC))
    assert rb.occurrence_count == 2


def test_baseline_prunes_old_events() -> None:
    rb = RollingBaseline(window=timedelta(minutes=10))
    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    rb.record(base - timedelta(hours=1))
    rb.record(base)
    # Older event should have been pruned.
    assert len(rb.timestamps) == 1


def test_baseline_rates_zero_when_empty() -> None:
    rb = RollingBaseline()
    assert rb.current_rate == 0.0
    assert rb.mean_rate == 0.0


def test_baseline_current_rate_counts_last_bucket() -> None:
    rb = RollingBaseline(bucket_minutes=5)
    t = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    rb.record(t - timedelta(minutes=10))  # outside the 5-min bucket
    rb.record(t - timedelta(minutes=2))  # inside
    rb.record(t)  # inside
    assert rb.current_rate == 2.0


# ---------------------------------------------------------------------------
# Detector — in-memory mode
# ---------------------------------------------------------------------------


async def test_detector_emits_for_new_signature() -> None:
    det = Detector()
    incident = await det.process(_event("TypeError: first time"))
    assert incident is not None
    assert incident.severity == "high"  # "error" -> "high"


async def test_detector_returns_none_for_low_severity_repeats() -> None:
    det = Detector()
    # First event is always new → emits.
    first = await det.process(_event("noisy info", severity="info"))
    assert first is not None
    # Second event with same signature, info severity, no spike → suppressed.
    second = await det.process(_event("noisy info", severity="info"))
    assert second is None


async def test_detector_dedupes_known_signature_in_memory() -> None:
    # First occurrence is always new and fires. Subsequent occurrences of
    # the same signature return None — even for high severity — because
    # the detector remembers it is already being investigated.
    det = Detector()
    first = await det.process(_event("TypeError: repeated"))
    assert first is not None
    second = await det.process(_event("TypeError: repeated"))
    assert second is None


async def test_detector_spike_detection() -> None:
    det = Detector(spike_multiplier=3.0)
    signature_text = "benign recurring noise"
    # Record enough historical events at info severity to build a baseline.
    for _ in range(10):
        await det.process(_event(signature_text, severity="info"))
    # The 11th event should not emit (no spike yet, info severity).
    assert await det.process(_event(signature_text, severity="info")) is None


# ---------------------------------------------------------------------------
# Detector — with a real (temp) database
# ---------------------------------------------------------------------------


@pytest.fixture
async def session_factory(tmp_path):  # type: ignore[no-untyped-def]
    db = tmp_path / "test.db"
    engine = get_engine(db)
    await create_tables(engine)
    factory = get_session_factory(engine)
    yield factory
    await engine.dispose()


async def test_detector_persists_incident(session_factory) -> None:  # type: ignore[no-untyped-def]
    det = Detector(session_factory=session_factory)
    incident = await det.process(_event("TypeError: persistable"))
    assert incident is not None
    assert incident.id.startswith("inc_")
    assert incident.signature == compute_signature(_event("TypeError: persistable"))


async def test_detector_dedupes_second_occurrence(session_factory) -> None:  # type: ignore[no-untyped-def]
    det = Detector(session_factory=session_factory)
    first = await det.process(_event("TypeError: dup"))
    assert first is not None
    # Second occurrence of the same signature → None (bumped in place).
    second = await det.process(_event("TypeError: dup"))
    assert second is None
