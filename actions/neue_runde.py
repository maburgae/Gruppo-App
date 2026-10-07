import json
from datetime import datetime

def main(
    players: list[str] | None = None,
    flights: dict[str, str] | None = None,
    ort: str = "Platzname",
    round_date: str | None = None,
) -> str:
    """Startet eine neue Runde. Optional können pro Spieler Flight-Werte übergeben werden.

    Args:
        players: Liste der Spielernamen.
        flights: Mapping Spieler -> Flight (String). Leere Strings werden als None gespeichert.
        ort: Platzname, wird unter 'Ort' gespeichert.
        round_date: Datumsschlüssel im Format DD.MM.YYYY. Wenn leer, wird heute verwendet.
    """
    if players is None:
        players = []
    if flights is None:
        flights = {}
    if not ort:
        ort = "Platzname"

    json_path = "json/golf_df/golf_df.json"
    # Read in the existing golf_df.json file
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            golf_data = json.load(f)
    except FileNotFoundError:
        golf_data = None
    if golf_data is None:
        print("No golf_df.json found. Creating a new default round file.")

    # Build default round data
    round_data = {
        "Ort": ort,
        "Par": [None]*18,
        "Hcp": [None]*18,
        "Spieler": {}
    }

    for name in players:
        flight_val = flights.get(name)
        if isinstance(flight_val, str) and flight_val.strip() == "":
            flight_val = None
        round_data["Spieler"][name] = {
            "Platz": None,
            "Netto": None,
            "Geld": None,
            "Gesp.Hcp": None,
            "Birdies": None,
            "Pars": None,
            "Bogies": None,
            "Strich": None,
            "DayHcp": None,
            "Ladies": None, 
            "N2TP": None,
            "LD": None,
            "Flight": flight_val,
            "Score": [None]*18,
            "NettoP": [None]*18
        }
    date_key = (round_date or "").strip() or datetime.now().strftime("%d.%m.%Y")
    out = {date_key: round_data}

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Default golf JSON written to {json_path}")

    return f"Neue Runde gestartet am {date_key} ({ort}). Spieler: {players}. Flights: {flights}"
