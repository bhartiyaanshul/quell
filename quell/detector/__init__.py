"""Detector — turn monitored events into :class:`Incident` records."""

from __future__ import annotations

from quell.detector.baseline import RollingBaseline
from quell.detector.detector import Detector
from quell.detector.signature import compute_signature

__all__ = ["Detector", "RollingBaseline", "compute_signature"]
