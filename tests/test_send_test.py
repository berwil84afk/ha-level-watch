"""Tests for test notifications: the send_test action and the card's test button."""

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_mock_service,
)

from custom_components.level_watch.const import DOMAIN, EVENT_THRESHOLD

from .conftest import CONFIG

FLOOD = {
    "id": "flood1",
    "name": "Meldestufe 1",
    "value": 500,
    "direction": "above",
    "notify": True,
    "targets": ["service:mobile_app_pixel"],
    "critical": True,
}
QUIET = {"id": "low1", "name": "Niedrigwasser", "value": 100, "direction": "below"}


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    hass.config.language = "de"
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG,
        options={"advanced": {"smoothing": 0}, "thresholds": [FLOOD, QUIET]},
        title="Rhein",
        entry_id="rhein",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _level_id(hass: HomeAssistant) -> str:
    return er.async_get(hass).async_get_entity_id("sensor", DOMAIN, "rhein_level")


async def test_action_sends_marked_message(hass: HomeAssistant, source) -> None:
    phone = async_mock_service(hass, "notify", "mobile_app_pixel")
    events = async_capture_events(hass, EVENT_THRESHOLD)
    source("320")
    await _setup(hass)

    result = await hass.services.async_call(
        DOMAIN, "send_test", {"entity_id": _level_id(hass)}, blocking=True, return_response=True
    )
    assert len(phone) == 1
    message = phone[0].data["message"]
    assert message.startswith("Test: Rhein: Meldestufe 1 erreicht. Pegel 320 cm")
    assert phone[0].data["data"]["tag"].endswith("_test")
    assert phone[0].data["data"]["channel"] == "alarm_stream"  # critical is kept
    assert result["thresholds"]["Meldestufe 1"]["sent"] == 1
    assert not events  # a test is no threshold event
    stage = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, "rhein_stage")
    assert hass.states.get(stage).state != "Meldestufe 1"


async def test_action_errors(hass: HomeAssistant, source) -> None:
    source("320")
    await _setup(hass)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "send_test", {"entity_id": _level_id(hass), "threshold": "Gibt es nicht"},
            blocking=True,
        )
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "send_test", {"entity_id": _level_id(hass), "threshold": "niedrigwasser"},
            blocking=True,
        )
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "send_test", {"entity_id": "sensor.pegel"}, blocking=True
        )


async def test_editor_test_uses_draft(hass: HomeAssistant, source, hass_ws_client) -> None:
    phone = async_mock_service(hass, "notify", "mobile_app_pixel")
    source("320")
    await _setup(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({
        "type": "level_watch/thresholds/test",
        "entity_id": _level_id(hass),
        "threshold": {
            "name": "Neu", "value": 400, "direction": "above", "color": [1, 2, 3],
            "targets": ["service:mobile_app_pixel", "service:gone", "persistent_notification"],
            "message": "{threshold} bei {level} {unit}",
        },
    })
    response = await client.receive_json()
    assert response["success"], response
    result = response["result"]
    assert result["message"] == "Test: Neu bei 320 cm"
    assert result["sent"] == 2
    assert [f["target"] for f in result["failed"]] == ["service:gone"]
    assert phone[0].data["message"] == "Test: Neu bei 320 cm"

    await client.send_json_auto_id({
        "type": "level_watch/thresholds/test",
        "entity_id": _level_id(hass),
        "threshold": {"name": "Neu", "value": 400, "direction": "above", "targets": []},
    })
    response = await client.receive_json()
    assert response["error"]["code"] == "targets_required"
