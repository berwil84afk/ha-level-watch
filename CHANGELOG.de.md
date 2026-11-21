# Änderungsprotokoll

[English](CHANGELOG.md) · **Deutsch**

Alle wichtigen Änderungen an Level Watch. Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), die Versionsnummern folgen [Semantic Versioning](https://semver.org/lang/de/).

Die Versionen 0.1.0 bis 0.5.0 waren Entwicklungsschritte ohne GitHub-Release. Die erste Version, die du über HACS installieren kannst, ist 0.6.0.

## [0.7.6] - 2026-11-21

### Neu
- README auf Englisch (`README.md`) und Deutsch (`README.de.md`), mit Screenshots in beiden Sprachen.
- Dieses Änderungsprotokoll auf Englisch und Deutsch.

### Behoben
- Karte: „in 6 Tagen“ statt des falschen „in 6 Tage“.
- Deutsche Oberfläche: Zusammengesetzte Wörter folgen jetzt dem Duden (zum Beispiel *Stabilbereich* statt *Stabil-Bereich*).

## [0.7.5] - 2026-11-21

### Geändert
- Karte: Die Wasseroberfläche bewegt sich deutlicher. Hinten läuft eine ruhige Dünung, vorne eine schnellere Welle mit heller Schaumkrone, beide gegenläufig. Ist im System „Bewegung reduzieren“ eingeschaltet, bleiben die Wellen still.

## [0.7.4] - 2026-11-21

### Neu
- Icon für die Integration. Home Assistant zeigt es ab Version 2026 unter *Einstellungen → Geräte & Dienste*.

## [0.7.3] - 2026-11-21

### Behoben
- Karte: Der Inhalt läuft nicht mehr in die Karte darunter. Das Dashboard richtet die Höhe der Karte nach ihrem Inhalt, und was trotzdem nicht passt, wird abgeschnitten.
- Tank mit Sensor in %: Die eingestellte Form wird wieder angezeigt. Beim liegenden Zylinder wird der Prozentwert in der passenden Füllhöhe gezeichnet.

## [0.7.2] - 2026-11-21

### Neu
- Karte: Schwellenlinien in Pegellatte, Tank, Verlauf und Ring zeigen einen Tooltip mit Name, Richtung, Wert und ob die Schwelle erreicht ist. Die Wasseroberfläche zeigt den aktuellen Pegel.

## [0.7.1] - 2026-11-21

### Neu
- Karte: Schalter *Verlauf anzeigen* im Karteneditor.
- Karte: Der Tank im klassischen Stil hat eine Skala in seiner Einheit (cm oder %).

### Behoben
- Karte: Ein leeres Feld *Verlauf (Stunden)* bedeutet nicht mehr stillschweigend 24 Stunden.

## [0.7.0] - 2026-11-21

### Neu
- Quellsensoren in %. Pegel, Bezüge, Schwellen, Rate (%/h), Meldungen und die Karte arbeiten dann in %. Tanks bekommen den Verbrauch in % pro Tag und die Reichweite in Tagen.

## [0.6.1] - 2026-11-21

### Neu
- Karte: Fährst du mit der Maus über eine Zone im Zonenbalken, siehst du Name und Bereich der Stufe.

### Behoben
- Karte: Die Zonenfarben bleiben im Dunkelmodus kräftig. Statt die anderen Zonen abzudunkeln, ist die Zone mit dem aktuellen Pegel höher dargestellt.

## [0.6.0] - 2026-11-21

### Neu
- Vorlagen für Schwellen: Flusspegel (Niedrigwasser, Meldestufe 1 bis 4) und Tank (fast leer, Reserve, voll).
- Schwelleneditor in der Karte für Admins, mit Vorschau des Zonenbalkens.

## [0.5.0] - 2026-11-21

### Neu
- Kartenstile: `forecast` (neuer Standard mit Zonenbalken und Prognosediagramm), `classic`, `ring` und `compact`.

## [0.4.0] - 2026-11-21

### Neu
- Dashboard-Karte für Wasserpegel und Tanks. Die Integration bringt sie selbst mit, eine Ressource ist nicht nötig.

## [0.3.0] - 2026-11-21

### Neu
- Tanks: Form (stehender Zylinder, liegender Zylinder, Quader) und Innenmaße.
- Sensoren für Volumen, freies Volumen, Verbrauch pro Tag, Reichweite, Zeit bis voll und letztes Nachtanken.

## [0.2.0] - 2026-11-21

### Neu
- Schwellen nach oben und unten, mit Hysterese und Farbe.
- Meldungen über die Companion App (auf Wunsch kritisch), dauerhafte Meldungen oder jeden anderen Benachrichtigungsdienst, mit Entwarnung und Wiederholung.
- Sensoren für Stufe, nächste Schwelle und Zeit bis zur nächsten Schwelle, ein Binärsensor je Schwelle und das Ereignis `level_watch_threshold`.

## [0.1.0] - 2026-11-21

### Neu
- Erste Version: Pegel, Tendenz, Änderungsrate, Minimum, Maximum und Änderung über 24 Stunden sowie Datenqualität aus jedem Längensensor.

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
