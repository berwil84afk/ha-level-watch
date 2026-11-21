# Level Watch für Home Assistant

Custom Integration, die einen **Wasserpegel** (Fluss, Teich, Brunnen) oder einen **Tank** (Zisterne, Heizöl) aus einem vorhandenen Sensor überwacht und daraus Kennzahlen berechnet.

> **Stand 0.7.0:** Pegel, Tendenz, Änderungsrate, 24-h-Werte, Datenqualität, Schwellenwerte mit Meldungen und Vorlagen, Tankvolumen, Verbrauch und Reichweite sowie eine eigene Karte für Wasserpegel und Tanks, in der du die Schwellen auch bearbeiten kannst.

## Was du bekommst

| Sensor | Bedeutung |
|---|---|
| Pegel | geglätteter Pegel in cm (Einheit in HA umstellbar) |
| Füllstand | Pegel in % zwischen *Bezug unten* und *Bezug oben* (nur wenn *Bezug oben* gesetzt) |
| Tendenz | steigend / fallend / stabil |
| Änderungsrate | cm pro Stunde, lineare Regression über das Tendenz-Zeitfenster |
| Minimum / Maximum 24 h | Extremwerte der letzten 24 Stunden |
| Änderung 24 h | Unterschied zu vor 24 Stunden |
| Datenqualität | OK, veraltet, Sensor nicht verfügbar oder keine Daten |
| Stufe | Name der schwersten aktiven Schwelle oder „Normal“, Farbe im Attribut `color` |
| Nächste Schwelle | Schwelle, auf die sich der Pegel gerade zubewegt |
| Zeit bis nächste Schwelle | Stunden bis dahin bei gleichbleibender Rate |
| *Binary-Sensor je Schwelle* | an, solange die Schwelle erreicht ist |

Stufe, nächste Schwelle und Zeit bis dahin gibt es nur, wenn mindestens eine Schwelle angelegt ist.

Die Messwerte und der Zustand der Schwellen werden gespeichert. Tendenz und 24-h-Werte überstehen so einen Neustart, und eine Meldung kommt nach einem Neustart nicht doppelt.

## Schwellenwerte und Meldungen

Schwellen legst du auf drei Wegen an:

- **In der Karte:** Admins sehen oben rechts einen Stift. Er öffnet einen Editor mit Live-Vorschau des Zonenbalkens. Dort legst du Schwellen an, änderst und löschst sie und stellst die Meldungen ein. *Speichern* übernimmt alles auf einmal.
- **Aus einer Vorlage:** *Level Watch → Konfigurieren → Schwellen aus Vorlage hinzufügen.*
  - *Flusspegel:* Niedrigwasser und Meldestufen 1–4.
  - *Tank:* fast leer, Reserve und voll.
  - Du trägst nur die Werte ein, die du brauchst. Name, Farbe, Richtung und Hysterese sind vorbelegt. „Kritisch“ gilt dabei nur für Meldestufe 3 und 4 bzw. „Fast leer“.
- **Einzeln:** *Level Watch → Konfigurieren → Schwellenwert hinzufügen.*

Je Schwelle:

| Feld | Bedeutung |
|---|---|
| Name, Wert | z. B. „Meldestufe 1“ bei 500 cm |
| Erreicht, wenn der Pegel | auf oder über den Wert steigt (Hochwasser, voller Tank) oder auf oder unter den Wert fällt (Niedrigwasser, Reserve) |
| Hysterese | so weit muss der Pegel zurückgehen, bevor die Schwelle aufgehoben wird (Vorgabe 2 cm) |
| Farbe | Farbe der Stufe, später für die Karte |
| Meldung senden, Melden über | Companion App, dauerhafte Meldung in Home Assistant oder jeder andere notify-Dienst (Telegram, E-Mail …) |
| Kritisch | nur Companion App: klingelt auch im Stumm-Modus |
| Meldungstext | leer für den Standardtext; Platzhalter `{name}`, `{threshold}`, `{value}`, `{level}`, `{trend}`, `{rate}` |
| Entwarnung senden | auch melden, wenn die Schwelle aufgehoben ist |
| Wiederholen alle | Meldung wiederholen, solange die Schwelle gilt (0 = einmal) |

