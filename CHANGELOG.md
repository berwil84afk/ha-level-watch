# Changelog

**English** · [Deutsch](CHANGELOG.de.md)

All notable changes to Level Watch. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

Versions 0.1.0 to 0.5.0 were development steps without a GitHub release. The first release you can install through HACS is 0.6.0.

## [0.12.0] - 2026-11-24

### Added
- Volume sensors in L, m³ or gal (also mL and ft³ with *Automatic*), for example a tank sensor that already reports litres. The level is kept in litres, the rate in L/h, and tanks get consumption in litres per day, the range in days and refill detection. With *Reference top* the fill level is shown in %. No tank shape is needed.
- Card: for litres the big value shows the content, with "61 % of 1,500 L" beside it.

### Changed
- Notifications have the title "Level Watch reports: <name>" (in German "Level Watch meldet: <name>"), so you can see at once where a message comes from.

## [0.11.1] - 2026-11-24

### Fixed
- Card (compact style): admins now see the pencil that opens the threshold editor, like in the other styles.

## [0.11.0] - 2026-11-24

### Added
- Card (compact style): thresholds appear as coloured marks beside the bar, with name and value on hover.
- Card (compact style): the hint line always explains something. If there is no forecast, it says why, for example "Range from tomorrow 04:07" while consumption data is still being collected, "No consumption seen yet", or how far the nearest threshold is ("11 kg to Refill salt").
- Level sensor: new attributes `consumption_status` and `consumption_ready` tell when the range of a tank can appear.

### Changed
- Card (compact style): the hint names the time first ("In 15 days: Refill salt") and may use two lines instead of being cut off.
- Sensors *Rate of change* and *Fill level* have their own icons instead of the default eye.

## [0.10.0] - 2026-11-24

### Added
- Card: *Send test* in the threshold editor sends the message of a threshold once to the chosen targets, marked as a test and with the current level. It works before saving and shows which targets failed.
- Action `level_watch.send_test` for the same in automations or the developer tools. Without a threshold name it tests every threshold that sends notifications.

### Changed
- Card: the notify targets in the threshold editor are grouped (Home Assistant, Companion app, notify entities, other services), with readable names, a search field and the chosen targets as chips at the top.
- Setup: the help for *Reference top* explains that for a tank you should enter the maximum fill level, so the fill level, the scale and the tank drawing are right.

## [0.9.0] - 2026-11-24

### Added
- Weight sensors in g, kg or lb, for example the salt stock of a water softener. The level is kept in kg, the rate in kg/h, and tanks get consumption in kg per day, the range in days and refill detection. With *Reference top* the fill level is shown in %.
- Card: for weights the container is filled with still granules instead of moving water, in a grey blue that suits salt.
- Card: new option `fill` (`auto`, `water`, `granules`) to choose the fill yourself, for example granules for pellets measured in cm.
- Card: new option `color` sets the fill colour while no threshold is active. Active thresholds keep their own colour.

### Changed
- Advanced settings: *Stable range* and *Refill detection* no longer show a fixed unit, because they use the unit of the level (cm, % or kg).
- Setup: *Distance from above* now explains that it needs a sensor that measures a length.

## [0.8.1] - 2026-11-23

### Changed
- Card (classic style): the history at the bottom is now the same chart as in the forecast style, scaled to the readings and with values on hover or tap.
- Card (classic style): the gauge is tidier. Thresholds show as coloured marks on the staff and as faint lines in the basin, and the current level is a bar on the staff instead of a line across the water.

## [0.8.0] - 2026-11-23

### Added
- Card (forecast style): hover over the chart, or tap it on a phone, to see the time, the value and the stage at that moment. To the right of "now" the tooltip shows the forecast.
- Card (forecast style): thresholds outside the chart appear as a hint at the edge, for example "↑ Second meadow flooded · 260 cm".

### Changed
- Card (forecast style): the chart is scaled to the readings, so the curve uses the full height. Only thresholds close to the readings, or the one the forecast reaches, are drawn as lines.
- Card (forecast style): threshold names no longer overlap. When two lines are too close, only one is labelled; the tooltip still names every line.
- Card (forecast style): the chart keeps its proportions instead of being stretched, so the labels are no longer distorted.

## [0.7.8] - 2026-11-21

### Added
- HACS validation in the repository workflow, as preparation for the HACS default repositories.

## [0.7.7] - 2026-11-21

### Changed
- Card: the waves now always move, even when "reduce motion" is switched on in the system (for example with Windows animation effects off).

### Fixed
- Card: the wave animation no longer starts over with every new reading. It carries on smoothly, also with sensors that report very often.

## [0.7.6] - 2026-11-21

### Added
- README in English (`README.md`) and German (`README.de.md`), with screenshots in both languages.
- This changelog in English and German.

