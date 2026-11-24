"""Tests for a source sensor that reports a weight, e.g. softener salt."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.level_watch import calc
from custom_components.level_watch.const import DOMAIN

from .conftest import CONFIG, SOURCE

SALT = {
    **CONFIG,
    "name": "Salzvorrat",
    "kind": "tank",
    "reference_min": 0,
    "reference_max": 50,
    "level_unit": "kg",
    "tank": {"shape": "none"},
}


def _state(hass: HomeAssistant, key: str):
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"salz_{key}")
    assert entity_id, key
    return hass.states.get(entity_id)


async def _setup(hass: HomeAssistant, **options) -> MockConfigEntry:
    hass.config.language = "de"
    entry = MockConfigEntry(
        domain=DOMAIN, data=SALT, options=options, title="Salzvorrat", entry_id="salz"
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def test_mass_units() -> None:
    assert calc.to_kg(2500, "g") == 2.5
    assert calc.to_kg(10, "lb") == pytest.approx(4.536, abs=0.001)
    assert calc.level_unit("g") == "kg"
    assert calc.level_unit("%") == "%"
    assert calc.level_unit("m") == "cm"
    assert calc.is_supported_unit("kg")
    assert not calc.is_supported_unit("W")


async def test_flow_detects_weight(hass: HomeAssistant, source) -> None:
    source("31.5", unit="kg")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    data = {
        "name": "Salzvorrat", "source_entity": SOURCE, "source_unit": "auto", "kind": "tank",
        "measurement_mode": "distance", "sensor_height": 100, "offset": 0,
        "reference_min": 0, "reference_max": 50, "tank": {"shape": "none"},
    }
    result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    assert result["errors"] == {"measurement_mode": "distance_needs_length"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**data, "measurement_mode": "level"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["level_unit"] == "kg"


async def test_weight_sensors(
    hass: HomeAssistant, source, freezer: FrozenDateTimeFactory
) -> None:
    source("30000", unit="g")  # 30 kg, reported in grams
    await _setup(hass, advanced={"smoothing": 0})
    level = _state(hass, "level")
    assert float(level.state) == 30
    assert level.attributes["unit_of_measurement"] == "kg"
    assert level.attributes["device_class"] == "weight"
    assert level.attributes["unit"] == "kg"
    assert float(_state(hass, "percent").state) == 60  # 30 of 50 kg
    assert _state(hass, "rate").attributes["unit_of_measurement"] == "kg/h"
    registry = er.async_get(hass)
    for key in ("volume", "free_volume"):
        assert registry.async_get_entity_id("sensor", DOMAIN, f"salz_{key}") is None

    # Two days at 1.5 kg per day
    value = 30.0
    for _ in range(48):
        freezer.tick(timedelta(hours=1))
        value -= 1.5 / 24
        source(f"{value * 1000:.0f}", unit="g")
        await hass.async_block_till_done()
    consumption = _state(hass, "consumption")
    assert consumption.attributes["unit_of_measurement"] == "kg/d"
    assert float(consumption.state) == pytest.approx(1.5, rel=0.02)
    assert float(_state(hass, "days_left").state) == pytest.approx(27 / 1.5, rel=0.02)

    # A new bag of salt counts as refill.
    freezer.tick(timedelta(minutes=10))
    source("52000", unit="g")
    await hass.async_block_till_done()
    assert _state(hass, "last_refill").state != "unknown"


async def test_weight_message(hass: HomeAssistant, source) -> None:
    phone = async_mock_service(hass, "notify", "mobile_app_pixel")
    source("8", unit="kg")
    await _setup(
        hass,
        advanced={"smoothing": 0},
        thresholds=[{
            "id": "salt", "name": "Salz nachfüllen", "value": 5, "direction": "below",
            "notify": True, "targets": ["service:mobile_app_pixel"],
        }],
    )
    source("4.5", unit="kg")
    await hass.async_block_till_done()
    assert len(phone) == 1
    assert phone[0].data["message"].startswith("Salzvorrat: Salz nachfüllen erreicht. Pegel 4,5 kg")


async def test_weight_rejects_length(hass: HomeAssistant, source) -> None:
    source("20", unit="kg")
    await _setup(hass)
    source("20", unit="cm")
    await hass.async_block_till_done()
    assert _state(hass, "data_quality").state == "unavailable"