Für Pegel an Bundeswasserstraßen nennt Pegelonline auf der Seite jeder Messstelle Kennwerte wie MNW (mittleres Niedrigwasser), NNW (niedrigstes bekanntes Niedrigwasser) und HHW (höchstes bekanntes Hochwasser). Sie sind in cm über dem Pegelnullpunkt angegeben, genau wie die Werte der PEGELONLINE-Integration. Du kannst sie also direkt als Schwellen eintragen, z. B. MNW als *Niedrigwasser*.

Ausgewertet wird nur, solange die Datenqualität „OK“ ist. Ein ausgefallener Sensor löst also keine Meldung aus. Dafür kannst du eine eigene Automation auf den Datenqualitäts-Sensor bauen.

Bei jedem Erreichen und Aufheben einer Schwelle feuert das Event `level_watch_threshold` mit `name`, `threshold`, `value`, `direction`, `active` und `level`. Darauf kannst du eigene Automationen aufbauen:

```yaml
triggers:
  - trigger: event
    event_type: level_watch_threshold
    event_data:
      threshold: Meldestufe 2
      active: true
actions:
  - action: switch.turn_on
    target:
      entity_id: switch.pumpe
```

## Datenquellen

Level Watch nimmt jeden Sensor mit einer Längeneinheit (mm, cm, m, in, ft) oder in Prozent, zum Beispiel:

