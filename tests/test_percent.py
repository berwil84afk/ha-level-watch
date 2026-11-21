"""Tests for a source sensor that reports the fill level in %."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.level_watch.const import DOMAIN

from .conftest import CONFIG, SOURCE

PERCENT_TANK = {
    **CONFIG,
    "name": "Öltank",
    "kind": "tank",
    "reference_min": 0,
    "reference_max": None,
    "level_unit": "%",
    "tank": {"shape": "box", "length": 100, "width": 100},  # ignored for %
}


def _state(hass: HomeAssistant, key: str):
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"oel_{key}")
    assert entity_id, key
    return hass.states.get(entity_id)


async def _setup(hass: HomeAssistant, **options) -> MockConfigEntry:
    hass.config.language = "de"
    entry = MockConfigEntry(
        domain=DOMAIN, data=PERCENT_TANK, options=options, title="Öltank", entry_id="oel"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_flow_detects_percent(hass: HomeAssistant, source) -> None:
    source("55", unit="%")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    data = {
        "name": "Öltank", "source_entity": SOURCE, "source_unit": "auto", "kind": "tank",
        "measurement_mode": "distance", "sensor_height": 100, "offset": 0,
        "reference_min": 0, "tank": {"shape": "none"},
    }
    result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    assert result["errors"] == {"measurement_mode": "percent_distance"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**data, "measurement_mode": "level"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["level_unit"] == "%"


async def test_percent_chosen_by_hand(hass: HomeAssistant, source) -> None:
    source("55", unit=None)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Öltank", "source_entity": SOURCE, "source_unit": "percent", "kind": "tank",
         "measurement_mode": "level", "offset": 0, "reference_min": 0,
         "tank": {"shape": "none"}},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["level_unit"] == "%"
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    level_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_level")
    assert float(hass.states.get(level_id).state) == 55


async def test_length_source_keeps_cm(hass: HomeAssistant, source) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Rhein", "source_entity": SOURCE, "source_unit": "auto", "kind": "water",
         "measurement_mode": "level", "offset": 0, "reference_min": 0,
         "tank": {"shape": "none"}},
    )
    assert result["data"]["level_unit"] == "cm"


async def test_percent_sensors(
    hass: HomeAssistant, source, freezer: FrozenDateTimeFactory
) -> None:
    source("60", unit="%")
    await _setup(hass, advanced={"smoothing": 0})
    level = _state(hass, "level")
    assert float(level.state) == 60
    assert level.attributes["unit_of_measurement"] == "%"
    assert "device_class" not in level.attributes
    assert level.attributes["unit"] == "%"
    assert level.attributes["top"] == 100  # top reference defaults to 100 %
    assert _state(hass, "rate").attributes["unit_of_measurement"] == "%/h"
    registry = er.async_get(hass)
    for key in ("percent", "volume", "free_volume"):
        assert registry.async_get_entity_id("sensor", DOMAIN, f"oel_{key}") is None

    # Two days at 2 % per day
    value = 60.0
    for _ in range(48):
        freezer.tick(timedelta(hours=1))
        value -= 2 / 24
        source(f"{value:.3f}", unit="%")
        await hass.async_block_till_done()
    consumption = _state(hass, "consumption")
    assert consumption.attributes["unit_of_measurement"] == "%/d"
    assert float(consumption.state) == pytest.approx(2, rel=0.01)
    assert float(_state(hass, "days_left").state) == pytest.approx(56 / 2, rel=0.01)


async def test_percent_rejects_length_reading(hass: HomeAssistant, source) -> None:
    source("60", unit="%")
    await _setup(hass)
    source("80", unit="cm")
    await hass.async_block_till_done()
    assert _state(hass, "data_quality").state == "unavailable"


async def test_percent_message(hass: HomeAssistant, source) -> None:
    phone = async_mock_service(hass, "notify", "mobile_app_pixel")
    source("30", unit="%")
    await _setup(
        hass,
        advanced={"smoothing": 0},
        thresholds=[{
            "id": "res", "name": "Reserve", "value": 20, "direction": "below",
            "notify": True, "targets": ["service:mobile_app_pixel"],
        }],
    )
    source("19", unit="%")
    await hass.async_block_till_done()
    assert len(phone) == 1
    assert phone[0].data["message"].startswith("Öltank: Reserve erreicht. Pegel 19 %")
