
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
    date_key = today.strftime("%d.%m.%Y")
    day_path = "json/golf_df/golf_df.json"

    calc_dayhcps_for_players_before_date(date_key)
    
    apply_dayhcps_from_json(day_path, "json/DayHcp.json")
    
    # Step 4: Calculate round for a certain date
    # date_key = "2.09.2025"   # <- gewünschtes Datum
    update_round_for_date(day_path, date_key)

    # Add money
    calculate_money_for_players(day_path, date_key)

    # date_key = "22.09.2025"  # Schlüssel wie in deiner JSON
    show_scorecard(day_path, date_key, save_path="pics/scorecard.png", show=False)
    
    json_file = "json/golf_df/golf_df.json"
    date_key = "30.09.2025"  # gewünschtes Datum

    players = load_round(day_path, date_key)
    make_ranking_table(players, save_path=f"pics/ranking.png", show=False)

    return "Tag erfolgreich berechnet."