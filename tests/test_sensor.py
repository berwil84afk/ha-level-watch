"""Tests for the Level Watch sensors."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.level_watch.const import DOMAIN

from .conftest import CONFIG


async def _setup(hass: HomeAssistant, **overrides) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, data={**CONFIG, **overrides}, title="Rhein", entry_id="rhein"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _state(hass: HomeAssistant, key: str):
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"rhein_{key}")
    assert entity_id, key
    return hass.states.get(entity_id)


async def test_initial_values(hass: HomeAssistant, source) -> None:
    await _setup(hass)
    level = _state(hass, "level")
    assert float(level.state) == 400
    assert level.attributes["unit_of_measurement"] == "cm"
    assert float(_state(hass, "percent").state) == 50
    assert _state(hass, "data_quality").state == "ok"
    # One reading is not enough for a trend.
    assert _state(hass, "trend").state == "unknown"
    assert _state(hass, "rate").state == "unknown"


async def test_no_percent_without_top_reference(hass: HomeAssistant, source) -> None:
    await _setup(hass, reference_max=None)
    assert (
        er.async_get(hass).async_get_entity_id("sensor", DOMAIN, "rhein_percent") is None
    )


async def test_distance_mode_and_unit(hass: HomeAssistant, source) -> None:
    source("0.5", unit="m")
    await _setup(hass, measurement_mode="distance", sensor_height=200, offset=10)
    assert float(_state(hass, "level").state) == 160


async def test_rising_trend(
    hass: HomeAssistant, source, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass, **{"advanced": {"smoothing": 0}})
    level = 400.0
    for _ in range(12):  # one hour, 5 cm every 5 minutes = 60 cm/h
        freezer.tick(timedelta(minutes=5))
        level += 5
        source(str(level))
        await hass.async_block_till_done()
    assert float(_state(hass, "rate").state) == pytest.approx(60, rel=0.01)
    assert _state(hass, "trend").state == "rising"
    assert float(_state(hass, "max_24h").state) == 460
    assert float(_state(hass, "min_24h").state) == 400


async def test_steady_value_is_carried_forward(
    hass: HomeAssistant, source, freezer: FrozenDateTimeFactory
) -> None:
    """A sensor that only reports changes still ends up stable, not rising."""
    await _setup(hass, **{"advanced": {"smoothing": 0}})
    for _ in range(6):
        freezer.tick(timedelta(minutes=5))
        source(str(400 + 10))
        await hass.async_block_till_done()
    # Now the level holds still for an hour without new state changes.
    for _ in range(60):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
    assert _state(hass, "trend").state == "stable"


async def test_stale_and_unavailable(
    hass: HomeAssistant, source, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass)
    freezer.tick(timedelta(minutes=61))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert _state(hass, "data_quality").state == "stale"
    # The last level stays visible.
    assert float(_state(hass, "level").state) == 400

    source("unavailable", unit=None)
    await hass.async_block_till_done()
    assert _state(hass, "data_quality").state == "unavailable"

    source("410")
    await hass.async_block_till_done()
    assert _state(hass, "data_quality").state == "ok"


async def test_jump_needs_confirmation(hass: HomeAssistant, source) -> None:
    await _setup(hass, **{"advanced": {"smoothing": 0, "max_jump": 20}})
    source("900")  # a single echo
    await hass.async_block_till_done()
    assert float(_state(hass, "level").state) == 400
    source("405")
    await hass.async_block_till_done()
    assert float(_state(hass, "level").state) == 405

    # A refill: three consistent readings are accepted.
    for value in ("700", "701", "702"):
        source(value)
        await hass.async_block_till_done()
    assert float(_state(hass, "level").state) == 702


async def test_history_survives_reload(
    hass: HomeAssistant, source, freezer: FrozenDateTimeFactory
) -> None:
    entry = await _setup(hass, **{"advanced": {"smoothing": 0}})
    for value in ("350", "300"):
        freezer.tick(timedelta(minutes=5))
        source(value)
        await hass.async_block_till_done()
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert float(_state(hass, "max_24h").state) == 400
    assert float(_state(hass, "min_24h").state) == 300
