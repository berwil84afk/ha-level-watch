"""Config and options flow for Level Watch."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers import selector

from . import calc
from .const import (
    CONF_ADVANCED,
    CONF_KIND,
    CONF_MAX_JUMP,
    CONF_MODE,
    CONF_NAME,
    CONF_OFFSET,
    CONF_REF_MAX,
    CONF_REF_MIN,
    CONF_SENSOR_HEIGHT,
    CONF_SMOOTHING,
    CONF_SOURCE,
    CONF_SOURCE_UNIT,
    CONF_STALE_TIMEOUT,
    CONF_TREND_DEADBAND,
    CONF_TREND_WINDOW,
    DEFAULT_MAX_JUMP,
    DEFAULT_NAME,
    DEFAULT_OFFSET,
    DEFAULT_REF_MIN,
    DEFAULT_SMOOTHING,
    DEFAULT_STALE_TIMEOUT,
    DEFAULT_TREND_DEADBAND,
    DEFAULT_TREND_WINDOW,
    DOMAIN,
    KIND_WATER,
    KINDS,
    MODE_DISTANCE,
    MODE_LEVEL,
    MODES,
    SOURCE_UNITS,
    UNIT_AUTO,
)


def _number(
    min_value: float, max_value: float, step: float, unit: str | None = None
) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=min_value,
            max=max_value,
            step=step,
            unit_of_measurement=unit,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _select(options: list[str], key: str) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            translation_key=key,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


LENGTH = _number(-100000, 100000, 0.1, "cm")
POSITIVE_LENGTH = _number(0, 100000, 0.1, "cm")


def _basic_schema(defaults: Mapping[str, Any], *, with_name: bool) -> dict:
    """Fields shared by the setup and the options form."""

    def opt(key: str) -> vol.Optional:
        value = defaults.get(key)
        if value is None:
            return vol.Optional(key)
        return vol.Optional(key, description={"suggested_value": value})

    fields: dict = {}
    if with_name:
        fields[vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME))] = (
            selector.TextSelector()
        )
    fields.update(
        {
            vol.Required(CONF_SOURCE, default=defaults.get(CONF_SOURCE, vol.UNDEFINED)): (
                selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
            ),
            vol.Required(
                CONF_SOURCE_UNIT, default=defaults.get(CONF_SOURCE_UNIT, UNIT_AUTO)
            ): _select(SOURCE_UNITS, CONF_SOURCE_UNIT),
            vol.Required(CONF_KIND, default=defaults.get(CONF_KIND, KIND_WATER)): _select(
                KINDS, CONF_KIND
            ),
            vol.Required(CONF_MODE, default=defaults.get(CONF_MODE, MODE_LEVEL)): _select(
                MODES, CONF_MODE
            ),
            opt(CONF_SENSOR_HEIGHT): POSITIVE_LENGTH,
            vol.Required(
                CONF_OFFSET, default=defaults.get(CONF_OFFSET, DEFAULT_OFFSET)
            ): LENGTH,
            vol.Required(
                CONF_REF_MIN, default=defaults.get(CONF_REF_MIN, DEFAULT_REF_MIN)
            ): LENGTH,
            opt(CONF_REF_MAX): LENGTH,
        }
    )
    return fields


def _advanced_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    adv = defaults.get(CONF_ADVANCED) or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_TREND_WINDOW, default=adv.get(CONF_TREND_WINDOW, DEFAULT_TREND_WINDOW)
            ): _number(5, 1440, 1, "min"),
            vol.Required(
                CONF_TREND_DEADBAND,
                default=adv.get(CONF_TREND_DEADBAND, DEFAULT_TREND_DEADBAND),
            ): _number(0, 1000, 0.1, "cm/h"),
            vol.Required(
                CONF_SMOOTHING, default=adv.get(CONF_SMOOTHING, DEFAULT_SMOOTHING)
            ): _number(0, 120, 1, "min"),
            vol.Required(
                CONF_STALE_TIMEOUT,
                default=adv.get(CONF_STALE_TIMEOUT, DEFAULT_STALE_TIMEOUT),
            ): _number(5, 10080, 1, "min"),
            vol.Required(
                CONF_MAX_JUMP, default=adv.get(CONF_MAX_JUMP, DEFAULT_MAX_JUMP)
            ): _number(0, 100000, 0.1, "cm"),
        }
    )


def _validate(hass: HomeAssistant, data: Mapping[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if data.get(CONF_MODE) == MODE_DISTANCE and data.get(CONF_SENSOR_HEIGHT) is None:
        errors[CONF_SENSOR_HEIGHT] = "height_required"
    ref_max = data.get(CONF_REF_MAX)
    if ref_max is not None and ref_max <= data.get(CONF_REF_MIN, DEFAULT_REF_MIN):
        errors[CONF_REF_MAX] = "max_below_min"
    if data.get(CONF_SOURCE_UNIT, UNIT_AUTO) == UNIT_AUTO:
        state = hass.states.get(data[CONF_SOURCE])
        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) if state else None
        if not calc.is_length_unit(unit):
            errors[CONF_SOURCE_UNIT] = "unit_unknown"
    return errors


def _with_cleared_optionals(data: dict[str, Any]) -> dict[str, Any]:
    """Store emptied optional fields as None so older values do not stick."""
    return {CONF_SENSOR_HEIGHT: None, CONF_REF_MAX: None, **data}


class LevelWatchConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up a monitored level."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate(self.hass, user_input)
            if not errors:
                self._async_abort_entries_match({CONF_SOURCE: user_input[CONF_SOURCE]})
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=_with_cleared_optionals(user_input),
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(_basic_schema(user_input or {}, with_name=True)),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return LevelWatchOptionsFlow()


class LevelWatchOptionsFlow(OptionsFlow):
    """Change the source, geometry and trend settings."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate(self.hass, user_input)
            if not errors:
                return self.async_create_entry(data=_with_cleared_optionals(user_input))
            current = {**current, **user_input}
        schema = _basic_schema(current, with_name=False)
        schema[vol.Required(CONF_ADVANCED)] = section(
            _advanced_schema(current), {"collapsed": True}
        )
        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(schema), errors=errors
        )
