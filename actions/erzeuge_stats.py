import json
from pathlib import Path


def load_round(json_file: str, date_key: str) -> dict:
    """Lädt die Runde zu einem Datum aus allrounds.json."""
    p = Path(json_file)
    if not p.exists():
        raise FileNotFoundError(json_file)
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if date_key not in data:
        raise ValueError(f"Date {date_key} not found in {json_file}")
    return data[date_key]["Spieler"]


def main():
    # Bild-Generierung ist obsolet, da Ranking/Scorecard als HTML gerendert werden.
    json_file = "json/golf_df/golf_df.json"
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return f"Fehler: Datei {json_file} nicht gefunden"
    except json.JSONDecodeError as e:
        return f"Fehler: Ungültiges JSON ({e})"

    if not isinstance(data, dict) or len(data) == 0:
        return "Fehler: JSON hat keinen gültigen Inhalt"

    keys = list(data.keys())
    if len(keys) != 1:
        return f"Fehler: Erwartet genau einen Schlüssel, gefunden {len(keys)}: {keys}"

    return "Stats-Rendering läuft als HTML (keine PNG-Erzeugung)."

if __name__ == "__main__":
    main()

