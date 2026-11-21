"""Tests for threshold templates and the card's threshold editor API."""

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.level_watch.const import DOMAIN

from .conftest import CONFIG

EXISTING = {
    "id": "keep1",
    "name": "Meldestufe 1",
    "value": 500,
    "direction": "above",
    "color": [251, 192, 45],
}


async def _setup(hass: HomeAssistant, thresholds=None) -> MockConfigEntry:
    hass.config.language = "de"
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG,
        options={"thresholds": thresholds or []},
        title="Rhein",
        entry_id="rhein",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _level_id(hass: HomeAssistant) -> str:
    return er.async_get(hass).async_get_entity_id("sensor", DOMAIN, "rhein_level")


async def test_river_preset(hass: HomeAssistant, source) -> None:
    entry = await _setup(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "add_preset"}
    )
    assert result["step_id"] == "add_preset"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"preset": "river"}
    )
    assert result["step_id"] == "preset_values"
    base = {"notify": False, "targets": [], "critical": False}
    result = await hass.config_entries.options.async_configure(result["flow_id"], base)
    assert result["errors"] == {"base": "preset_empty"}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {**base, "low": 150, "stage1": 500, "stage3": 700, "notify": True,
         "targets": ["persistent_notification"], "critical": True},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    ths = entry.options["thresholds"]
    assert [(t["name"], t["value"], t["direction"]) for t in ths] == [
        ("Niedrigwasser", 150, "below"),
        ("Meldestufe 1", 500, "above"),
        ("Meldestufe 3", 700, "above"),
    ]
    # Critical only where it makes sense.
    assert [t["critical"] for t in ths] == [False, False, True]
    assert all(t["targets"] == ["persistent_notification"] for t in ths)
    assert len({t["id"] for t in ths}) == 3


async def test_ws_get(hass: HomeAssistant, source, hass_ws_client) -> None:
    await _setup(hass, [EXISTING])
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "level_watch/thresholds", "entity_id": _level_id(hass)})
    msg = await client.receive_json()
    assert msg["success"], msg
    res = msg["result"]
    assert res["entry_id"] == "rhein"
    assert res["can_edit"] is True
    assert res["thresholds"][0]["id"] == "keep1"
    assert res["thresholds"][0]["color"] == [251, 192, 45]
    assert "persistent_notification" in res["targets"]

    await client.send_json_auto_id({"type": "level_watch/thresholds", "entity_id": "sensor.pegel"})
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "not_found"


async def test_ws_save(hass: HomeAssistant, source, hass_ws_client) -> None:
    entry = await _setup(hass, [EXISTING])
    client = await hass_ws_client(hass)
    level_id = _level_id(hass)

    async def save(thresholds):
        await client.send_json_auto_id(
            {"type": "level_watch/thresholds/save", "entity_id": level_id, "thresholds": thresholds}
        )
        return await client.receive_json()

    msg = await save([{"name": "X", "value": 1, "direction": "above", "notify": True}])
    assert msg["error"]["code"] == "targets_required"
    msg = await save([{"name": "", "value": 1, "direction": "above"}])
    assert msg["error"]["code"] == "invalid_format"
    msg = await save([{"name": "X", "value": 1, "direction": "sideways"}])
    assert msg["error"]["code"] == "invalid_format"

    msg = await save(
        [
            {**EXISTING, "value": 550, "color": [1, 2, 3]},
            {"id": "forged", "name": "Niedrigwasser", "value": 120, "direction": "below",
             "notify": True, "targets": ["persistent_notification"], "unknown": 1},
        ]
    )
    assert msg["success"], msg
    await hass.async_block_till_done()
    ths = entry.options["thresholds"]
    assert [t["name"] for t in ths] == ["Niedrigwasser", "Meldestufe 1"]
    assert ths[1]["id"] == "keep1"  # known ids survive
    assert ths[0]["id"] != "forged"  # unknown ids are replaced
    assert "unknown" not in ths[0]
    assert ths[1]["color"] == [1, 2, 3]
    # The entry reloaded with the new thresholds.
    assert {t.name for t in entry.runtime_data.settings.thresholds} == {"Niedrigwasser", "Meldestufe 1"}
    state = hass.states.get(level_id)
    assert [t["value"] for t in state.attributes["thresholds"]] == [120, 550]


async def test_ws_save_needs_admin(
    hass: HomeAssistant, source, hass_ws_client, hass_read_only_access_token
) -> None:
    entry = await _setup(hass, [EXISTING])
    client = await hass_ws_client(hass, hass_read_only_access_token)
    await client.send_json_auto_id(
        {"type": "level_watch/thresholds/save", "entity_id": _level_id(hass), "thresholds": []}
    )
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "unauthorized"
    assert entry.options["thresholds"] == [EXISTING]
