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

from . import calc, messaging, tank
from .const import (
    CONF_ADVANCED,
    CONF_CONSUMPTION_WINDOW,
    CONF_DIAMETER,
    CONF_KIND,
    CONF_LENGTH,
    CONF_LEVEL_UNIT,
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
    EVENT_THRESHOLD,
    HISTORY_HOURS,
    KIND_TANK,
    KIND_WATER,
    LONG_HISTORY_POINTS,
    MIN_CONSUMPTION_SPAN,
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
    UNIT_CM,
    UNIT_KG,
    UNIT_PERCENT,
)
from .thresholds import (
    Threshold,
    format_message,
    load_thresholds,
    next_threshold,
    stage,
    texts,
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
    thresholds: tuple[Threshold, ...] = ()
    level_unit: str = UNIT_CM  # cm; % for a percentage source; kg for a weight
    tank: tank.TankShape | None = None  # only for a tank with a known shape
    # Shape the card draws; set for a tank in % too, which has no volume.
    display_shape: str | None = None
    consumption_window: float = DEFAULT_CONSUMPTION_WINDOW * 86400  # seconds
    refill_jump: float = DEFAULT_REFILL_JUMP  # cm

    @classmethod
    def from_config(cls, conf: Mapping[str, Any]) -> Settings:
        adv = conf.get(CONF_ADVANCED) or {}

        def opt(key: str, default: float) -> float:
            value = adv.get(key, conf.get(key))
            return float(default if value is None else value)

        height = conf.get(CONF_SENSOR_HEIGHT)
        tank_conf = conf.get(CONF_TANK) or {}

        def dim(key: str) -> float | None:
            value = tank_conf.get(key)
            return None if value in (None, "", 0) else float(value)

        shape = tank.TankShape(
            shape=tank_conf.get(CONF_SHAPE) or tank.NONE,
            diameter=dim(CONF_DIAMETER),
            length=dim(CONF_LENGTH),
            width=dim(CONF_WIDTH),
        )
        kind = conf.get(CONF_KIND) or KIND_WATER
        unit = conf.get(CONF_LEVEL_UNIT) or UNIT_CM
        ref_max = conf.get(CONF_REF_MAX)
        if unit == UNIT_PERCENT and ref_max is None:
            ref_max = 100.0  # a percentage runs to 100 unless told otherwise
        return cls(
            name=conf.get(CONF_NAME) or DEFAULT_NAME,
            source=conf[CONF_SOURCE],
            source_unit=calc.normalize_unit(conf.get(CONF_SOURCE_UNIT)) or UNIT_AUTO,
            kind=kind,
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
            thresholds=tuple(load_thresholds(conf.get(CONF_THRESHOLDS))),
            level_unit=unit,
            display_shape=(
                shape.shape if kind == KIND_TANK and shape.shape != tank.NONE else None
            ),
            # No volume for a source in %: the shape would have nothing to measure.
            tank=shape if kind == KIND_TANK and shape.defined and unit == UNIT_CM else None,
            consumption_window=opt(CONF_CONSUMPTION_WINDOW, DEFAULT_CONSUMPTION_WINDOW)
            * 86400,
            refill_jump=opt(CONF_REFILL_JUMP, DEFAULT_REFILL_JUMP),
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
    stage: Threshold | None = None
    active: Mapping[str, bool] | None = None
    next_threshold: Threshold | None = None
    hours_to_next: float | None = None
    # Tank values
    volume: float | None = None
    capacity: float | None = None
    free_volume: float | None = None
    consumption: float | None = None
    days_left: float | None = None
    hours_to_full: float | None = None
    last_refill: datetime | None = None
    # Why there is no range yet: "collecting" (until consumption_ready) or "no_use".
    consumption_status: str | None = None
    consumption_ready: datetime | None = None


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
        # Smoothed levels over days for the consumption, thinned to a fixed size.
        window = self.settings.consumption_window
        self.long = calc.LevelHistory(window, max(300.0, window / LONG_HISTORY_POINTS))
        self._last_refill: float | None = None
        self.snapshot = Snapshot()
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}"
        )
        self._listeners: list[Callable[[], None]] = []
        # Filled by the entities; used to remove entities of deleted thresholds.
        self.unique_ids: set[str] = set()
        self._unsubs: list[CALLBACK_TYPE] = []
        self._source_available = False
        self._last_reading: float | None = None
        self._pending_jump: list[float] = []
        self._warned_unit = False
        # Threshold state survives restarts so nothing is announced twice.
        self._active: dict[str, bool] = {}
        self._last_sent: dict[str, float] = {}

    # -- lifecycle -----------------------------------------------------------

    async def async_load(self) -> None:
        """Restore the history saved before the last restart."""
        data = await self._store.async_load()
        if not data:
            return
        now = dt_util.utcnow().timestamp()
        try:
            self.history.load(data.get("samples", []), now)
            self.long.load(data.get("long", []), now)
            self._last_refill = data.get("last_refill")
            self._last_reading = data.get("last_reading")
            known = {t.id for t in self.settings.thresholds}
            self._active = {
                k: bool(v) for k, v in (data.get("active") or {}).items() if k in known
            }
            self._last_sent = {
                k: float(v) for k, v in (data.get("last_sent") or {}).items() if k in known
            }
        except (TypeError, ValueError):
            _LOGGER.warning("Ignoring unreadable history of %s", self.settings.name)
            self.history.load([], now)
            self.long.load([], now)

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
            self._track_long(ts)
        self._recompute(ts)
        self._repeat_messages(ts)

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
        self._track_long(ts)
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
        s = self.settings
        if s.level_unit == UNIT_PERCENT:
            # The entry was set up for %, so only % (or a missing unit) fits.
            if unit not in (UNIT_PERCENT, None, ""):
                self._warn_unit(unit)
                return None
            return value + s.offset
        if s.level_unit == UNIT_KG:
            # A weight, e.g. the salt stock of a water softener; kept in kg.
            if unit in (None, ""):
                return value + s.offset
            if not calc.is_mass_unit(unit):
                self._warn_unit(unit)
                return None
            return calc.to_kg(value, unit) + s.offset
        if not calc.is_length_unit(unit):
            self._warn_unit(unit)
            return None
        return calc.raw_to_level(
            calc.to_cm(value, unit),
            distance_mode=s.distance_mode,
            sensor_height=s.sensor_height,
            offset=s.offset,
        )

    def _warn_unit(self, unit: str | None) -> None:
        """Log an unusable source unit once, not on every reading."""
        if not self._warned_unit:
            _LOGGER.warning(
                "%s has unit %r; set the source unit in the Level Watch options",
                self.settings.source,
                unit,
            )
            self._warned_unit = True

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
        trend = calc.trend(rate, s.trend_deadband)
        stats = calc.period_stats(h, now, HISTORY_HOURS * 3600)
        if level is not None and quality == QUALITY_OK:
            self._evaluate_thresholds(now, level, trend, rate)
        upcoming = None
        hours = None
        if level is not None and trend in (calc.RISING, calc.FALLING):
            upcoming = next_threshold(s.thresholds, self._active, level, rate)
            if upcoming is not None and rate:
                hours = (upcoming.value - level) / rate
        self.snapshot = Snapshot(
            level=level,
            raw_level=last.value if last else None,
            percent=None if level is None else self._percent(level),
            rate=rate,
            trend=trend,
            min_24h=stats.minimum,
            max_24h=stats.maximum,
            change_24h=stats.change,
            quality=quality,
            last_reading=(
                dt_util.utc_from_timestamp(self._last_reading)
                if self._last_reading is not None
                else None
            ),
            stage=stage(s.thresholds, self._active),
            active=dict(self._active),
            next_threshold=upcoming,
            hours_to_next=hours,
            **self._tank_values(now, level, rate if trend == calc.RISING else None),
        )
        for update in list(self._listeners):
            update()

    def _data_to_save(self) -> dict[str, Any]:
        return {
            "samples": self.history.dump(),
            "last_reading": self._last_reading,
            "active": self._active,
            "last_sent": self._last_sent,
            "long": self.long.dump(),
            "last_refill": self._last_refill,
        }

    # -- tank ----------------------------------------------------------------

    @callback
    def _track_long(self, ts: float) -> None:
        """Feed the smoothed level into the long history; spot refills."""
        level = calc.smoothed(self.history, ts, self.settings.smoothing)
        if level is None:
            return
        if tank.is_refill(self.long, ts, level, self.settings.refill_jump):
            # The consumption starts over after a delivery or a rain shower.
            _LOGGER.debug("%s: refill detected at %.1f cm", self.settings.name, level)
            self.long.load([], ts)
            self._last_refill = ts
        self.long.add(ts, level)

    def _percent(self, level: float) -> float | None:
        s = self.settings
        if s.level_unit == UNIT_PERCENT:
            return None  # the level already is the percentage
        if s.tank is not None:
            return tank.volume_percent(s.tank, level, s.ref_min, s.ref_max)
        return calc.percent(level, s.ref_min, s.ref_max)

    def _tank_values(
        self, now: float, level: float | None, rising_rate: float | None
    ) -> dict[str, Any]:
        s = self.settings
        if s.kind != KIND_TANK or level is None:
            return {}
        values: dict[str, Any] = {
            "hours_to_full": tank.hours_to_full(level, s.ref_max, rising_rate),
            "last_refill": (
                dt_util.utc_from_timestamp(self._last_refill)
                if self._last_refill is not None
                else None
            ),
        }
        if s.level_unit != UNIT_CM:
            # % and kg: consumption and range in the level's own unit.
            consumption = tank.consumption_per_day(
                tank.LINEAR,
                self.long,
                now,
                s.consumption_window,
                min(MIN_CONSUMPTION_SPAN, s.consumption_window / 2),
            )
            days = tank.days_left(tank.LINEAR, level, s.ref_min, consumption)
            values.update(
                consumption=consumption,
                days_left=days,
                **self._consumption_status(now, consumption, days),
            )
            return values
        shape = s.tank
        if shape is None:
            return values
        volume = shape.volume(level)
        cap = tank.capacity(shape, s.ref_max)
        consumption = tank.consumption_per_day(
            shape,
            self.long,
            now,
            s.consumption_window,
            min(MIN_CONSUMPTION_SPAN, s.consumption_window / 2),
        )
        values.update(
            volume=volume,
            capacity=cap,
            free_volume=None if cap is None else max(0.0, cap - volume),
            consumption=consumption,
            days_left=tank.days_left(shape, level, s.ref_min, consumption),
        )
        values.update(self._consumption_status(now, consumption, values["days_left"]))
        return values

    def _consumption_status(
        self, now: float, consumption: float | None, days_left: float | None
    ) -> dict[str, Any]:
        """Tell the card why the range is missing and when it can appear."""
        if consumption is None:
            window = self.settings.consumption_window
            samples = self.long.since(now - window)
            start = samples[0].ts if samples else now
            ready = max(now, start + min(MIN_CONSUMPTION_SPAN, window / 2))
            return {
                "consumption_status": "collecting",
                "consumption_ready": dt_util.utc_from_timestamp(ready),
            }
        if days_left is None:
            return {"consumption_status": "no_use"}
        return {"consumption_status": "ok"}

    # -- thresholds ----------------------------------------------------------

    @callback
    def _evaluate_thresholds(
        self, now: float, level: float, trend: str | None, rate: float | None
    ) -> None:
        changed = False
        for th in self.settings.thresholds:
            was = self._active.get(th.id)
            active = th.is_active(level, bool(was))
            if was is not None and active == was:
                continue
            self._active[th.id] = active
            changed = True
            if was is None and not active:
                continue  # first look at a new threshold, nothing to report
            self.hass.bus.async_fire(
                EVENT_THRESHOLD,
                {
                    "entry_id": self.entry_id,
                    "name": self.settings.name,
                    "threshold_id": th.id,
                    "threshold": th.name,
                    "direction": th.direction,
                    "value": th.value,
                    "active": active,
                    "level": round(level, 2),
                },
            )
            if th.notify and (active or th.clear_message):
                self._send(th, now, level, trend, rate, cleared=not active)
        if changed:
            self._store.async_delay_save(self._data_to_save, 1)

    @callback
    def _repeat_messages(self, now: float) -> None:
        snap = self.snapshot
        if snap.level is None or snap.quality != QUALITY_OK:
            return
        for th in self.settings.thresholds:
            if not (th.notify and th.repeat > 0 and self._active.get(th.id)):
                continue
            if now - self._last_sent.get(th.id, 0) >= th.repeat * 60:
                self._send(th, now, snap.level, snap.trend, snap.rate, cleared=False)
                self._store.async_delay_save(self._data_to_save, 1)

    @callback
    def _send(
        self,
        th: Threshold,
        now: float,
        level: float,
        trend: str | None,
        rate: float | None,
        *,
        cleared: bool,
    ) -> None:
        message = format_message(
            th.message,
            language=self.hass.config.language,
            name=self.settings.name,
            threshold=th,
            level=level,
            trend=trend,
            rate=rate,
            cleared=cleared,
            unit=self.settings.level_unit,
        )
        self._last_sent[th.id] = now
        self.hass.async_create_task(
            messaging.async_send(
                self.hass,
                th.targets,
                title=self.settings.name,
                message=message,
                tag=f"{DOMAIN}_{self.entry_id}_{th.id}",
                critical=th.critical,
                cleared=cleared,
            ),
            eager_start=True,
        )


    async def async_send_test(self, th: Threshold) -> dict[str, Any]:
        """Send the threshold's message once, marked as a test.

        Uses the current level (or the threshold value if there is none yet) and
        changes no state: no event, no repeat timer, no active flag.
        """
        snap = self.snapshot
        message = format_message(
            th.message,
            language=self.hass.config.language,
            name=self.settings.name,
            threshold=th,
            level=snap.level if snap.level is not None else th.value,
            trend=snap.trend,
            rate=snap.rate,
            unit=self.settings.level_unit,
        )
        prefix = texts(self.hass.config.language)["test"]
        failed = await messaging.async_send(
            self.hass,
            th.targets,
            title=self.settings.name,
            message=f"{prefix}: {message}",
            tag=f"{DOMAIN}_{self.entry_id}_{th.id}_test",
            critical=th.critical,
            cleared=False,
        )
        return {
            "message": f"{prefix}: {message}",
            "sent": len(th.targets) - len(failed),
            "failed": [{"target": target, "error": error} for target, error in failed],
        }


def _reading_time(state: State) -> float:
    """When the source last reported, even if the value did not change."""
    reported = getattr(state, "last_reported", None) or state.last_updated
    return reported.timestamp()


def _agree(values: list[float], max_jump: float) -> bool:
    """True if the pending readings are close to each other."""
    recent = values[-JUMP_CONFIRMATIONS:]
    return max(recent) - min(recent) <= max_jump
