"""Rolling baseline — per-signature event-rate statistics over a 24h window.

The :class:`RollingBaseline` keeps a deque of event timestamps per
signature and computes a simple rate (events per minute) plus a
historical mean so the detector can decide whether the current burst is
a spike.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass
class RollingBaseline:
    """Event-rate statistics for one signature within a rolling window.

    Attributes:
        window:           Time window over which rate is computed (default 24h).
        bucket_minutes:   Width of each historical bucket used for the mean
                          rate calculation (default 60 minutes).
        timestamps:       Event timestamps in chronological order.
        occurrence_count: Lifetime occurrences seen.
    """

    window: timedelta = timedelta(hours=24)
    bucket_minutes: int = 60
    timestamps: deque[datetime] = field(default_factory=deque)
    occurrence_count: int = 0

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record(self, when: datetime) -> None:
        """Record an event at *when* and prune timestamps outside the window."""
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        self.timestamps.append(when)
        self.occurrence_count += 1
        cutoff = when - self.window
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()

    # ------------------------------------------------------------------
    # Derived metrics
    # ------------------------------------------------------------------

    @property
    def current_rate(self) -> float:
        """Events observed in the last ``bucket_minutes`` minutes.

        This is an absolute count in the most-recent bucket — not a per
        minute rate — which makes comparisons against :attr:`mean_rate`
        consistent.
        """
        if not self.timestamps:
            return 0.0
        cutoff = self.timestamps[-1] - timedelta(minutes=self.bucket_minutes)
        return float(sum(1 for ts in self.timestamps if ts >= cutoff))

    @property
    def mean_rate(self) -> float:
        """Mean events per bucket over the retained window.

        Computed as ``total_events / n_buckets`` where ``n_buckets`` is
        ``max(1, window_minutes // bucket_minutes)``.  Uses a floor of 1
        so a newly-seen signature never looks like an "infinite spike".
        """
        if not self.timestamps:
            return 0.0
        window_minutes = int(self.window.total_seconds() // 60) or 1
        n_buckets = max(1, window_minutes // self.bucket_minutes)
        return len(self.timestamps) / n_buckets


__all__ = ["RollingBaseline"]
