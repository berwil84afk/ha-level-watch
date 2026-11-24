"""Tests for a source sensor that reports a volume, e.g. a tank in litres."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.level_watch import calc
from custom_components.level_watch.const import DOMAIN

from .conftest import CONFIG, SOURCE

OIL = {
    **CONFIG,
    "name": "Heizöl",
    "kind": "tank",
    "reference_min": 0,
    "reference_max": 1500,
    "level_unit": "L",
    "tank": {"shape": "none"},
}


def _state(hass: HomeAssistant, key: str):
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"oel_{key}")
    assert entity_id, key
    return hass.states.get(entity_id)


async def _setup(hass: HomeAssistant, **options) -> MockConfigEntry:
    hass.config.language = "de"
    entry = MockConfigEntry(domain=DOMAIN, data=OIL, options=options, title="Heizöl", entry_id="oel")
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def test_volume_units() -> None:
    assert calc.to_liters(1.2, "m³") == pytest.approx(1200)
    assert calc.to_liters(10, "gal") == pytest.approx(37.854, abs=0.001)
    assert calc.level_unit("L") == "L"
    assert calc.level_unit("m³") == "L"
    assert calc.normalize_unit("l") == "L"
    assert calc.normalize_unit("m3") == "m³"
    assert calc.is_supported_unit("mL")


async def test_flow_detects_volume(hass: HomeAssistant, source) -> None:
    source("900", unit="L")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {
        "name": "Heizöl", "source_entity": SOURCE, "source_unit": "auto", "kind": "tank",
        "measurement_mode": "level", "offset": 0, "reference_min": 0, "reference_max": 1500,
        "tank": {"shape": "none"},
    })
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["level_unit"] == "L"


async def test_volume_sensors(hass: HomeAssistant, source, freezer: FrozenDateTimeFactory) -> None:
    source("0.9", unit="m3".replace("3", "³"))  # 900 L, reported in m³
    await _setup(hass, advanced={"smoothing": 0})
    level = _state(hass, "level")
    assert float(level.state) == 900
    assert level.attributes["unit_of_measurement"] == "L"
    assert level.attributes["device_class"] == "volume_storage"
    assert float(_state(hass, "percent").state) == 60
    assert _state(hass, "rate").attributes["unit_of_measurement"] == "L/h"

    value = 900.0
    for _ in range(48):
        freezer.tick(timedelta(hours=1))
        value -= 12 / 24  # 12 L per day
        source(f"{value / 1000:.4f}", unit="m³")
        await hass.async_block_till_done()
    consumption = _state(hass, "consumption")
    assert consumption.attributes["unit_of_measurement"] == "L/d"
    assert float(consumption.state) == pytest.approx(12, rel=0.02)
    assert float(_state(hass, "days_left").state) == pytest.approx(876 / 12, rel=0.02)


async def test_volume_rejects_weight(hass: HomeAssistant, source) -> None:
    source("900", unit="L")
    await _setup(hass)
    source("20", unit="kg")
    await hass.async_block_till_done()
    assert _state(hass, "data_quality").state == "unavailable"
