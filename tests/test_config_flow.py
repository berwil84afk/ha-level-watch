"""Tests for the Level Watch config and options flow."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.level_watch.const import DOMAIN

from .conftest import CONFIG, SOURCE

USER_INPUT = {
    "name": "Rhein",
    "source_entity": SOURCE,
    "source_unit": "auto",
    "kind": "water",
    "measurement_mode": "level",
    "offset": 0,
    "reference_min": 0,
    "reference_max": 800,
    "tank": {"shape": "none"},
}


async def _start(hass: HomeAssistant):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def test_user_flow(hass: HomeAssistant, source) -> None:
    result = await _start(hass)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Rhein"
    assert result["data"]["sensor_height"] is None
    assert result["data"]["reference_max"] == 800


async def test_user_flow_errors(hass: HomeAssistant, source) -> None:
    result = await _start(hass)
    bad = {
        **USER_INPUT,
        "measurement_mode": "distance",
        "reference_min": 100,
        "reference_max": 50,
    }
    result = await hass.config_entries.flow.async_configure(result["flow_id"], bad)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        "sensor_height": "height_required",
        "reference_max": "max_below_min",
    }


async def test_unit_needed_without_sensor_unit(hass: HomeAssistant, source) -> None:
    source("1.2", unit=None)
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["errors"] == {"source_unit": "unit_unknown"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, "source_unit": "m"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_same_source_twice(hass: HomeAssistant, source) -> None:
    MockConfigEntry(domain=DOMAIN, data=CONFIG).add_to_hass(hass)
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant, source) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data=CONFIG, title="Rhein")
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["settings", "add_threshold", "add_preset"]
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "settings"}
    )
    assert result["type"] is FlowResultType.FORM
    options = {
        k: v for k, v in USER_INPUT.items() if k not in ("name", "reference_max")
    }
    options["advanced"] = {
        "trend_window": 30,
        "trend_deadband": 2,
        "smoothing": 0,
        "stale_timeout": 120,
        "max_jump": 0,
    }
    result = await hass.config_entries.options.async_configure(result["flow_id"], options)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    # Clearing the top reference removes it instead of keeping 800.
    assert entry.options["reference_max"] is None
    await hass.async_block_till_done()
    assert entry.runtime_data.settings.trend_window == 30 * 60
    assert entry.runtime_data.settings.ref_max is None
