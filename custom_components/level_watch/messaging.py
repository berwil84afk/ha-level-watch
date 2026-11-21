"""Send threshold messages to the targets chosen for a threshold."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

_LOGGER = logging.getLogger(__name__)

# Target ids as stored in the threshold options.
TARGET_PERSISTENT = "persistent_notification"
SERVICE_PREFIX = "service:"  # legacy notify service, e.g. service:mobile_app_pixel
ENTITY_PREFIX = "entity:"  # notify entity, e.g. entity:notify.telegram

NOTIFY = "notify"


def available_targets(hass: HomeAssistant) -> dict[str, str]:
    """All targets a threshold can notify, as id -> label."""
    targets = {TARGET_PERSISTENT: "Home Assistant (persistent notification)"}
    for service in sorted(hass.services.async_services_for_domain(NOTIFY)):
        if service in ("send_message", "persistent_notification"):
            continue
        targets[f"{SERVICE_PREFIX}{service}"] = f"notify.{service}"
    registry = er.async_get(hass)
    for state in sorted(hass.states.async_all(NOTIFY), key=lambda s: s.entity_id):
        entry = registry.async_get(state.entity_id)
        name = state.name or state.entity_id
        if entry is None or not entry.disabled_by:
            targets[f"{ENTITY_PREFIX}{state.entity_id}"] = f"{name} ({state.entity_id})"
    return targets


async def async_send(
    hass: HomeAssistant,
    targets: tuple[str, ...],
    *,
    title: str,
    message: str,
    tag: str,
    critical: bool,
    cleared: bool,
) -> None:
    """Send one message to every target; a failing target does not stop others."""
    for target in targets:
        try:
            await _send_one(
                hass, target, title=title, message=message, tag=tag,
                critical=critical and not cleared, cleared=cleared,
            )
        except (HomeAssistantError, ValueError) as err:
            _LOGGER.warning("Level Watch could not notify %s: %s", target, err)


async def _send_one(
    hass: HomeAssistant,
    target: str,
    *,
    title: str,
    message: str,
    tag: str,
    critical: bool,
    cleared: bool,
) -> None:
    if target == TARGET_PERSISTENT:
        # The same id replaces the alert with the all-clear and vice versa.
        persistent_notification.async_create(hass, message, title, notification_id=tag)
        return

    if target.startswith(ENTITY_PREFIX):
        await hass.services.async_call(
            NOTIFY,
            "send_message",
            {"entity_id": target.removeprefix(ENTITY_PREFIX), "title": title, "message": message},
            blocking=True,
        )
        return

    if target.startswith(SERVICE_PREFIX):
        service = target.removeprefix(SERVICE_PREFIX)
        if not hass.services.has_service(NOTIFY, service):
            raise ValueError(f"notify.{service} does not exist (any more)")
        payload: dict[str, Any] = {"title": title, "message": message}
        if service.startswith("mobile_app_"):
            payload["data"] = _mobile_app_data(tag, critical)
        await hass.services.async_call(NOTIFY, service, payload, blocking=True)
        return

    raise ValueError(f"unknown target {target!r}")


def _mobile_app_data(tag: str, critical: bool) -> dict[str, Any]:
    """Companion app extras: replace older messages, optionally break silence."""
    data: dict[str, Any] = {"tag": tag, "group": "level_watch"}
    if critical:
        # iOS: critical alert; Android: alarm stream, delivered immediately.
        data["push"] = {"sound": {"name": "default", "critical": 1, "volume": 1.0}}
        data.update({"ttl": 0, "priority": "high", "channel": "alarm_stream"})
    return data
