# compute_dayhcp_and_stableford.py
# Compute DayHcp, Stableford stats & Ranking for a given date in allrounds.json

# einfügen, dass bei Score null auch NettoP ist gleich null. Das bedeutet, Strich.

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


def normalize_requested_date_key(requested: str, data: Dict[str, Any]) -> str:
    """Return an existing key from data matching the requested date (supports dd.mm.yyyy or yyyy-mm-dd)."""
    if requested in data:
        return requested
    dt = parse_date_key(requested)
    if not dt:
        raise ValueError(f"Unrecognized date format: {requested}")
    alt1 = dt.strftime("%d.%m.%Y")
    alt2 = dt.strftime("%Y-%m-%d")
    if alt1 in data:
        return alt1
    if alt2 in data:
        return alt2
    raise ValueError(f"Date {requested} not found in file.")


def round_half_up(x: float) -> int:
    return math.floor(x + 0.5)


def shots_received_on_hole(day_hcp: Optional[int], stroke_index: Optional[int]) -> int:
    """
    Distribute handicap shots using Stroke Index (1..18).
    Each hole gets base = H//18, and extra +1 on the 'H%18' lowest SI holes.
    Treat None day_hcp as 0.
    """
    if day_hcp is None:
        day_hcp = 0
    if stroke_index is None or not isinstance(stroke_index, int):
        return 0
    if day_hcp <= 0:
        return 0
    base = day_hcp // 18
    extra = 1 if stroke_index <= (day_hcp % 18) else 0
    return base + extra


def stableford_points(par: Optional[int], gross: Optional[int], shots: int) -> int:
    if par is None or gross is None:
        return 0
    net = gross - shots
    diff = net - par
    if diff <= -3:
        return 5
    elif diff == -2:
        return 4
    elif diff == -1:
        return 3
    elif diff == 0:
        return 2
    elif diff == 1:
        return 1
    else:
        return 0


def _pad18(lst: List[Any]) -> List[Any]:
    lst = list(lst or [])
    if len(lst) < 18:
        lst += [None] * (18 - len(lst))
    return lst[:18]


