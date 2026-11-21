"""Config and options flow for Level Watch."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

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

from . import calc, messaging, tank
from .const import (
    CONF_ADVANCED,
    CONF_CONSUMPTION_WINDOW,
    CONF_DIAMETER,
    CONF_KIND,
    CONF_LENGTH,
    CONF_MAX_JUMP,
    CONF_MODE,
    CONF_NAME,
    CONF_OFFSET,
    CONF_REF_MAX,
    CONF_REF_MIN,
    CONF_REFILL_JUMP,
    CONF_SENSOR_HEIGHT,
    CONF_SHAPE,
    CONF_SMOOTHING,
    CONF_SOURCE,
    CONF_SOURCE_UNIT,
    CONF_STALE_TIMEOUT,
    CONF_TANK,
    CONF_THRESHOLDS,
    CONF_TREND_DEADBAND,
    CONF_TREND_WINDOW,
    CONF_WIDTH,
    DEFAULT_CONSUMPTION_WINDOW,
    DEFAULT_MAX_JUMP,
    DEFAULT_NAME,
    DEFAULT_OFFSET,
    DEFAULT_REF_MIN,
    DEFAULT_REFILL_JUMP,
    DEFAULT_SMOOTHING,
    DEFAULT_STALE_TIMEOUT,
    DEFAULT_TREND_DEADBAND,
    DEFAULT_TREND_WINDOW,
    DOMAIN,
    KIND_TANK,
    KIND_WATER,
    KINDS,
    MODE_DISTANCE,
    MODE_LEVEL,
    MODES,
    SOURCE_UNITS,
    UNIT_AUTO,
)
from .thresholds import (
    ABOVE,
    DEFAULT_ABOVE_COLOR,
    DEFAULT_BELOW_COLOR,
    DEFAULT_HYSTERESIS,
    DIRECTIONS,
    PRESETS,
    preset_thresholds,
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
            vol.Required(CONF_TANK): section(
                _tank_schema(defaults.get(CONF_TANK) or {}),
                {"collapsed": defaults.get(CONF_KIND) != KIND_TANK},
            ),
        }
    )
    return fields


def _tank_schema(tank_conf: Mapping[str, Any]) -> vol.Schema:
    def opt(key: str) -> vol.Optional:
        value = tank_conf.get(key)
        if not value:
            return vol.Optional(key)
        return vol.Optional(key, description={"suggested_value": value})

    return vol.Schema(
        {
            vol.Required(CONF_SHAPE, default=tank_conf.get(CONF_SHAPE, tank.NONE)): _select(
                tank.SHAPES, CONF_SHAPE
            ),
            opt(CONF_DIAMETER): POSITIVE_LENGTH,
            opt(CONF_LENGTH): POSITIVE_LENGTH,
            opt(CONF_WIDTH): POSITIVE_LENGTH,
        }
    )


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
            vol.Required(
                CONF_CONSUMPTION_WINDOW,
                default=adv.get(CONF_CONSUMPTION_WINDOW, DEFAULT_CONSUMPTION_WINDOW),
            ): _number(1, 60, 1, "d"),
            vol.Required(
                CONF_REFILL_JUMP, default=adv.get(CONF_REFILL_JUMP, DEFAULT_REFILL_JUMP)
            ): _number(0, 1000, 0.5, "cm"),
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
    tank_conf = data.get(CONF_TANK) or {}
    shape = tank.TankShape(
        shape=tank_conf.get(CONF_SHAPE) or tank.NONE,
        diameter=tank_conf.get(CONF_DIAMETER),
        length=tank_conf.get(CONF_LENGTH),
        width=tank_conf.get(CONF_WIDTH),
    )
    if data.get(CONF_KIND) == KIND_TANK and shape.shape != tank.NONE and shape.missing():
        errors["base"] = f"tank_{shape.shape}"
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
    """Change the settings and manage the thresholds."""

    def __init__(self) -> None:
        self._edit_id: str | None = None
        self._preset: str | None = None

    @property
    def _options(self) -> dict[str, Any]:
        return dict(self.config_entry.options)

    @property
    def _thresholds(self) -> list[dict[str, Any]]:
        return [dict(t) for t in self.config_entry.options.get(CONF_THRESHOLDS, [])]

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        menu = ["settings", "add_threshold", "add_preset"]
        if self._thresholds:
            menu += ["edit_threshold", "remove_threshold"]
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate(self.hass, user_input)
            if not errors:
                return self.async_create_entry(
                    data={**self._options, **_with_cleared_optionals(user_input)}
                )
            current = {**current, **user_input}
        schema = _basic_schema(current, with_name=False)
        schema[vol.Required(CONF_ADVANCED)] = section(
            _advanced_schema(current), {"collapsed": True}
        )
        return self.async_show_form(
            step_id="settings", data_schema=vol.Schema(schema), errors=errors
        )

    # -- thresholds ------------------------------------------------------------

    async def async_step_add_threshold(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._edit_id = None
        return await self.async_step_threshold()

    async def async_step_add_preset(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick a set of typical thresholds, then fill in their values."""
        if user_input is not None:
            self._preset = user_input["preset"]
            return await self.async_step_preset_values()
        kind = {**self.config_entry.data, **self.config_entry.options}.get(CONF_KIND)
        return self.async_show_form(
            step_id="add_preset",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "preset", default="tank" if kind == KIND_TANK else "river"
                    ): _select(list(PRESETS), "preset")
                }
            ),
        )

    async def async_step_preset_values(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        preset = self._preset or "river"
        errors: dict[str, str] = {}
        if user_input is not None:
            values = {item.key: user_input.get(item.key) for item in PRESETS[preset]}
            if all(v is None for v in values.values()):
                errors["base"] = "preset_empty"
            elif user_input.get("notify") and not user_input.get("targets"):
                errors["targets"] = "targets_required"
            else:
                added = preset_thresholds(
                    preset,
                    values,
                    language=self.hass.config.language,
                    notify=bool(user_input.get("notify")),
                    targets=user_input.get("targets") or [],
                    critical=bool(user_input.get("critical")),
                    new_id=lambda: uuid4().hex[:8],
                )
                thresholds = sorted(self._thresholds + added, key=lambda t: t["value"])
                return self.async_create_entry(
                    data={**self._options, CONF_THRESHOLDS: thresholds}
                )
        fields: dict = {vol.Optional(item.key): LENGTH for item in PRESETS[preset]}
        fields.update(
            {
                vol.Required("notify", default=False): selector.BooleanSelector(),
                vol.Optional("targets", default=[]): self._targets_selector([]),
                vol.Required("critical", default=False): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="preset_values",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={"preset": preset},
        )

    def _targets_selector(self, current: list[str]) -> selector.SelectSelector:
        targets = messaging.available_targets(self.hass)
        # Keep targets that vanished selectable so editing does not drop them silently.
        for target in current:
            targets.setdefault(target, target)
        return selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[selector.SelectOptionDict(value=k, label=v) for k, v in targets.items()],
                multiple=True,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )

    async def async_step_edit_threshold(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._edit_id = user_input["threshold"]
            return await self.async_step_threshold()
        return self.async_show_form(
            step_id="edit_threshold",
            data_schema=vol.Schema(
                {vol.Required("threshold"): self._threshold_picker(multiple=False)}
            ),
        )

    async def async_step_remove_threshold(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            drop = set(user_input.get("thresholds") or [])
            kept = [t for t in self._thresholds if t["id"] not in drop]
            return self.async_create_entry(data={**self._options, CONF_THRESHOLDS: kept})
        return self.async_show_form(
            step_id="remove_threshold",
            data_schema=vol.Schema(
                {vol.Required("thresholds"): self._threshold_picker(multiple=True)}
            ),
        )

    async def async_step_threshold(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        thresholds = self._thresholds
        existing = next((t for t in thresholds if t["id"] == self._edit_id), None)
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get("notify") and not user_input.get("targets"):
                errors["targets"] = "targets_required"
            else:
                item = {
                    "message": "",
                    **user_input,
                    "id": existing["id"] if existing else uuid4().hex[:8],
                    "color": list(user_input.get("color") or _default_color(user_input)),
                }
                if existing:
                    thresholds = [item if t["id"] == item["id"] else t for t in thresholds]
                else:
                    thresholds.append(item)
                thresholds.sort(key=lambda t: t["value"])
                return self.async_create_entry(
                    data={**self._options, CONF_THRESHOLDS: thresholds}
                )
        defaults = user_input or existing or {}
        return self.async_show_form(
            step_id="threshold",
            data_schema=self._threshold_schema(defaults),
            errors=errors,
        )

    def _threshold_picker(self, *, multiple: bool) -> selector.SelectSelector:
        def label(t: Mapping[str, Any]) -> str:
            sign = "≥" if t["direction"] == ABOVE else "≤"
            return f"{t['name']} ({sign} {t['value']} cm)"

        return selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value=t["id"], label=label(t))
                    for t in self._thresholds
                ],
                multiple=multiple,
                mode=selector.SelectSelectorMode.LIST,
            )
        )

    def _threshold_schema(self, d: Mapping[str, Any]) -> vol.Schema:
        def suggested(key: str) -> dict[str, Any] | None:
            value = d.get(key)
            return None if value in (None, "") else {"suggested_value": value}

        return vol.Schema(
            {
                vol.Required("name", default=d.get("name", vol.UNDEFINED)): (
                    selector.TextSelector()
                ),
                vol.Required("value", default=d.get("value", vol.UNDEFINED)): LENGTH,
                vol.Required("direction", default=d.get("direction", ABOVE)): _select(
                    DIRECTIONS, "direction"
                ),
                vol.Required(
                    "hysteresis", default=d.get("hysteresis", DEFAULT_HYSTERESIS)
                ): POSITIVE_LENGTH,
                vol.Optional("color", description=suggested("color")): (
                    selector.ColorRGBSelector()
                ),
                vol.Required("notify", default=d.get("notify", False)): (
                    selector.BooleanSelector()
                ),
                vol.Optional("targets", default=list(d.get("targets") or [])): (
                    self._targets_selector(list(d.get("targets") or []))
                ),
                vol.Required("critical", default=d.get("critical", False)): (
                    selector.BooleanSelector()
                ),
                vol.Optional("message", description=suggested("message")): (
                    selector.TextSelector(selector.TextSelectorConfig(multiline=True))
                ),
                vol.Required(
                    "clear_message", default=d.get("clear_message", True)
                ): selector.BooleanSelector(),
                vol.Required("repeat", default=d.get("repeat", 0)): _number(
                    0, 10080, 1, "min"
                ),
            }
        )


def _default_color(data: Mapping[str, Any]) -> tuple[int, int, int]:
    return DEFAULT_ABOVE_COLOR if data.get("direction") == ABOVE else DEFAULT_BELOW_COLOR
