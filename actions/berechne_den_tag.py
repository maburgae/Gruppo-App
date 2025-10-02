from datetime import date, datetime
from calc_the_day import apply_dayhcps_from_json, update_round_for_date
from DayHcp import calc_dayhcps_for_players_before_date
from calc_the_day import update_round_for_date
from functions import calculate_money_for_players
from show_scorecard import show_scorecard
import json
from ranking_table import make_ranking_table, load_round


def main() -> str:
    """Berechnet den Tag anhand des DataFrames. Platzhalter-Logik."""
    today = date.today()
    date_key_today = today.strftime("%d.%m.%Y")
    day_path = "json/golf_df/golf_df.json"

    # Wähle den zu verarbeitenden Schlüssel: heute falls vorhanden, sonst den vorhandenen Schlüssel
    try:
        with open(day_path, "r", encoding="utf-8") as f:
            day_data = json.load(f)
        if not isinstance(day_data, dict) or len(day_data) == 0:
            raise ValueError("golf_df.json hat keinen gültigen Spieltag-Schlüssel")
        if date_key_today in day_data:
            date_key = date_key_today
        else:
            # Fallback: nutze den vorhandenen Schlüssel (z.B. wenn der Tag bereits angelegt wurde)
            date_key = next(iter(day_data.keys()))
    except Exception:
        # In Notfällen nutze das heutige Datum
        date_key = date_key_today

    calc_dayhcps_for_players_before_date(date_key)

    apply_dayhcps_from_json(day_path, "json/DayHcp.json")

    # Runde für den Tag berechnen/aktualisieren
    update_round_for_date(day_path, date_key)

    # Geld berechnen
    calculate_money_for_players(day_path, date_key)

    # Scorecard (Front/Back) erzeugen -> wird als <date>_front.png / <date>_back.png gespeichert
    show_scorecard(day_path, date_key, save_path=f"scorecards/{date_key}.png", show=False)

    # Optional: Ranking-Vorschau kann hier erstellt werden (Konf-Seite erzeugt es ebenfalls)
    players = load_round(day_path, date_key)
    make_ranking_table(players, save_path=f"rankings/{date_key}.png", show=False)

    return "Tag erfolgreich berechnet."