import json
from datetime import date, datetime

def main(players: list[str] | None = None) -> str:
    """Startet eine neue Runde. Platzhalter-Logik."""
    if players is None:
        players = []

    json_path = "json/golf_df/golf_df.json"
    # Read in the existing golf_df.json file
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            golf_data = json.load(f)
    except FileNotFoundError:
        golf_data = None
    # Create a copy with date and time extended
    dt_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    copy_path = f"json/golf_df/golf_df_copy_{dt_str}.json"
    if golf_data is not None:
        with open(copy_path, "w", encoding="utf-8") as f:
            json.dump(golf_data, f, ensure_ascii=False, indent=2)
        print(f"Copy of golf JSON written to {copy_path}")
    else:
        print(f"No golf_df.json found to copy.")

    # Build default round data
    round_data = {
        "Ort": "Platzname",
        "Par": [None]*18,
        "Hcp": [None]*18,
        "Spieler": {}
    }

    for name in players:
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
            "Score": [None]*18,
            "NettoP": [None]*18
        }
    today = datetime.now().strftime("%d.%m.%Y")
    out = {today: round_data}

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Default golf JSON written to {json_path}")

    return f"Neue Runde gestartet. Spieler: {players}"
