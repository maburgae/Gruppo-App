# Beschreibung der Daten in allrounds.json / allrounds_long.csv

## Überblick
Die Datei `allrounds.json` enthält den vollständigen historischen Datenbestand aller erfassten Golfrunden der "Gruppo". Jede Runde ist eindeutig über ihr Datum (Format: `DD.MM.YYYY`) als Top-Level-Schlüssel identifiziert. Unter jedem Datum liegen Metadaten zur Runde (z. B. Platzname) sowie strukturierte Leistungs‑ und Ergebnisdaten je Spieler.

Zur besseren Weiterverarbeitung (z. B. durch ChatGPT, Tabellenkalkulationen oder BI‑Tools) wurde zusätzlich eine normalisierte CSV-Datei `allrounds_long.csv` erzeugt. Diese repräsentiert sämtliche Informationen (inkl. aller verschachtelten Listen) in einem zeilenorientierten Long-Format.

## Struktur von allrounds.json
Top-Level (pro Datumsschlüssel):
```
<Datum>: {
  "Ort": <String | Platzname>,
  "Par": [p1, p2, ..., p18],          # Par-Werte je Loch (Integer oder null)
  "Hcp": [h1, h2, ..., h18],          # Course-Handicap / Vorgaben je Loch (Integer oder null)
  "Spieler": {
      <Spielername>: {
          "Platz": <Integer | null>,  # Rang / Platzierung des Spielers in der Tageswertung
          "Netto": <Integer | null>,  # Netto-Punkte oder Score (Definition projektspezifisch)
          "Geld": <Integer | null>,   # Vergebene Geld-/Bonus-Einheiten (berechnete Wertung)
          "Gesp.Hcp": <Float|Int|null>, # Gespieltes Handicap / berechneter Wert für die Runde
          "Birdies": <Integer | null>,
          "Pars": <Integer | null>,
          "Bogies": <Integer | null>,
          "Strich": <Integer | null>, # Anzahl "Strich" (nicht gescorte Löcher / Ausfälle)
          "DayHcp": <Float|Int|null>, # Tages-Handicap vor / nach Berechnung
          "Ladies": <Integer | null>, # Sonderwertung "Ladies"
          "N2TP": <Integer | null>,   # Sonderwertung Nearest to the Pin (1 = gewonnen, sonst null)
          "LD": <Integer | null>,     # Sonderwertung Longest Drive (1 = gewonnen, sonst null)
          "Flight": <String | null>,  # Zugeordneter Flight (Gruppierung)
          "Score": [s1, s2, ..., s18],# Rohscore pro Loch (Integer oder null)
          "NettoP": [n1, n2, ..., n18]# Netto-Punkte pro Loch (Integer oder null)
      },
      ... weitere Spieler ...
  }
}
```
Hinweise:
- Fehlende / nicht ausgefüllte Werte sind mit `null` markiert.
- Listen haben immer Länge 18 (für 18 Löcher), sofern definiert.
- `Flight` kann benutzt werden, um Spieler gruppenweise (z. B. Flight 1 / Flight 2) auszuwerten.

## Struktur von allrounds_long.csv
Die CSV-Datei liegt im Long-Format vor (Delimiter `;`). Kopfzeile:
```
Date;Ort;Player;Field;Index;Value
```
Bedeutung der Spalten:
- `Date`: Datum der Runde (`DD.MM.YYYY`).
- `Ort`: Platzname der Runde (wie in JSON unter `Ort`).
- `Player`: Spielername (leer für zeilen, die sich auf Par/Hcp beziehen).
- `Field`: Kennzeichner des Datenfeldes:
  - Par / Hcp (Platzdefinition)
  - Für Spieler: Platz, Netto, Geld, Gesp.Hcp, Birdies, Pars, Bogies, Strich, DayHcp, Ladies, N2TP, LD, Flight, Score, NettoP
- `Index`: Loch-Nummer (1..18) für Felder, die Listen sind (Par, Hcp, Score, NettoP). Für reine Skalarfelder leer.
- `Value`: Der jeweilige Wert (Zahl oder Text oder leer / null äquivalent).

### Abbildung / Transformation
1. Par- und Hcp-Arrays werden je Loch in separate Zeilen ohne Spielername geschrieben.
2. Für jeden Spieler werden zuerst alle Skalarfelder (Platz, Netto, ...) als eigene Zeilen mit leerem Index erfasst.
3. Danach folgen pro Spieler alle Listeneinträge (Score[i], NettoP[i]) mit Index 1..18.
4. `null` aus dem JSON bleibt in Python `None` und wird im CSV als leeres Feld (oder literal 'None' je nach Interpret) dargestellt – hier leer, sofern möglich.

## Nutzung / Analysebeispiele
- Summierung aller Birdies je Jahr: Filter Field == "Birdies" und aggregiere Value nach Date (Jahr extrahieren) oder Player.
- Flight-Auswertung: Filter Field == "Flight" um Zuordnung zu erhalten und Scores getrennt auswerten.
- Lochstatistik: Filter Field == "Score" und gruppiere nach Index (Loch) über mehrere Daten.
- Sonderwertungen: Field in ("LD", "N2TP", "Ladies") zur Ermittlung von Gewinnerhäufigkeiten.

## Datenqualität / Konsistenz
- Es wird vorausgesetzt, dass jede Runde genau 18 Löcher umfasst. Falls Runden abgebrochen wurden, erscheinen `null` Einträge.
- In Skalarfeldern kann `null` auftreten, wenn Berechnungen (z. B. Tages- oder gespieltes Handicap) noch nicht durchgeführt wurden.
- Geld / Sonderwertungen hängen von separaten Berechnungsskripten ab (z. B. Tagesberechnung, Statistikroutinen).

## Erweiterbarkeit
- Weitere Felder können ohne Bruch hinzugefügt werden: Sie erscheinen automatisch als zusätzliche `Field`-Werte im Long-Format.
- Für BI-Modelle kann das Long-Format direkt pivotiert werden (z. B. Score je Spieler/Loch, oder Netto summiert).

## Datei-Lage
- Original JSON: `json/allrounds.json`
- CSV (Long-Format): `json/allrounds_long.csv`
- Diese README: `json/allrounds_README.md`

## Hinweise zur Weitergabe an ChatGPT
- Das Long-Format verhindert Abschneidung großer verschachtelter Strukturen.
- Bei sehr großen Datenmengen ggf. in Jahresscheiben splitten.
- Für gezielte Fragen: Vorab subsetten (z. B. nur bestimmte Felder oder Spieler) und erneut als kompakte CSV bereitstellen.

---
Stand der Dokumentation: automatisch generiert.
