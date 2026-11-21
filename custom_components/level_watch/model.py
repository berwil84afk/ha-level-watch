"""Runtime model: follows the source sensor and derives the level values."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    EventStateReportedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_state_report_event,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

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
    HISTORY_HOURS,
    KIND_WATER,
    MIN_SAMPLE_SPACING,
    MODE_DISTANCE,
    MODE_LEVEL,
    QUALITY_NO_DATA,
    QUALITY_OK,
    QUALITY_STALE,
    QUALITY_UNAVAILABLE,
    STORAGE_SAVE_DELAY,
    STORAGE_VERSION,
    TICK_INTERVAL,
    UNIT_AUTO,
)

_LOGGER = logging.getLogger(__name__)

# A jump is accepted once this many readings in a row confirm it (a tank
# being refilled is a real jump, an echo off the tank wall is not).
JUMP_CONFIRMATIONS = 3
RECOMPUTE_INTERVAL = timedelta(seconds=60)


@dataclass(frozen=True, slots=True)
class Settings:
    """Every setting of one entry, with defaults filled in."""

    name: str
    source: str
    source_unit: str
    kind: str
    distance_mode: bool
    sensor_height: float | None
    offset: float
    ref_min: float
    ref_max: float | None
    trend_window: float  # seconds
    trend_deadband: float  # cm/h
    smoothing: float  # seconds
    stale_timeout: float  # seconds
    max_jump: float  # cm

    @classmethod
    def from_config(cls, conf: Mapping[str, Any]) -> Settings:
        adv = conf.get(CONF_ADVANCED) or {}

        def opt(key: str, default: float) -> float:
            value = adv.get(key, conf.get(key))
            return float(default if value is None else value)

        height = conf.get(CONF_SENSOR_HEIGHT)
        ref_max = conf.get(CONF_REF_MAX)
        return cls(
            name=conf.get(CONF_NAME) or DEFAULT_NAME,
            source=conf[CONF_SOURCE],
            source_unit=conf.get(CONF_SOURCE_UNIT) or UNIT_AUTO,
            kind=conf.get(CONF_KIND) or KIND_WATER,
            distance_mode=conf.get(CONF_MODE, MODE_LEVEL) == MODE_DISTANCE,
            sensor_height=None if height is None else float(height),
            offset=float(conf.get(CONF_OFFSET) or DEFAULT_OFFSET),
            ref_min=float(
                DEFAULT_REF_MIN if conf.get(CONF_REF_MIN) is None else conf[CONF_REF_MIN]
            ),
            ref_max=None if ref_max is None else float(ref_max),
            trend_window=opt(CONF_TREND_WINDOW, DEFAULT_TREND_WINDOW) * 60,
            trend_deadband=opt(CONF_TREND_DEADBAND, DEFAULT_TREND_DEADBAND),
            smoothing=opt(CONF_SMOOTHING, DEFAULT_SMOOTHING) * 60,
            stale_timeout=opt(CONF_STALE_TIMEOUT, DEFAULT_STALE_TIMEOUT) * 60,
            max_jump=opt(CONF_MAX_JUMP, DEFAULT_MAX_JUMP),
        )


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Derived values at one point in time."""

    level: float | None = None
    raw_level: float | None = None
    percent: float | None = None
    rate: float | None = None
    trend: str | None = None
    min_24h: float | None = None
    max_24h: float | None = None
    change_24h: float | None = None
    quality: str = QUALITY_NO_DATA
    last_reading: datetime | None = None


