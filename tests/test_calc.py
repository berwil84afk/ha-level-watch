"""Tests for the pure level maths."""

import pytest

from custom_components.level_watch import calc


def history_of(points, keep=86400 * 2, spacing=0):
    h = calc.LevelHistory(keep, spacing)
    for ts, value in points:
        h.add(ts, value)
    return h


def test_units() -> None:
    assert calc.to_cm(1.5, "m") == 150
    assert calc.to_cm(25, "mm") == 2.5
    assert calc.is_length_unit("cm")
    assert not calc.is_length_unit("%")
    assert not calc.is_length_unit(None)
    with pytest.raises(ValueError):
        calc.to_cm(1, "%")


def test_distance_mode() -> None:
    # Sensor 200 cm above tank bottom measures 50 cm down to the surface.
    assert calc.raw_to_level(50, distance_mode=True, sensor_height=200, offset=0) == 150
    assert calc.raw_to_level(50, distance_mode=False, sensor_height=None, offset=-5) == 45
    with pytest.raises(ValueError):
        calc.raw_to_level(50, distance_mode=True, sensor_height=None, offset=0)


def test_percent() -> None:
    assert calc.percent(50, 0, 200) == 25
    assert calc.percent(-10, 0, 200) == 0
    assert calc.percent(250, 0, 200) == 100
    assert calc.percent(50, 0, None) is None
    assert calc.percent(50, 100, 100) is None


def test_history_thins_fast_sensors() -> None:
    h = history_of(((t, t) for t in range(0, 61, 2)), spacing=10)
    ts = [s.ts for s in h.samples]
    # Roughly one sample per 10 s, and the newest reading is always kept.
    assert 6 <= len(ts) <= 10
    assert ts[-1] == 60
    assert h.last.value == 60


def test_history_prunes_and_ignores_out_of_order() -> None:
    h = history_of([(0, 1), (100, 2), (50, 9)], keep=60)
    assert [s.ts for s in h.samples] == [100]


def test_history_roundtrip() -> None:
    h = history_of([(0, 1.0), (60, 2.5)])
    h2 = calc.LevelHistory(86400)
    h2.load(h.dump(), now=60)
    assert h2.samples == h.samples


def test_smoothing_removes_spike() -> None:
    h = history_of([(0, 100), (60, 100), (120, 400), (180, 100), (240, 100)])
    assert calc.smoothed(h, 240, 300) == 100
    assert calc.smoothed(h, 240, 0) == 100
    assert calc.smoothed(calc.LevelHistory(10), 0, 300) is None


def test_rate_linear() -> None:
    # 2 cm per 10 minutes = 12 cm/h
    h = history_of((m * 60, 100 + m * 0.2) for m in range(0, 61, 5))
    assert calc.rate_per_hour(h, 3600, 3600) == pytest.approx(12)
    assert calc.trend(12, 1) == calc.RISING
    assert calc.trend(-12, 1) == calc.FALLING
    assert calc.trend(0.5, 1) == calc.STABLE
    assert calc.trend(None, 1) is None


def test_rate_needs_coverage() -> None:
    # Three readings within two minutes say nothing about the hourly trend.
    h = history_of([(3480, 100), (3540, 101), (3600, 102)])
    assert calc.rate_per_hour(h, 3600, 3600) is None
    assert calc.rate_per_hour(history_of([(0, 1), (3600, 2)]), 3600, 3600) is None


def test_period_stats() -> None:
    day = 86400
    h = history_of([(0, 100), (day / 2, 80), (day, 130)])
    stats = calc.period_stats(h, day, day)
    assert (stats.minimum, stats.maximum, stats.change) == (80, 130, 30)
    # Less than a day of data: no change yet, but min/max are known.
    short = calc.period_stats(history_of([(0, 100), (3600, 90)]), 3600, day)
    assert (short.minimum, short.maximum, short.change) == (90, 100, None)


def test_jump() -> None:
    assert calc.is_jump(100, 150, 20)
    assert not calc.is_jump(100, 110, 20)
    assert not calc.is_jump(100, 500, 0)
    assert not calc.is_jump(None, 500, 20)
