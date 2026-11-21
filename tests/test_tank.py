"""Tests for tank volume, consumption and range."""

from datetime import timedelta
import math

from freezegun.api import FrozenDateTimeFactory
import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.level_watch import tank
from custom_components.level_watch.calc import LevelHistory
from custom_components.level_watch.const import DOMAIN

from .conftest import CONFIG

VERTICAL = tank.TankShape(tank.VERTICAL, diameter=100)
HORIZONTAL = tank.TankShape(tank.HORIZONTAL, diameter=100, length=200)
BOX = tank.TankShape(tank.BOX, length=200, width=50)


def test_volumes() -> None:
    assert VERTICAL.volume(100) == pytest.approx(math.pi * 50**2 * 100 / 1000)
    assert BOX.volume(100) == pytest.approx(1000)
    full = math.pi * 50**2 * 200 / 1000
    assert HORIZONTAL.volume(100) == pytest.approx(full)
    assert HORIZONTAL.volume(50) == pytest.approx(full / 2)
    assert HORIZONTAL.volume(150) == pytest.approx(full)  # clamped to the shape
    assert HORIZONTAL.volume(-5) == 0
    # A horizontal cylinder holds less in its bottom quarter than a quarter.
    assert HORIZONTAL.volume(25) < full / 4


def test_missing_dimensions() -> None:
    assert tank.TankShape(tank.HORIZONTAL, diameter=100).missing() == ["length"]
    assert tank.TankShape(tank.BOX, length=1, width=1).defined
    assert not tank.TankShape(tank.NONE).defined


def test_percent_by_volume() -> None:
    # Half height of a horizontal cylinder is half the volume, a quarter is not.
    assert tank.volume_percent(HORIZONTAL, 50, 0, None) == pytest.approx(50)
    assert tank.volume_percent(HORIZONTAL, 25, 0, None) == pytest.approx(19.55, abs=0.01)
    assert tank.volume_percent(VERTICAL, 25, 0, 100) == pytest.approx(25)
    assert tank.volume_percent(VERTICAL, 25, 0, None) is None
    assert tank.capacity(HORIZONTAL, None) == pytest.approx(math.pi * 50**2 * 200 / 1000)


def test_consumption_and_range() -> None:
    long = LevelHistory(7 * 86400)
    # Box with 10 L per cm: 2 cm per day = 20 L/d.
    for hour in range(0, 49):
        long.add(hour * 3600, 100 - hour * 2 / 24)
    now = 48 * 3600
    used = tank.consumption_per_day(BOX, long, now, 7 * 86400, 12 * 3600)
    assert used == pytest.approx(20)
    assert tank.days_left(BOX, 96, 10, used) == pytest.approx(43)
    assert tank.days_left(BOX, 96, 10, 0) is None
    # Not enough time covered yet
    assert tank.consumption_per_day(BOX, long, now, 7 * 86400, 3 * 86400) is None


def test_refill_and_full() -> None:
    long = LevelHistory(86400)
    long.add(0, 50)
    long.add(3600, 49.5)
    assert not tank.is_refill(long, 3600, 52, 5)
    assert tank.is_refill(long, 3600, 80, 5)
    assert not tank.is_refill(long, 3600, 80, 0)
    assert tank.hours_to_full(80, 100, 10) == 2
    assert tank.hours_to_full(80, 100, -10) is None
    assert tank.hours_to_full(80, None, 10) is None


# -- integration ---------------------------------------------------------------

TANK = {
    **CONFIG,
    "name": "Heizöl",
    "kind": "tank",
    "reference_min": 5,
    "reference_max": 150,
    "tank": {"shape": "box", "length": 200, "width": 50},  # 10 L per cm
}


def _state(hass: HomeAssistant, key: str):
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"oel_{key}")
    assert entity_id, key
    return hass.states.get(entity_id)


async def _setup(hass: HomeAssistant, **options) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, data=TANK, options=options, title="Heizöl", entry_id="oel"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_tank_sensors(
    hass: HomeAssistant, source, freezer: FrozenDateTimeFactory
) -> None:
    source("100")
    await _setup(hass, advanced={"smoothing": 0})
    assert float(_state(hass, "volume").state) == 1000
    assert float(_state(hass, "free_volume").state) == 500
    assert _state(hass, "volume").attributes["capacity"] == 1500
    assert _state(hass, "consumption").state == "unknown"
    assert _state(hass, "level").attributes["volume"] == 1000

    # 2 days at 3 cm per day = 30 L/d
    level = 100.0
    for _ in range(48):
        freezer.tick(timedelta(hours=1))
        level -= 3 / 24
        source(f"{level:.3f}")
        await hass.async_block_till_done()
    assert float(_state(hass, "consumption").state) == pytest.approx(30, rel=0.01)
    # 94 cm left above the 5 cm bottom reference = 890 L / 30 L/d
    assert float(_state(hass, "days_left").state) == pytest.approx(890 / 30, rel=0.01)
    assert _state(hass, "last_refill").state == "unknown"

    # Delivery: consumption starts over, the refill is recorded.
    freezer.tick(timedelta(minutes=10))
    source("140")
    await hass.async_block_till_done()
    assert _state(hass, "last_refill").state != "unknown"
    assert _state(hass, "consumption").state == "unknown"
    assert float(_state(hass, "volume").state) == 1400


async def test_tank_without_shape(hass: HomeAssistant, source) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={**TANK, "tank": {"shape": "none"}},
        title="Zisterne",
        entry_id="oel",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    assert registry.async_get_entity_id("sensor", DOMAIN, "oel_volume") is None
    assert registry.async_get_entity_id("sensor", DOMAIN, "oel_time_to_full")
    assert registry.async_get_entity_id("sensor", DOMAIN, "oel_last_refill")


async def test_water_has_no_tank_sensors(hass: HomeAssistant, source) -> None:
    await _setup_water(hass)
    registry = er.async_get(hass)
    for key in ("volume", "time_to_full", "last_refill", "consumption"):
        assert registry.async_get_entity_id("sensor", DOMAIN, f"oel_{key}") is None


async def _setup_water(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={**TANK, "kind": "water"},
        title="Teich",
        entry_id="oel",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_flow_needs_tank_dimensions(hass: HomeAssistant, source) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    data = {
        "name": "Öltank", "source_entity": "sensor.pegel", "source_unit": "auto",
        "kind": "tank", "measurement_mode": "level", "offset": 0, "reference_min": 0,
        "tank": {"shape": "horizontal_cylinder", "diameter": 120},
    }
    result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    assert result["errors"] == {"base": "tank_horizontal_cylinder"}
    data["tank"]["length"] = 250
    result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    assert result["type"] == "create_entry"
    assert result["data"]["tank"]["length"] == 250