# ---------- Core ----------
def apply_dayhcps_from_json(json_path: str, dayhcp_path: str) -> None:
    """
    Reads DayHcp.json and writes all DayHcps in there to the corresponding day and player in the target JSON file (golf_df format).
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(dayhcp_path, "r", encoding="utf-8") as f:
        dayhcp_data = json.load(f)
    for date_key, player_map in dayhcp_data.items():
        if date_key in data and "Spieler" in data[date_key]:
            for player, dhcp in player_map.items():
                if player in data[date_key]["Spieler"]:
                    data[date_key]["Spieler"][player]["DayHcp"] = dhcp
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[ok] DayHcps written to {json_path}")


def update_round_for_date(json_path: str, date_key: str) -> None:
    p = Path(json_path)
    if not p.exists():
        raise FileNotFoundError(json_path)

    with p.open("r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    for key in data:
        
        actual_key = normalize_requested_date_key(key, data)
        round_obj = data[actual_key]
        dt = parse_date_key(actual_key)
        if not dt:
            raise ValueError(f"Cannot parse date key: {actual_key}")

        pars: List[Optional[int]] = _pad18(round_obj.get("Par", [None] * 18))
        sindex: List[Optional[int]] = _pad18(round_obj.get("Hcp", [None] * 18))  # Stroke Index per hole
        players: Dict[str, Any] = round_obj.get("Spieler", {})

        # 1) DayHcp wird nicht mehr berechnet, sondern vorausgesetzt
        for pname, pdata in players.items():
            if "DayHcp" not in pdata or pdata["DayHcp"] == 0:
                raise ValueError(f"DayHcp fehlt oder ist 0 für Spieler: {pname} am {actual_key}")

        # 2) Stableford per hole & counters
        for pname, pdata in players.items():
            scores = _pad18(pdata.get("Score", []))
            day_hcp = pdata.get("DayHcp", 0)
            # Ensure NettoP array exists and is padded
            if "NettoP" not in pdata or not isinstance(pdata["NettoP"], list):
                pdata["NettoP"] = [None] * 18
            else:
                pdata["NettoP"] = _pad18(pdata["NettoP"])
            netto_p: List[int] = []
            pars_count = 0
            bogies_count = 0
            birdies_count = 0
            strich_count = 0

            for i in range(18):
                par_i = pars[i] if isinstance(pars[i], int) else None
                si_i = sindex[i] if isinstance(sindex[i], int) else None
                sc_i = scores[i] if isinstance(scores[i], int) else None

                shots = shots_received_on_hole(day_hcp, si_i) if (par_i and si_i) else 0
                # Wenn Score 0 (Strich), dann NettoP = 0
                if sc_i == 0:
                    pts = 0
                else:
                    pts = stableford_points(par_i, sc_i, shots)

                # Zählwerte (gross-basiert für Birdies/Pars/Bogies; Strich = 0 NettoP)
                if sc_i is not None and par_i is not None:
                    if sc_i == par_i - 1:
                        birdies_count += 1
                    elif sc_i == par_i:
                        pars_count += 1
                    elif sc_i == par_i + 1:
                        bogies_count += 1
                if pts == 0:
                    strich_count += 1

                netto_p.append(pts)
                pdata["NettoP"][i] = pts  # Update NettoP array in-place

            pdata["Netto"] = sum(netto_p)
            pdata["Pars"] = pars_count
            pdata["Bogies"] = bogies_count
            pdata["Birdies"] = birdies_count
            pdata["Strich"] = strich_count
            pdata["Gesp.Hcp"] = int(day_hcp + 36 - pdata["Netto"])

        # 3) Ranking ("Platz") mit Countback nach Stroke Index
        # Map SI (1..18) -> Lochindex (0..17)
        si_to_idx = {}
        for idx, si in enumerate(sindex):
            if isinstance(si, int) and 1 <= si <= 18 and si not in si_to_idx:
                si_to_idx[si] = idx
        # Falls Hcp unvollständig: fehlende SI auf 0-Punkte-Index abbilden (wir nehmen None -> behandelt wie 0)
        ordered_holes = [si_to_idx.get(si, None) for si in range(1, 19)]

        # Baue Sortierschlüssel: (-Netto, -NettoP@SI1, -NettoP@SI2, ..., -NettoP@SI18)
        def player_sort_key(item):
            pname, pdata = item
            netto = pdata.get("Netto", 0)
            np_arr = _pad18(pdata.get("NettoP", []))
            tb = []
            for h in ordered_holes:
                val = np_arr[h] if (isinstance(h, int) and 0 <= h < 18) else 0
                tb.append(-val)  # größer ist besser -> negativ für absteigend
            return (-netto, *tb)

        sorted_players = sorted(players.items(), key=player_sort_key)

        # Dense Ranking zuweisen
        last_key = None
        current_rank = 0
        for idx, (pname, pdata) in enumerate(sorted_players):
            k = player_sort_key((pname, pdata))
            if k != last_key:
                current_rank += 1
                last_key = k
            pdata["Platz"] = current_rank

        # Save back
        with p.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[ok] Updated round '{actual_key}' in {json_path}")


# ---------- Main ----------
def main():
    # Step 1: Read main data file
    json_file = "golf_df.json"
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Step 2: Read DayHcp.json and write DayHcps to main data
    dayhcp_file = "DayHcp.json"
    apply_dayhcps_from_json(json_file, dayhcp_file)
    
    # Step 3: Save updated main data back to file
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Step 4: Calculate round for a certain date
    date_key = "24.09.2025"   # <- gewünschtes Datum
    update_round_for_date(json_file, date_key)


if __name__ == "__main__":
    main()
