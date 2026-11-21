"""Pure level calculations: history, smoothing, trend and statistics.

Nothing in here imports Home Assistant, so the maths can be tested on its own.
All levels are in cm, all timestamps are POSIX seconds.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import median
from typing import Iterable

RISING = "rising"
FALLING = "falling"
STABLE = "stable"

# The trend needs samples covering at least this share of its window, so a
# couple of readings right after a restart do not produce a wild rate.
MIN_WINDOW_COVERAGE = 0.25
MIN_TREND_SAMPLES = 3

_TO_CM = {"mm": 0.1, "cm": 1.0, "m": 100.0, "in": 2.54, "ft": 30.48}


def to_cm(value: float, unit: str) -> float:
    """Convert a length to cm; raise ValueError for unknown units."""
    try:
        return value * _TO_CM[unit]
    except KeyError as err:
        raise ValueError(f"unsupported unit {unit!r}") from err


def is_length_unit(unit: str | None) -> bool:
    return unit in _TO_CM


def raw_to_level(
    reading_cm: float, *, distance_mode: bool, sensor_height: float | None, offset: float
) -> float:
    """Turn a sensor reading into a level above the reference zero.

    In distance mode the sensor measures from above down to the surface, so the
    level is the mounting height minus that distance.
    """
    if distance_mode:
        if sensor_height is None:
            raise ValueError("distance mode needs a sensor height")
        reading_cm = sensor_height - reading_cm
    return reading_cm + offset


def percent(level: float, ref_min: float, ref_max: float | None) -> float | None:
    """Level as a share of the reference range, clamped to 0-100."""
    if ref_max is None or ref_max <= ref_min:
        return None
    return max(0.0, min(100.0, (level - ref_min) / (ref_max - ref_min) * 100.0))


@dataclass(frozen=True, slots=True)
class Sample:
    ts: float
    value: float


class LevelHistory:
    """Time-ordered level samples for a sliding period."""

    def __init__(self, keep_seconds: float, min_spacing: float = 0.0) -> None:
        self.keep_seconds = keep_seconds
        self.min_spacing = min_spacing
        self._samples: deque[Sample] = deque()

    def __len__(self) -> int:
        return len(self._samples)

    @property
    def samples(self) -> list[Sample]:
        return list(self._samples)

    @property
    def last(self) -> Sample | None:
        return self._samples[-1] if self._samples else None

    def add(self, ts: float, value: float) -> None:
        """Add a sample, thinning fast sensors to about one per min_spacing.

        The newest sample stays open: while it is closer than min_spacing to the
        one before it, a new reading replaces it instead of being appended. That
        keeps the latest value current without storing every reading.
        """
        if self._samples and ts < self._samples[-1].ts:
            return  # out of order, ignore
        if len(self._samples) >= 2 and ts - self._samples[-2].ts < self.min_spacing:
            self._samples[-1] = Sample(ts, value)
        else:
            self._samples.append(Sample(ts, value))
        self.prune(ts)

    def prune(self, now: float) -> None:
        limit = now - self.keep_seconds
        while self._samples and self._samples[0].ts < limit:
            self._samples.popleft()

    def since(self, ts: float) -> list[Sample]:
        return [s for s in self._samples if s.ts >= ts]

    def value_at_or_before(self, ts: float) -> Sample | None:
        found = None
        for sample in self._samples:
            if sample.ts > ts:
                break
            found = sample
        return found

    def dump(self) -> list[list[float]]:
        return [[round(s.ts, 1), round(s.value, 3)] for s in self._samples]

    def load(self, data: Iterable[Iterable[float]], now: float) -> None:
        self._samples.clear()
        for ts, value in sorted((float(t), float(v)) for t, v in data):
            self._samples.append(Sample(ts, value))
        self.prune(now)


def smoothed(history: LevelHistory, now: float, window_seconds: float) -> float | None:
    """Median of the samples in the window; the last value if it is empty."""
    last = history.last
    if last is None:
        return None
    if window_seconds <= 0:
        return last.value
    values = [s.value for s in history.since(now - window_seconds)]
    return median(values) if values else last.value


def rate_per_hour(
    history: LevelHistory, now: float, window_seconds: float
) -> float | None:
    """Least-squares slope over the window in cm/h, or None without enough data."""
    if window_seconds <= 0:
        return None
    samples = history.since(now - window_seconds)
    if len(samples) < MIN_TREND_SAMPLES:
        return None
    span = samples[-1].ts - samples[0].ts
    if span < window_seconds * MIN_WINDOW_COVERAGE:
        return None
    t0 = samples[0].ts
    xs = [s.ts - t0 for s in samples]
    ys = [s.value for s in samples]
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0:
        return None
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    return sxy / sxx * 3600.0


def trend(rate: float | None, deadband: float) -> str | None:
    if rate is None:
        return None
    if rate > deadband:
        return RISING
    if rate < -deadband:
        return FALLING
    return STABLE


@dataclass(frozen=True, slots=True)
class Stats:
    minimum: float | None
    maximum: float | None
    change: float | None


def period_stats(history: LevelHistory, now: float, period_seconds: float) -> Stats:
    """Min, max and change over the period (change only with a full period)."""
    samples = history.since(now - period_seconds)
    if not samples:
        return Stats(None, None, None)
    values = [s.value for s in samples]
    change = None
    oldest = history.samples[0] if len(history) else None
    if oldest is not None and now - oldest.ts >= period_seconds * 0.95:
        start = history.value_at_or_before(now - period_seconds) or samples[0]
        change = samples[-1].value - start.value
    return Stats(min(values), max(values), change)


def is_jump(previous: float | None, value: float, max_jump: float) -> bool:
    """True if the value jumps further than allowed (0 disables the check)."""
    return max_jump > 0 and previous is not None and abs(value - previous) > max_jump
