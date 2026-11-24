"""Telegram puts the title as a plain first line, so Level Watch makes it bold."""

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.level_watch import messaging


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("markdown", "*Level Watch meldet: Stand Salz*"),
        ("html", "<b>Level Watch meldet: Stand Salz</b>"),
        ("markdownv2", "*Level Watch meldet: Stand Salz \\(1\\.2\\)*"),
        ("plain_text", "Level Watch meldet: Stand Salz"),
    ],
)
async def test_telegram_title(hass: HomeAssistant, mode: str, expected: str) -> None:
    calls = async_mock_service(hass, "notify", "send_message")
    bot = MockConfigEntry(domain="telegram_bot", options={"parse_mode": mode})
    bot.add_to_hass(hass)
    er.async_get(hass).async_get_or_create(
        "notify", "telegram_bot", "chat1", config_entry=bot, suggested_object_id="bernd"
    )
    title = "Level Watch meldet: Stand Salz" + (" (1.2)" if mode == "markdownv2" else "")
    await messaging.async_send(
        hass, ("entity:notify.bernd",), title=title, message="Test", tag="t",
        critical=False, cleared=False,
    )
    assert calls[0].data["title"] == expected


async def test_other_services_keep_title(hass: HomeAssistant) -> None:
    calls = async_mock_service(hass, "notify", "send_message")
    er.async_get(hass).async_get_or_create(
        "notify", "alexa_media", "echo", suggested_object_id="echo"
    )
    await messaging.async_send(
        hass, ("entity:notify.echo",), title="Level Watch meldet: Rhein", message="x",
        tag="t", critical=False, cleared=False,
    )
    assert calls[0].data["title"] == "Level Watch meldet: Rhein"
