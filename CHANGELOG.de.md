# Änderungsprotokoll

[English](CHANGELOG.md) · **Deutsch**

Alle wichtigen Änderungen an Level Watch. Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), die Versionsnummern folgen [Semantic Versioning](https://semver.org/lang/de/).

Die Versionen 0.1.0 bis 0.5.0 waren Entwicklungsschritte ohne GitHub-Release. Die erste Version, die du über HACS installieren kannst, ist 0.6.0.

## [0.12.1] - 2026-11-24

### Geändert
- Telegram: Der Titel einer Meldung ist jetzt fett. Telegram zeigt den Titel als normale erste Zeile, deshalb zeichnet Level Watch ihn im Parse-Modus deines Bots aus (Markdown, MarkdownV2 oder HTML). Andere Dienste bekommen den Titel unverändert.

## [0.12.0] - 2026-11-24

### Neu
- Volumensensoren in L, m³ oder gal (mit *Automatisch* auch mL und ft³), zum Beispiel ein Tanksensor, der schon Liter meldet. Der Pegel wird in Litern geführt, die Rate in L/h, und Tanks bekommen den Verbrauch in Litern pro Tag, die Reichweite in Tagen und das Erkennen von Nachtanken. Mit *Bezug oben* wird der Füllstand in % angezeigt. Eine Tankform ist nicht nötig.
- Karte: Bei Litern zeigt der große Wert den Inhalt, daneben „61 % von 1.500 L“.

### Geändert
- Meldungen haben den Titel „Level Watch meldet: <Name>“ (auf Englisch „Level Watch reports: <name>“). So siehst du sofort, woher eine Meldung kommt.

## [0.11.1] - 2026-11-24

### Behoben
- Karte (Stil Kompakt): Admins sehen jetzt den Stift, der den Schwelleneditor öffnet, wie in den anderen Stilen.

## [0.11.0] - 2026-11-24

### Neu
- Karte (Stil Kompakt): Schwellen erscheinen als farbige Marken neben dem Balken, mit Name und Wert bei Mouseover.
- Karte (Stil Kompakt): Die Hinweiszeile erklärt immer etwas. Gibt es keine Prognose, steht dort warum, zum Beispiel „Reichweite ab morgen 04:07“, solange noch Daten für den Verbrauch gesammelt werden, „Noch kein Verbrauch erkannt“ oder wie weit die nächste Schwelle entfernt ist („11 kg bis Salz nachfüllen“).
- Pegelsensor: Die neuen Attribute `consumption_status` und `consumption_ready` sagen, wann die Reichweite eines Tanks erscheinen kann.

### Geändert
- Karte (Stil Kompakt): Der Hinweis nennt zuerst die Zeit („In 15 Tagen: Salz nachfüllen“) und darf zwei Zeilen nutzen, statt abgeschnitten zu werden.
- Die Sensoren *Änderungsrate* und *Füllstand* haben eigene Icons statt des Standard-Auges.

## [0.10.0] - 2026-11-24

### Neu
- Karte: *Test senden* im Schwelleneditor schickt die Meldung einer Schwelle einmal an die gewählten Ziele, als Test markiert und mit dem aktuellen Pegel. Das geht auch vor dem Speichern, und du siehst, welche Ziele fehlgeschlagen sind.
- Aktion `level_watch.send_test` für dasselbe in Automationen oder in den Entwicklerwerkzeugen. Ohne Namen einer Schwelle werden alle Schwellen mit Meldung getestet.

### Geändert
- Karte: Die Meldeziele im Schwelleneditor sind gruppiert (Home Assistant, Companion App, Benachrichtigungs-Entitäten, weitere Dienste), mit lesbaren Namen, Suchfeld und den gewählten Zielen als Chips oben.
- Einrichtung: Die Hilfe zu *Bezug oben* erklärt, dass du beim Tank den maximalen Füllstand eintragen sollst, damit Füllstand, Skala und Tankgrafik stimmen.

## [0.9.0] - 2026-11-24

### Neu
- Gewichtssensoren in g, kg oder lb, zum Beispiel für den Salzvorrat einer Enthärtungsanlage. Der Pegel wird in kg geführt, die Rate in kg/h, und Tanks bekommen den Verbrauch in kg pro Tag, die Reichweite in Tagen und das Erkennen von Nachfüllen. Mit *Bezug oben* wird der Füllstand in % angezeigt.
- Karte: Bei Gewichten ist der Behälter mit ruhigen Körnern statt bewegtem Wasser gefüllt, in einem Graublau, das zu Salz passt.
- Karte: Neue Option `fill` (`auto`, `water`, `granules`), um die Füllung selbst zu wählen, zum Beispiel Körner für Pellets, die in cm gemessen werden.
- Karte: Neue Option `color` legt die Füllfarbe fest, solange keine Schwelle aktiv ist. Aktive Schwellen behalten ihre eigene Farbe.

### Geändert
- Erweiterte Einstellungen: *Stabilbereich* und *Nachtanken erkennen ab* zeigen keine feste Einheit mehr, weil sie die Einheit des Pegels nutzen (cm, % oder kg).
- Einrichtung: Bei *Abstand von oben* steht jetzt, dass dafür ein Sensor nötig ist, der eine Länge misst.

## [0.8.1] - 2026-11-23

### Geändert
- Karte (Stil Klassisch): Der Verlauf unten ist jetzt dasselbe Diagramm wie im Prognose-Stil, nach den Messwerten skaliert und mit Werten bei Mouseover oder Antippen.
- Karte (Stil Klassisch): Die Pegellatte ist aufgeräumter. Schwellen erscheinen als farbige Marken an der Latte und als dezente Linien im Becken, der aktuelle Pegel ist ein Strich auf der Latte statt einer Linie quer durchs Wasser.

## [0.8.0] - 2026-11-23

### Neu
- Karte (Stil Prognose): Fährst du mit der Maus über das Diagramm oder tippst am Handy darauf, siehst du Zeitpunkt, Wert und Stufe zu diesem Zeitpunkt. Rechts von „jetzt“ zeigt der Tooltip die Prognose.
- Karte (Stil Prognose): Schwellen außerhalb des Diagramms erscheinen als Hinweis am Rand, zum Beispiel „↑ Zweite Wiese überflutet · 260 cm“.

### Geändert
- Karte (Stil Prognose): Das Diagramm richtet sich nach den Messwerten, die Kurve nutzt die volle Höhe. Als Linie erscheinen nur Schwellen in der Nähe der Messwerte und die, die die Prognose erreicht.
- Karte (Stil Prognose): Die Namen der Schwellen überlappen nicht mehr. Liegen zwei Linien zu dicht, bekommt nur eine eine Beschriftung; im Tooltip stehen weiterhin alle.
- Karte (Stil Prognose): Das Diagramm behält sein Seitenverhältnis, statt gestreckt zu werden. Die Beschriftungen sind dadurch nicht mehr verzerrt.

## [0.7.8] - 2026-11-21

### Neu
- HACS-Prüfung im Workflow des Repositorys, als Vorbereitung für die Aufnahme in die HACS-Standard-Repositories.

## [0.7.7] - 2026-11-21

### Geändert
- Karte: Die Wellen bewegen sich jetzt immer, auch wenn im System „Bewegung reduzieren“ eingeschaltet ist (zum Beispiel bei ausgeschalteten Animationseffekten in Windows).

### Behoben
- Karte: Die Wellenanimation beginnt nicht mehr bei jedem neuen Messwert von vorn. Sie läuft gleichmäßig weiter, auch bei Sensoren, die sehr oft melden.

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