class LevelWatchModel:
    """Follows one source sensor and keeps the derived values current."""

    def __init__(
        self, hass: HomeAssistant, entry_id: str, conf: Mapping[str, Any]
    ) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.settings = Settings.from_config(conf)
        keep = max(HISTORY_HOURS * 3600, self.settings.trend_window) + 3600
        self.history = calc.LevelHistory(keep, MIN_SAMPLE_SPACING)
        self.snapshot = Snapshot()
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}"
        )
        self._listeners: list[Callable[[], None]] = []
        self._unsubs: list[CALLBACK_TYPE] = []
        self._source_available = False
        self._last_reading: float | None = None
        self._pending_jump: list[float] = []
        self._warned_unit = False

    # -- lifecycle -----------------------------------------------------------

    async def async_load(self) -> None:
        """Restore the history saved before the last restart."""
        data = await self._store.async_load()
        if not data:
            return
        now = dt_util.utcnow().timestamp()
        try:
            self.history.load(data.get("samples", []), now)
            self._last_reading = data.get("last_reading")
        except (TypeError, ValueError):
            _LOGGER.warning("Ignoring unreadable history of %s", self.settings.name)
            self.history.load([], now)

    @callback
    def async_start(self) -> None:
        source = self.settings.source
        self._unsubs += [
            async_track_state_change_event(self.hass, source, self._on_state_changed),
            async_track_state_report_event(self.hass, source, self._on_state_reported),
            async_track_time_interval(self.hass, self._on_tick, RECOMPUTE_INTERVAL),
        ]
        self._handle_state(self.hass.states.get(source))

    async def async_stop(self) -> None:
        while self._unsubs:
            self._unsubs.pop()()
        await self._store.async_save(self._data_to_save())

    @callback
    def async_add_listener(self, update: Callable[[], None]) -> CALLBACK_TYPE:
        self._listeners.append(update)

        @callback
        def remove() -> None:
            self._listeners.remove(update)

        return remove

    # -- input ---------------------------------------------------------------

    @callback
    def _on_state_changed(self, event: Event[EventStateChangedData]) -> None:
        self._handle_state(event.data["new_state"])

    @callback
    def _on_state_reported(self, event: Event[EventStateReportedData]) -> None:
        self._handle_state(self.hass.states.get(self.settings.source))

    @callback
    def _on_tick(self, now: datetime) -> None:
        """Recompute (staleness ages) and carry a steady value forward.

        Many sensors only send changes, so a level that holds still would leave
        no samples and the trend would hang on the last movement.
        """
        ts = now.timestamp()
        last = self.history.last
        if (
            self._source_available
            and last is not None
            and self._last_reading is not None
            and ts - self._last_reading < self.settings.stale_timeout
            and ts - last.ts >= TICK_INTERVAL
        ):
            self.history.add(ts, last.value)
        self._recompute(ts)

    @callback
    def _handle_state(self, state: State | None) -> None:
        now = dt_util.utcnow().timestamp()
        level = self._parse(state)
        if level is None:
            self._source_available = False
            self._recompute(now)
            return
        self._source_available = True
        ts = min(_reading_time(state), now) if state else now
        last = self.history.last
        if calc.is_jump(last.value if last else None, level, self.settings.max_jump):
            self._pending_jump.append(level)
            if len(self._pending_jump) < JUMP_CONFIRMATIONS or not _agree(
                self._pending_jump, self.settings.max_jump
            ):
                _LOGGER.debug("%s: ignoring jump to %.1f cm", self.settings.name, level)
                self._pending_jump = self._pending_jump[-JUMP_CONFIRMATIONS:]
                self._recompute(now)
                return
        self._pending_jump.clear()
        self.history.add(ts, level)
        self._last_reading = ts
        self._store.async_delay_save(self._data_to_save, STORAGE_SAVE_DELAY)
        self._recompute(now)

    def _parse(self, state: State | None) -> float | None:
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE, ""):
            return None
        try:
            value = float(state.state)
        except ValueError:
            return None
        unit = self.settings.source_unit
        if unit == UNIT_AUTO:
            unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        if not calc.is_length_unit(unit):
            if not self._warned_unit:
                _LOGGER.warning(
                    "%s has unit %r; set the source unit in the Level Watch options",
                    self.settings.source,
                    unit,
                )
                self._warned_unit = True
            return None
        s = self.settings
        return calc.raw_to_level(
            calc.to_cm(value, unit),
            distance_mode=s.distance_mode,
            sensor_height=s.sensor_height,
            offset=s.offset,
        )

    # -- output --------------------------------------------------------------

    @callback
    def _recompute(self, now: float) -> None:
        s = self.settings
        h = self.history
        last = h.last
        if last is None:
            quality = QUALITY_NO_DATA
        elif not self._source_available:
            quality = QUALITY_UNAVAILABLE
        elif self._last_reading is None or now - self._last_reading > s.stale_timeout:
            quality = QUALITY_STALE
        else:
            quality = QUALITY_OK

        level = calc.smoothed(h, now, s.smoothing)
        rate = calc.rate_per_hour(h, now, s.trend_window)
        stats = calc.period_stats(h, now, HISTORY_HOURS * 3600)
        self.snapshot = Snapshot(
            level=level,
            raw_level=last.value if last else None,
            percent=None if level is None else calc.percent(level, s.ref_min, s.ref_max),
            rate=rate,
            trend=calc.trend(rate, s.trend_deadband),
            min_24h=stats.minimum,
            max_24h=stats.maximum,
            change_24h=stats.change,
            quality=quality,
            last_reading=(
                dt_util.utc_from_timestamp(self._last_reading)
                if self._last_reading is not None
                else None
            ),
        )
        for update in list(self._listeners):
            update()

    def _data_to_save(self) -> dict[str, Any]:
        return {"samples": self.history.dump(), "last_reading": self._last_reading}


def _reading_time(state: State) -> float:
    """When the source last reported, even if the value did not change."""
    reported = getattr(state, "last_reported", None) or state.last_updated
    return reported.timestamp()


def _agree(values: list[float], max_jump: float) -> bool:
    """True if the pending readings are close to each other."""
    recent = values[-JUMP_CONFIRMATIONS:]
    return max(recent) - min(recent) <= max_jump
