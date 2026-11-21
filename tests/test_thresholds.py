"""Tests for the pure threshold logic."""

from custom_components.level_watch.thresholds import (
    ABOVE,
    BELOW,
    Threshold,
    format_message,
    load_thresholds,
    next_threshold,
    stage,
)

FLOOD = Threshold(id="f", name="Stufe 1", value=500, direction=ABOVE, hysteresis=5)
FLOOD2 = Threshold(id="f2", name="Stufe 2", value=600, direction=ABOVE)
LOW = Threshold(id="l", name="Reserve", value=50, direction=BELOW, hysteresis=5)


def test_above_with_hysteresis() -> None:
    assert not FLOOD.is_active(499, False)
    assert FLOOD.is_active(500, False)
    # Stays active until the level is back below value - hysteresis.
    assert FLOOD.is_active(496, True)
    assert not FLOOD.is_active(495, True)


def test_below_with_hysteresis() -> None:
    assert LOW.is_active(50, False)
    assert not LOW.is_active(51, False)
    assert LOW.is_active(54, True)
    assert not LOW.is_active(55, True)


def test_load_sorts_and_defaults() -> None:
    items = load_thresholds(
        [
            {"id": "b", "name": "B", "value": 600, "direction": "above"},
            {"id": "a", "name": "A", "value": 20, "direction": "below"},
        ]
    )
    assert [t.id for t in items] == ["a", "b"]
    assert items[0].hex_color == "#1976d2"  # blue for falling
    assert items[1].hex_color == "#f57c00"  # orange for rising
    assert items[1].clear_message is True


def test_stage_prefers_most_severe() -> None:
    ths = [LOW, FLOOD, FLOOD2]
    assert stage(ths, {}) is None
    assert stage(ths, {"f": True}) is FLOOD
    assert stage(ths, {"f": True, "f2": True}) is FLOOD2
    assert stage(ths, {"l": True}) is LOW


def test_next_threshold() -> None:
    ths = [LOW, FLOOD, FLOOD2]
    assert next_threshold(ths, {}, 300, 10) is FLOOD
    assert next_threshold(ths, {"f": True}, 550, 10) is FLOOD2
    assert next_threshold(ths, {}, 300, -10) is LOW
    assert next_threshold(ths, {}, 300, 0) is None
    assert next_threshold(ths, {}, 700, 10) is None


def test_messages() -> None:
    text = format_message(
        "", language="de", name="Rhein", threshold=FLOOD, level=512.34,
        trend="rising", rate=4.0,
    )
    assert text == "Rhein: Stufe 1 erreicht. Pegel 512,3 cm, steigend (+4 cm/h)."
    text = format_message(
        "", language="en", name="Rhein", threshold=FLOOD, level=490,
        trend="falling", rate=-2.5, cleared=True,
    )
    assert text == "Rhein: Stufe 1 cleared. Level 490 cm, falling."
    custom = format_message(
        "{threshold} bei {level} cm ({value}) {unbekannt}", language="de",
        name="Rhein", threshold=FLOOD, level=501, trend=None, rate=None,
    )
    assert custom == "Stufe 1 bei 501 cm (500) {unbekannt}"
    broken = format_message(
        "Pegel {level", language="de", name="Rhein", threshold=FLOOD, level=501,
        trend=None, rate=None,
    )
    assert broken == "Pegel {level"
