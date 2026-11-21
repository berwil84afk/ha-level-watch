# Todo

- [ ] **Schwellenwerte über die Karte einrichten**
  Schwellen direkt in der Level-Watch-Karte anlegen, ändern und löschen, statt nur unter *Geräte & Dienste → Konfigurieren*.
  Ideen dazu:
  - Die Integration bietet einen WebSocket-Befehl, z. B. `level_watch/thresholds/update`, der die Schwellen in den Optionen speichert. Danach lädt der Eintrag wie beim Options-Flow neu.
  - Den Befehl dürfen nur Admins aufrufen.
  - In der Karte öffnet ein Stift-Symbol eine Liste der Schwellen mit Name, Wert, Richtung, Hysterese, Farbe und Meldung. Neue Schwellen ließen sich per Klick auf die Pegellatte setzen.
  - Die Meldeziele kommen aus derselben Liste wie im Options-Flow (`messaging.available_targets`).
