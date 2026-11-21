"""Fixtures for Level Watch tests."""

import pytest

from homeassistant.core import HomeAssistant

SOURCE = "sensor.pegel"

CONFIG = {
    "name": "Rhein",
    "source_entity": SOURCE,
    "source_unit": "auto",
    "kind": "water",
    "measurement_mode": "level",
    "sensor_height": None,
    "offset": 0,
    "reference_min": 0,
    "reference_max": 800,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in all tests."""
    return


@pytest.fixture
def source(hass: HomeAssistant):
    """Set the source sensor; returns a setter for later values."""

    def set_level(value: str, unit: str | None = "cm", force: bool = False) -> None:
        attrs = {"unit_of_measurement": unit} if unit else {}
        hass.states.async_set(SOURCE, value, attrs, force_update=force)

    set_level("400")
    return set_level
