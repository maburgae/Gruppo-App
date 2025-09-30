import json
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# ---------- Helpers ----------
def parse_date_key(k: str) -> Optional[datetime]:
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(k, fmt)
        except ValueError:
            pass
    return None

def last_six_hcps_before(data: Dict[str, Any], player: str, before_dt: datetime) -> List[int]:
    """Collect last up to 6 previous 'Gesp.Hcp' integers for player strictly before before_dt."""
    items: List[Tuple[datetime, int]] = []
    for k, v in data.items():
        dt = parse_date_key(k)
        if not dt or not isinstance(v, dict) or dt >= before_dt:
            continue
        stats = v.get("Spieler", {}).get(player)
        if not stats:
            continue
        h = stats.get("Gesp.Hcp")
        if isinstance(h, int):
            items.append((dt, h))
    items.sort(key=lambda x: x[0], reverse=True)
    return [h for _, h in items[:6]]

def calc_dayhcps_for_date(data: Dict[str, Any], date_str: str) -> Dict[str, int]:
    """
    For all players at the given date, calculate DayHcp and return a dict {player: DayHcp}.
    """
    dt = parse_date_key(date_str)
    if not dt:
        raise ValueError(f"Unrecognized date format: {date_str}")
    round_obj = data.get(date_str)
    if not round_obj or "Spieler" not in round_obj:
        raise ValueError(f"No round or players found for date: {date_str}")
    result = {}
    for player, pdata in round_obj["Spieler"].items():
        prev6 = last_six_hcps_before(data, player, dt)
        if prev6:
            avg = sum(prev6) / len(prev6)
            dayhcp = math.floor(avg + 0.5)
        else:
            dayhcp = 0
        result[player] = dayhcp
    return result

def calc_dayhcps_for_players_before_date(date_str: str) -> Dict[str, int]:
    """
    For all players in the input list, calculate DayHcp using the last six rounds before the given date.
    Returns a dict {player: DayHcp}.
    """
    json_path = "json/allrounds.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    players = ["Marc", "Andy", "Bernie", "Buffy", "Heiko", "Jens", "Markus"]  # Example input list

    dt = parse_date_key(date_str)
    if not dt:
        raise ValueError(f"Unrecognized date format: {date_str}")
    result = {}
    for player in players:
        prev6 = last_six_hcps_before(data, player, dt)
        if prev6:
            avg = sum(prev6) / len(prev6)
            dayhcp = math.floor(avg + 0.5)
        else:
            dayhcp = 0
        result[player] = dayhcp
    
    out_path = "json/DayHcp.json"
    out_data = {date_str: result}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"DayHcp for input players before {date_str} written to {out_path}.")

def main():

    date_str = "28.09.2025"
    dayhcps = calc_dayhcps_for_players_before_date(date_str)
    # Write result to DayHcp.json with date as key
    


if __name__ == "__main__":
    main()

