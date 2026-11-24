"""WebSocket commands for the card: read and save the thresholds of an entry."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from . import messaging
from .const import CONF_THRESHOLDS, DOMAIN
from .thresholds import DIRECTIONS, Threshold

COLOR = vol.All([vol.All(vol.Coerce(int), vol.Range(min=0, max=255))], vol.Length(min=3, max=3))

THRESHOLD_SCHEMA = vol.Schema(
    {
        vol.Optional("id"): vol.Any(None, vol.All(str, vol.Length(max=32))),
        vol.Required("name"): vol.All(str, vol.Strip, vol.Length(min=1, max=80)),
        vol.Required("value"): vol.Coerce(float),
        vol.Required("direction"): vol.In(DIRECTIONS),
        vol.Optional("hysteresis", default=2.0): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional("color"): vol.Any(None, COLOR),
        vol.Optional("notify", default=False): bool,
        vol.Optional("targets", default=[]): [str],
        vol.Optional("critical", default=False): bool,
        vol.Optional("message", default=""): vol.Any(None, vol.All(str, vol.Length(max=500))),
        vol.Optional("clear_message", default=True): bool,
        vol.Optional("repeat", default=0): vol.All(vol.Coerce(float), vol.Range(min=0, max=10080)),
    },
    extra=vol.REMOVE_EXTRA,
)


@callback
def async_register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_get_thresholds)
    websocket_api.async_register_command(hass, ws_save_thresholds)
    websocket_api.async_register_command(hass, ws_test_threshold)


def _entry_for(hass: HomeAssistant, entity_id: str) -> ConfigEntry | None:
    reg = er.async_get(hass).async_get(entity_id)
    if reg is None or reg.platform != DOMAIN or reg.config_entry_id is None:
        return None
    return hass.config_entries.async_get_entry(reg.config_entry_id)


def model_for(hass: HomeAssistant, entity_id: str):
    """The running model behind a Level Watch entity, or None."""
    entry = _entry_for(hass, entity_id)
    if entry is None or entry.state is not ConfigEntryState.LOADED:
        return None
    return entry.runtime_data


def _public(item: dict[str, Any]) -> dict[str, Any]:
    th = Threshold.from_dict(item)
    return {
        "id": th.id,
        "name": th.name,
        "value": th.value,
        "direction": th.direction,
        "hysteresis": th.hysteresis,
        "color": list(th.color),
        "notify": th.notify,
        "targets": list(th.targets),
        "critical": th.critical,
        "message": th.message,
        "clear_message": th.clear_message,
        "repeat": th.repeat,
    }


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/thresholds", vol.Required("entity_id"): str}
)
@callback
def ws_get_thresholds(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Thresholds of the entry behind the entity and the possible notify targets."""
    entry = _entry_for(hass, msg["entity_id"])
    if entry is None:
        connection.send_error(msg["id"], "not_found", "Not a Level Watch entity")
        return
    connection.send_result(
        msg["id"],
        {
            "entry_id": entry.entry_id,
            "thresholds": [_public(t) for t in entry.options.get(CONF_THRESHOLDS, [])],
            "targets": messaging.available_targets(hass),
            "can_edit": connection.user.is_admin,
        },
    )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/thresholds/save",
        vol.Required("entity_id"): str,
        vol.Required("thresholds"): [dict],
    }
)
@callback
def ws_save_thresholds(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Replace all thresholds of the entry; the entry reloads like after the options."""
    entry = _entry_for(hass, msg["entity_id"])
    if entry is None:
        connection.send_error(msg["id"], "not_found", "Not a Level Watch entity")
        return
    known = {t["id"] for t in entry.options.get(CONF_THRESHOLDS, [])}
    cleaned: list[dict[str, Any]] = []
    for index, raw in enumerate(msg["thresholds"]):
        try:
            item = THRESHOLD_SCHEMA(raw)
        except vol.Invalid as err:
            connection.send_error(msg["id"], "invalid_format", f"Threshold {index + 1}: {err}")
            return
        if item["notify"] and not item["targets"]:
            connection.send_error(
                msg["id"], "targets_required", f"Threshold {index + 1}: no notify target"
            )
            return
        # Keep ids the entry knows so state and history follow the threshold.
        if item.get("id") not in known:
            item["id"] = uuid4().hex[:8]
        item["message"] = item.get("message") or ""
        if item.get("color") is None:
            item.pop("color", None)
        cleaned.append(item)
    cleaned.sort(key=lambda t: t["value"])
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_THRESHOLDS: cleaned}
    )
    connection.send_result(msg["id"], {"thresholds": [_public(t) for t in cleaned]})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/thresholds/test",
        vol.Required("entity_id"): str,
        vol.Required("threshold"): dict,
    }
)
@websocket_api.async_response
async def ws_test_threshold(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Send a test message for a threshold as it is in the editor, saved or not."""
    model = model_for(hass, msg["entity_id"])
    if model is None:
        connection.send_error(msg["id"], "not_found", "Not a loaded Level Watch entity")
        return
    try:
        item = THRESHOLD_SCHEMA(msg["threshold"])
    except vol.Invalid as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    if not item["targets"]:
        connection.send_error(msg["id"], "targets_required", "No notify target")
        return
    item["id"] = item.get("id") or "draft"
    item["message"] = item.get("message") or ""
    result = await model.async_send_test(Threshold.from_dict(item))
    connection.send_result(msg["id"], result)