- **Ultraschall- oder Radarsensor** über ESPHome oder Tasmota. Misst er von oben nach unten, wähle *Messart: Abstand von oben* und gib die Einbauhöhe an.
- **Drucksensor** im Brunnen oder Tank.
- **Offizielle Pegel** über die in Home Assistant enthaltene Integration [PEGELONLINE](https://www.home-assistant.io/integrations/pegel_online/). Daten: WSV, PEGELONLINE, Lizenz DL-DE->Zero-2.0. Es sind ungeprüfte Rohdaten.

- **Füllstandssensor in %**, etwa von einem Heizöl- oder Zisternenmodul. Level Watch rechnet dann durchgehend in %: Pegel, Bezüge, Schwellen, Rate (%/h), Min/Max und die Karte. Beim Tank gibt es Verbrauch in %/Tag und die Reichweite in Tagen, aber keine Liter (die Tankform wird dafür nicht gebraucht). Ohne *Bezug oben* gilt 100 %. *Abstand von oben* ist bei % nicht möglich.

> Level Watch ersetzt keine amtlichen Hochwasserwarnungen.

## Installation

### HACS

1. HACS → ⋮ → *Benutzerdefinierte Repositories* → `https://github.com/berwil84afk/ha-level-watch`, Typ *Integration* → *Hinzufügen*.
2. „Level Watch“ in HACS suchen → *Herunterladen*.
3. Home Assistant neu starten.

### Manuell

1. Den Ordner `custom_components/level_watch` nach `/config/custom_components/level_watch` kopieren.
2. Home Assistant neu starten.

## Einrichtung

*Einstellungen → Geräte & Dienste → Integration hinzufügen → Level Watch.* Für jeden überwachten Pegel richtest du einen eigenen Eintrag ein.

| Feld | Bedeutung |
|---|---|
| Pegelsensor | Quelle des Pegels oder Abstands |
| Einheit des Sensors | *Automatisch* nimmt die Einheit des Sensors |
| Art | Wasserpegel oder Tank |
| Messart | *Pegel* oder *Abstand von oben* |
| Einbauhöhe | nur bei Abstand: Höhe des Sensors über dem Nullpunkt (z. B. Tankboden) |
| Korrektur | wird zu jedem Wert addiert |
| Bezug unten / oben | Pegel für 0 % und 100 % |

In den Optionen unter *Tendenz und Datenqualität*:

| Einstellung | Vorgabe | Bedeutung |
|---|---|---|
| Zeitfenster Tendenz | 60 min | Zeitraum der Ratenberechnung |
| Stabil-Bereich | 1 cm/h | Raten innerhalb ± gelten als stabil |
| Glättung | 5 min | Median gegen einzelne Ausreißer, 0 = aus |
| Veraltet nach | 60 min | ohne Meldung des Sensors gilt der Wert als veraltet |
| Max. Sprung | 0 (aus) | größere Sprünge zählen erst nach 3 übereinstimmenden Messungen |
| Zeitraum Verbrauch | 7 d | nur Tank: über diesen Zeitraum wird der Tagesverbrauch gemittelt |
| Nachtanken erkennen ab | 5 cm | nur Tank: so viel Anstieg binnen zwei Stunden gilt als Nachtanken, 0 = aus |

Für einen Heizöltank, dessen Pegel nur langsam fällt, lohnt ein langes Zeitfenster (z. B. 1440 min) und ein kleiner Stabil-Bereich (z. B. 0,05 cm/h).

## Tank

Bei *Art: Tank* gibst du im Abschnitt *Tank* die Form und die Innenmaße an. Der Nullpunkt ist der Tankboden. Liegt dein Sensor-Nullpunkt woanders, gleichst du das mit *Korrektur* aus.

| Form | Maße |
|---|---|
| Stehender Zylinder | Durchmesser |
| Liegender Zylinder | Durchmesser, Länge |
| Quader | Länge, Breite |

Damit kommen diese Sensoren dazu:

| Sensor | Bedeutung |
|---|---|
| Volumen | Inhalt in Litern, Fassungsvermögen im Attribut `capacity` |
| Freies Volumen | so viel passt noch hinein, bis *Bezug oben* (beim liegenden Zylinder sonst bis zum Durchmesser) |
| Verbrauch pro Tag | Liter pro Tag, gemittelt seit dem letzten Nachtanken über höchstens den eingestellten Zeitraum. Ein Wert erscheint nach 12 Stunden Daten. |
| Reichweite | Tage, bis *Bezug unten* bei diesem Verbrauch erreicht ist |
| Zeit bis voll | Stunden bis *Bezug oben*, solange der Pegel steigt (auch ohne Form) |
| Letztes Nachtanken | Zeitpunkt des letzten erkannten Nachtankens (auch ohne Form) |

Mit Form rechnet der *Füllstand* nach Volumen. Beim liegenden Zylinder ist halbe Höhe genau 50 %, ein Viertel der Höhe aber nur etwa 20 %.

Regen in der Zisterne zählt wie Nachtanken. Danach beginnt die Verbrauchsrechnung von vorn.

## Karte

Die Integration bringt die Karte **Level Watch** mit. Eine Ressource musst du nicht eintragen. Du findest sie unter *Dashboard bearbeiten → Karte hinzufügen → Level Watch* und kannst sie dort über die Oberfläche einstellen.

- **Wasserpegel:** Pegellatte mit Skala, Wasserbecken mit bewegter Oberfläche und den Schwellen als Linien. Eine erreichte Schwelle wird durchgezogen dargestellt.
- **Tank:** Die Darstellung folgt der eingestellten Form: liegender Zylinder (Ansicht von der Stirnseite), stehender Zylinder oder Quader. Angezeigt werden Füllstand, Liter, Reichweite, Verbrauch und *Zeit bis voll*.
- **Farbe:** Wasser und Akzente nehmen die Farbe der aktiven Stufe an, sonst Blau.
- **Dazu:** Tendenzpfeil mit Rate, *Nächste Schwelle in …*, Verlauf der letzten 24 Stunden mit Schwellenlinien und ein Hinweis, wenn die Daten veraltet sind oder der Sensor fehlt.

Die Karte hat vier Stile:

| Stil | Inhalt |
|---|---|
| `forecast` (Standard) | Zonenbalken mit den Stufen und dem aktuellen Pegel, darunter Verlauf und gestrichelte Prognose bis zur nächsten Schwelle, dazu „Meldestufe 2 voraussichtlich heute 14:49“ bzw. „Reicht noch 132 Tage (bis 2. Apr.)“ |
| `classic` | Pegellatte mit Wasserbecken oder Tankform, wie oben beschrieben |
| `ring` | Füllstandsring mit Schwellen-Markierungen, gut für Tanks |
| `compact` | schmale Kachel für halbe Breite: Balken, Wert, Stufe, Hinweis |

```yaml
type: custom:level-watch-card
entity: sensor.rhein_pegel   # oder eine andere Entität desselben Level-Watch-Geräts
style: forecast              # forecast, classic, ring oder compact
title: Rhein                 # optional, sonst der Gerätename
mode: auto                   # auto, water oder tank
show_history: true           # false blendet den Verlauf aus
history_hours: 24            # Länge des Verlaufs
forecast_hours: 12           # wie weit die Prognose reicht
```

## Entwicklung

```bash
pip install -r requirements_test.txt
pytest
```

Die Karte siehst du ohne Home Assistant mit Testdaten: Starte `python -m http.server 8766` im Repo und öffne `http://127.0.0.1:8766/dev/preview.html`. Mit `?style=ring` usw. siehst du nur einen Stil.

Die Tests laufen auf Linux (GitHub Actions). Home Assistant selbst unterstützt Windows nicht.
