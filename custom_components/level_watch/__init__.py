"""Level Watch: monitor a water or tank level with trend and thresholds."""

from __future__ import annotations

from pathlib import Path

import voluptuous as vol

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_COMPONENT_LOADED, Platform
from homeassistant.core import (
    Event,
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .const import CARD_URL, DOMAIN, STORAGE_VERSION, VERSION
from . import websocket
from .model import LevelWatchModel

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type LevelWatchConfigEntry = ConfigEntry[LevelWatchModel]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the Level Watch card; no resource needs to be added by hand."""
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                CARD_URL,
                str(Path(__file__).parent / "www" / "level-watch-card.js"),
                cache_headers=False,
            )
        ]
    )
    _async_register_card(hass)
    websocket.async_register(hass)
    _async_register_services(hass)
    return True


SEND_TEST_SCHEMA = vol.Schema(
    {vol.Required("entity_id"): cv.entity_id, vol.Optional("threshold"): cv.string}
)


@callback
def _async_register_services(hass: HomeAssistant) -> None:
    async def send_test(call: ServiceCall) -> ServiceResponse:
        model = websocket.model_for(hass, call.data["entity_id"])
        if model is None:
            raise ServiceValidationError(
                f"{call.data['entity_id']} is not an entity of a loaded Level Watch entry"
            )
        wanted = call.data.get("threshold", "").strip().casefold()
        if wanted:
            chosen = [th for th in model.settings.thresholds if th.name.casefold() == wanted]
            if not chosen:
                raise ServiceValidationError(f"No threshold named {call.data['threshold']!r}")
            if not chosen[0].targets:
                raise ServiceValidationError(
                    f"Threshold {chosen[0].name!r} has no notify target"
                )
        else:
            chosen = [th for th in model.settings.thresholds if th.notify and th.targets]
            if not chosen:
                raise ServiceValidationError("No threshold with a notification")
        results = {th.name: await model.async_send_test(th) for th in chosen}
        return {"thresholds": results} if call.return_response else None

    hass.services.async_register(
        DOMAIN,
        "send_test",
        send_test,
        schema=SEND_TEST_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )


@callback
def _async_register_card(hass: HomeAssistant) -> None:
    """Load the card in the browser once the frontend is set up."""
    url = f"{CARD_URL}?v={VERSION}"
    if "frontend" in hass.config.components:
        frontend.add_extra_js_url(hass, url)
        return

    @callback
    def _component_loaded(event: Event) -> None:
        if event.data.get("component") == "frontend":
            frontend.add_extra_js_url(hass, url)
            unsub()

    unsub = hass.bus.async_listen(EVENT_COMPONENT_LOADED, _component_loaded)


async def async_setup_entry(hass: HomeAssistant, entry: LevelWatchConfigEntry) -> bool:
    model = LevelWatchModel(hass, entry.entry_id, {**entry.data, **entry.options})
    await model.async_load()
    entry.runtime_data = model
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_remove_stale_entities(hass, entry, model)
    model.async_start()
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LevelWatchConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_stop()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: LevelWatchConfigEntry) -> None:
    """Delete the stored history together with the entry."""
    await Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}").async_remove()


def _async_remove_stale_entities(
    hass: HomeAssistant, entry: LevelWatchConfigEntry, model: LevelWatchModel
) -> None:
    """Drop entities of removed thresholds or settings, e.g. the percentage."""
    registry = er.async_get(hass)
    for reg in er.async_entries_for_config_entry(registry, entry.entry_id):
        if reg.unique_id not in model.unique_ids:
            registry.async_remove(reg.entity_id)


async def _async_reload(hass: HomeAssistant, entry: LevelWatchConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
