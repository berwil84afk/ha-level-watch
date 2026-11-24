"""Constants for Level Watch."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "level_watch"
VERSION: Final = "0.10.0"
CARD_URL: Final = "/level_watch/level-watch-card.js"

# Basic settings
CONF_NAME: Final = "name"
CONF_SOURCE: Final = "source_entity"
CONF_SOURCE_UNIT: Final = "source_unit"
# Unit every level value is kept in: cm, or % for a source that reports %.
CONF_LEVEL_UNIT: Final = "level_unit"
CONF_KIND: Final = "kind"
CONF_MODE: Final = "measurement_mode"
CONF_SENSOR_HEIGHT: Final = "sensor_height"
CONF_OFFSET: Final = "offset"
CONF_REF_MIN: Final = "reference_min"
CONF_REF_MAX: Final = "reference_max"

CONF_THRESHOLDS: Final = "thresholds"
EVENT_THRESHOLD: Final = "level_watch_threshold"

# Advanced settings (options flow section)
CONF_ADVANCED: Final = "advanced"
CONF_TREND_WINDOW: Final = "trend_window"
CONF_TREND_DEADBAND: Final = "trend_deadband"
CONF_SMOOTHING: Final = "smoothing"
CONF_STALE_TIMEOUT: Final = "stale_timeout"
CONF_MAX_JUMP: Final = "max_jump"
CONF_CONSUMPTION_WINDOW: Final = "consumption_window"
CONF_REFILL_JUMP: Final = "refill_jump"

# Tank section
CONF_TANK: Final = "tank"
CONF_SHAPE: Final = "shape"
CONF_DIAMETER: Final = "diameter"
CONF_LENGTH: Final = "length"
CONF_WIDTH: Final = "width"

KIND_WATER: Final = "water"
KIND_TANK: Final = "tank"
KINDS: Final = [KIND_WATER, KIND_TANK]

MODE_LEVEL: Final = "level"
MODE_DISTANCE: Final = "distance"
MODES: Final = [MODE_LEVEL, MODE_DISTANCE]

UNIT_AUTO: Final = "auto"
UNIT_PERCENT: Final = "%"
# Translation keys may not contain "%", so the option is called "percent".
SOURCE_UNIT_PERCENT: Final = "percent"
UNIT_KG: Final = "kg"
SOURCE_UNITS: Final = [UNIT_AUTO, "mm", "cm", "m", "in", "ft", SOURCE_UNIT_PERCENT, "g", "kg", "lb"]

DEFAULT_NAME: Final = "Pegel"
DEFAULT_OFFSET: Final = 0.0
DEFAULT_REF_MIN: Final = 0.0
DEFAULT_TREND_WINDOW: Final = 60  # minutes
DEFAULT_TREND_DEADBAND: Final = 1.0  # cm/h
DEFAULT_SMOOTHING: Final = 5  # minutes, 0 = off
DEFAULT_STALE_TIMEOUT: Final = 60  # minutes
DEFAULT_MAX_JUMP: Final = 0.0  # cm, 0 = off
DEFAULT_CONSUMPTION_WINDOW: Final = 7  # days
DEFAULT_REFILL_JUMP: Final = 5.0  # cm
# The consumption needs data over at least this long (or half the window).
MIN_CONSUMPTION_SPAN: Final = 12 * 3600
# The long history keeps about this many samples whatever the window.
LONG_HISTORY_POINTS: Final = 1000

# Internal unit for every level value.
UNIT_CM: Final = "cm"
UNIT_RATE: Final = "cm/h"

# History handling
HISTORY_HOURS: Final = 24
MIN_SAMPLE_SPACING: Final = 10  # seconds; closer samples replace the previous one
TICK_INTERVAL: Final = 300  # seconds; carry the last value forward this often
STORAGE_VERSION: Final = 1
STORAGE_SAVE_DELAY: Final = 300  # seconds

QUALITY_OK: Final = "ok"
QUALITY_STALE: Final = "stale"
QUALITY_UNAVAILABLE: Final = "unavailable"
QUALITY_NO_DATA: Final = "no_data"
QUALITIES: Final = [QUALITY_OK, QUALITY_STALE, QUALITY_UNAVAILABLE, QUALITY_NO_DATA]

TREND_RISING: Final = "rising"
TREND_FALLING: Final = "falling"
TREND_STABLE: Final = "stable"
TRENDS: Final = [TREND_RISING, TREND_FALLING, TREND_STABLE]
