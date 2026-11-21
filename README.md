# Level Watch für Home Assistant

Custom Integration, die einen **Wasserpegel** (Fluss, Teich, Brunnen) oder einen **Tank** (Zisterne, Heizöl) aus einem vorhandenen Sensor überwacht und daraus Kennzahlen berechnet.

> **Stand 0.1.0:** Pegel, Tendenz, Änderungsrate, 24-h-Werte und Datenqualität.
> Schwellenwerte mit Meldungen, Tankvolumen und die eigene Pegel-Karte folgen in den nächsten Versionen.

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

Die Messwerte werden gespeichert, damit Tendenz und 24-h-Werte einen Neustart überstehen.

## Datenquellen

Level Watch nimmt jeden Sensor mit einer Längeneinheit (mm, cm, m, in, ft), zum Beispiel:

- **Ultraschall- oder Radarsensor** über ESPHome oder Tasmota. Misst er von oben nach unten, wähle *Messart: Abstand von oben* und gib die Einbauhöhe an.
- **Drucksensor** im Brunnen oder Tank.
- **Offizielle Pegel** über die in Home Assistant enthaltene Integration [PEGELONLINE](https://www.home-assistant.io/integrations/pegel_online/). Daten: WSV, PEGELONLINE, Lizenz DL-DE->Zero-2.0. Es sind ungeprüfte Rohdaten.

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

Für einen Heizöltank, dessen Pegel nur langsam fällt, lohnt ein langes Zeitfenster (z. B. 1440 min) und ein kleiner Stabil-Bereich (z. B. 0,05 cm/h).

## Entwicklung

```bash
pip install -r requirements_test.txt
pytest
```

Die Tests laufen auf Linux (GitHub Actions). Home Assistant selbst unterstützt Windows nicht.