### Fixed
- Card (German): "in 6 Tagen" instead of the wrong "in 6 Tage".
- German interface: compound words now follow the Duden (for example *Stabilbereich* instead of *Stabil-Bereich*).

## [0.7.5] - 2026-11-21

### Changed
- Card: the water surface moves more clearly. A slow swell runs behind a quicker wave with a light crest, in opposite directions. With "reduce motion" switched on in the system, the waves stay still.

## [0.7.4] - 2026-11-21

### Added
- Integration icon. Home Assistant 2026 and later shows it under *Settings → Devices & services*.

## [0.7.3] - 2026-11-21

### Fixed
- Card: the content no longer runs into the card below. The card lets the dashboard size it to its content and clips anything that still does not fit.
- Tank with a sensor in %: the configured shape is shown again. For a horizontal cylinder, the percentage is drawn at the matching fill height.

## [0.7.2] - 2026-11-21

### Added
- Card: threshold lines in the gauge, the tank, the history and the ring show a tooltip with name, direction, value and whether the threshold is reached. The water surface shows the current level.

## [0.7.1] - 2026-11-21

### Added
- Card: switch *Show history* in the card editor.
- Card: the classic tank has a scale in its unit (cm or %).

### Fixed
- Card: an empty *History (hours)* field no longer silently means 24 hours.

## [0.7.0] - 2026-11-21

### Added
- Source sensors in %. Level, references, thresholds, rate (%/h), messages and the card then all work in %. Tanks get consumption in % per day and the range in days.

## [0.6.1] - 2026-11-21

### Added
- Card: hovering a zone in the zone bar shows its stage name and range.

### Fixed
- Card: zone colours stay bright on dark themes. The zone holding the current level is drawn taller instead of dimming the others.

## [0.6.0] - 2026-11-21

### Added
- Threshold templates: river gauge (low water, warning levels 1 to 4) and tank (almost empty, reserve, full).
- Threshold editor in the card for admins, with a live preview of the zone bar.

## [0.5.0] - 2026-11-21

### Added
- Card styles: `forecast` (new default with zone bar and forecast chart), `classic`, `ring` and `compact`.

## [0.4.0] - 2026-11-21

### Added
- Dashboard card for water levels and tanks. The integration installs it, no resource needed.

## [0.3.0] - 2026-11-21

### Added
- Tanks: shape (vertical cylinder, horizontal cylinder, box) and inner dimensions.
- Sensors for volume, free volume, consumption per day, range, time to full and last refill.

## [0.2.0] - 2026-11-21

### Added
- Thresholds upwards and downwards, with hysteresis and colour.
- Notifications through the Companion app (optionally critical), persistent notifications or any notify service, with all-clear and repeat.
- Sensors for stage, next threshold and time to the next threshold, one binary sensor per threshold, and the event `level_watch_threshold`.

## [0.1.0] - 2026-11-21

### Added
- First version: level, trend, rate of change, minimum, maximum and change over 24 hours, and data quality from any length sensor.

[0.8.1]: https://github.com/berwil84afk/ha-level-watch/releases/tag/v0.8.1
[0.8.0]: https://github.com/berwil84afk/ha-level-watch/releases/tag/v0.8.0
[0.7.8]: https://github.com/berwil84afk/ha-level-watch/releases/tag/v0.7.8
[0.7.7]: https://github.com/berwil84afk/ha-level-watch/releases/tag/v0.7.7
[0.7.6]: https://github.com/berwil84afk/ha-level-watch/releases/tag/v0.7.6
[0.7.5]: https://github.com/berwil84afk/ha-level-watch/releases/tag/v0.7.5
[0.7.4]: https://github.com/berwil84afk/ha-level-watch/releases/tag/v0.7.4
[0.7.3]: https://github.com/berwil84afk/ha-level-watch/releases/tag/v0.7.3
[0.7.2]: https://github.com/berwil84afk/ha-level-watch/releases/tag/v0.7.2
[0.7.1]: https://github.com/berwil84afk/ha-level-watch/releases/tag/v0.7.1
[0.7.0]: https://github.com/berwil84afk/ha-level-watch/releases/tag/v0.7.0
[0.6.1]: https://github.com/berwil84afk/ha-level-watch/releases/tag/v0.6.1
[0.6.0]: https://github.com/berwil84afk/ha-level-watch/releases/tag/v0.6.0
[0.5.0]: https://github.com/berwil84afk/ha-level-watch/commit/72a5919
[0.4.0]: https://github.com/berwil84afk/ha-level-watch/commit/7dca1c2
[0.3.0]: https://github.com/berwil84afk/ha-level-watch/commit/1dfb7f8
[0.2.0]: https://github.com/berwil84afk/ha-level-watch/commit/0816894
[0.1.0]: https://github.com/berwil84afk/ha-level-watch/commit/22aec11
