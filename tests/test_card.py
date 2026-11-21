"""Tests for serving the card and the attributes it reads."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.level_watch.const import CARD_URL, DOMAIN

from .conftest import CONFIG


async def test_card_is_served(hass: HomeAssistant, hass_client) -> None:
    assert await async_setup_component(hass, DOMAIN, {})
    client = await hass_client()
    response = await client.get(CARD_URL)
    assert response.status == 200
    body = await response.text()
    assert 'customElements.define("level-watch-card"' in body


async def test_level_attributes_for_card(hass: HomeAssistant, source) -> None:
    source("300")
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            **CONFIG,
            "kind": "tank",
            "reference_max": None,
            "tank": {"shape": "horizontal_cylinder", "diameter": 400, "length": 500},
        },
        title="Öl",
        entry_id="oel",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, "oel_level")
    attrs = hass.states.get(entity_id).attributes
    assert attrs["shape"] == "horizontal_cylinder"
    assert attrs["top"] == 400  # the diameter when there is no top reference
    assert attrs["quality"] == "ok"
    assert attrs["stage"] is None
    assert attrs["color"] == "#26a69a"
    assert 80 < attrs["percent"] < 81  # 3/4 of the height is about 80 % by volume
    for key in ("trend", "rate", "consumption", "days_left", "hours_to_next"):
        assert key in attrs
