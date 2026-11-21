"""Tests for threshold entities, events and notifications."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.level_watch.const import DOMAIN, EVENT_THRESHOLD

from .conftest import CONFIG

FLOOD = {
    "id": "flood1",
    "name": "Meldestufe 1",
    "value": 500,
    "direction": "above",
    "hysteresis": 5,
    "color": [255, 0, 0],
    "notify": True,
    "targets": ["service:mobile_app_pixel", "persistent_notification"],
    "critical": True,
    "message": "",
    "clear_message": True,
    "repeat": 0,
}


@pytest.fixture
def phone(hass: HomeAssistant):
    return async_mock_service(hass, "notify", "mobile_app_pixel")


async def _setup(hass: HomeAssistant, thresholds, **options) -> MockConfigEntry:
    hass.config.language = "de"
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG,
        options={"advanced": {"smoothing": 0}, "thresholds": thresholds, **options},
        title="Rhein",
        entry_id="rhein",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _entity(hass: HomeAssistant, platform: str, key: str):
    entity_id = er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"rhein_{key}")
    assert entity_id, key
    return hass.states.get(entity_id)


async def test_crossing_notifies_and_clears(hass: HomeAssistant, source, phone) -> None:
    events = async_capture_events(hass, EVENT_THRESHOLD)
    await _setup(hass, [FLOOD])
    assert _entity(hass, "binary_sensor", "threshold_flood1").state == "off"
    assert _entity(hass, "sensor", "stage").state == "Normal"
    assert phone == []  # nothing to report at 400 cm

    source("505")
    await hass.async_block_till_done()
    assert _entity(hass, "binary_sensor", "threshold_flood1").state == "on"
    stage = _entity(hass, "sensor", "stage")
    assert stage.state == "Meldestufe 1"
    assert stage.attributes["color"] == "#ff0000"
    level = _entity(hass, "sensor", "level")
    assert level.attributes["color"] == "#ff0000"
    assert level.attributes["thresholds"][0]["active"] is True

    assert len(phone) == 1
    call = phone[0].data
    assert call["title"] == "Rhein"
    assert call["message"].startswith("Rhein: Meldestufe 1 erreicht. Pegel 505 cm")
    assert call["data"]["tag"] == "level_watch_rhein_flood1"
    assert call["data"]["push"]["sound"]["critical"] == 1
    notes = persistent_notification._async_get_or_create_notifications(hass)
    assert "level_watch_rhein_flood1" in notes

    assert [e.data["active"] for e in events] == [True]

    # Within the hysteresis: still active, no new message.
    source("497")
    await hass.async_block_till_done()
    assert _entity(hass, "binary_sensor", "threshold_flood1").state == "on"
    assert len(phone) == 1

    source("490")
    await hass.async_block_till_done()
    assert _entity(hass, "binary_sensor", "threshold_flood1").state == "off"
    assert len(phone) == 2
    assert "aufgehoben" in phone[1].data["message"]
    assert "push" not in phone[1].data["data"]  # the all-clear is not critical
    assert [e.data["active"] for e in events] == [True, False]


async def test_no_second_message_after_restart(hass: HomeAssistant, source, phone) -> None:
    entry = await _setup(hass, [FLOOD])
    source("505")
    await hass.async_block_till_done()
    assert len(phone) == 1
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert _entity(hass, "binary_sensor", "threshold_flood1").state == "on"
    assert len(phone) == 1


async def test_repeat(
    hass: HomeAssistant, source, phone, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass, [{**FLOOD, "repeat": 30, "clear_message": False}])
    source("505")
    await hass.async_block_till_done()
    assert len(phone) == 1
    for _ in range(31):
        freezer.tick(timedelta(minutes=1))
        source("505", force=True)  # sensor keeps reporting, data stays fresh
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
    assert len(phone) == 2

    source("400")
    await hass.async_block_till_done()
    assert len(phone) == 2  # no all-clear wanted


async def test_no_evaluation_while_stale(
    hass: HomeAssistant, source, phone, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass, [FLOOD])
    source("unavailable", unit=None)
    await hass.async_block_till_done()
    assert len(phone) == 0
    assert _entity(hass, "binary_sensor", "threshold_flood1").state == "off"


async def test_failing_target_does_not_stop_others(hass: HomeAssistant, source) -> None:
    # notify.mobile_app_pixel does not exist here.
    await _setup(hass, [FLOOD])
    source("505")
    await hass.async_block_till_done()
    notes = persistent_notification._async_get_or_create_notifications(hass)
    assert "level_watch_rhein_flood1" in notes


async def test_time_to_next(
    hass: HomeAssistant, source, phone, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass, [{**FLOOD, "notify": False}])
    level = 400.0
    for _ in range(12):  # 60 cm/h
        freezer.tick(timedelta(minutes=5))
        level += 5
        source(str(level))
        await hass.async_block_till_done()
    assert _entity(hass, "sensor", "next_threshold").state == "Meldestufe 1"
    # 460 cm now, 40 cm to go at 60 cm/h
    assert float(_entity(hass, "sensor", "time_to_next").state) == pytest.approx(
        40 / 60, abs=0.01
    )


async def test_threshold_options(hass: HomeAssistant, source, phone) -> None:
    entry = await _setup(hass, [])
    assert er.async_get(hass).async_get_entity_id("sensor", DOMAIN, "rhein_stage") is None

    async def menu(step: str):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.MENU
        return await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": step}
        )

    # Add: notify without target is refused.
    result = await menu("add_threshold")
    assert result["step_id"] == "threshold"
    data = {
        "name": "Überlauf", "value": 700, "direction": "above", "hysteresis": 2,
        "notify": True, "targets": [], "critical": False, "clear_message": True,
        "repeat": 0,
    }
    result = await hass.config_entries.options.async_configure(result["flow_id"], data)
    assert result["errors"] == {"targets": "targets_required"}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {**data, "targets": ["persistent_notification"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    (th,) = entry.options["thresholds"]
    assert th["color"] == [245, 124, 0]
    assert entry.options["advanced"] == {"smoothing": 0}  # other options kept
    assert _entity(hass, "binary_sensor", f"threshold_{th['id']}") is not None
    assert _entity(hass, "sensor", "stage").state == "Normal"

    # Edit
    result = await menu("edit_threshold")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"threshold": th["id"]}
    )
    assert result["step_id"] == "threshold"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {**data, "value": 350, "notify": False}
    )
    await hass.async_block_till_done()
    assert entry.options["thresholds"][0]["value"] == 350
    assert entry.options["thresholds"][0]["id"] == th["id"]
    # 400 cm is above the new value: active right away.
    assert _entity(hass, "binary_sensor", f"threshold_{th['id']}").state == "on"

    # Remove: its entity goes too.
    result = await menu("remove_threshold")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"thresholds": [th["id"]]}
    )
    await hass.async_block_till_done()
    assert entry.options["thresholds"] == []
    registry = er.async_get(hass)
    assert registry.async_get_entity_id("binary_sensor", DOMAIN, f"rhein_threshold_{th['id']}") is None
    assert registry.async_get_entity_id("sensor", DOMAIN, "rhein_stage") is None
