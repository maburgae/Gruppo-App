from datetime import date, datetime
from calc_the_day import apply_dayhcps_from_json, update_round_for_date
from DayHcp import calc_dayhcps_for_players_before_date
from calc_the_day import update_round_for_date
from functions import calculate_money_for_players
from show_scorecard import show_scorecard
import json
from ranking_table import make_ranking_table, load_round
import os


NO_SHOW_JSON_PATH = "json/no_show_players.json"


def _load_no_show_players() -> list[str]:
    if not os.path.exists(NO_SHOW_JSON_PATH):
        return []
    try:
        with open(NO_SHOW_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            players = data.get("players", [])
        elif isinstance(data, list):
            players = data
        else:
            players = []
        out = []
        for p in players:
            if isinstance(p, str):
                pn = p.strip()
                if pn and pn not in out:
                    out.append(pn)
        return out
    except Exception:
        return []


def _has_numeric_score(pdata: dict) -> bool:
    scores = pdata.get("Score")
    if not isinstance(scores, list):
        return False
    return any(isinstance(v, (int, float)) for v in scores)


def _append_no_show_players_with_daily_max(json_path: str, date_key: str) -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if date_key not in data or "Spieler" not in data[date_key]:
        return

    no_show_players = _load_no_show_players()
    if len(no_show_players) == 0:
        return

    players = data[date_key]["Spieler"]

    max_money = 0
    for pdata in players.values():
        g = pdata.get("Geld")
        if isinstance(g, (int, float)):
            max_money = max(max_money, int(g))
        elif g not in (None, ""):
            try:
                max_money = max(max_money, int(float(str(g).replace(",", "."))))
            except Exception:
                pass

    for pname in no_show_players:
        if pname in players:
            if not _has_numeric_score(players[pname]):
                players[pname] = {"Geld": max_money}
            continue

        players[pname] = {"Geld": max_money}

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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

    # No-show Spieler mit Tages-Maximalbetrag nachträglich einfügen (vor Bild/Diagramm-Erzeugung)
    _append_no_show_players_with_daily_max(day_path, date_key)

    # Scorecard (Front/Back) erzeugen -> wird als <date>_front.png / <date>_back.png gespeichert
    show_scorecard(day_path, date_key, save_path=f"scorecards/{date_key}.png", show=False)

    # Optional: Ranking-Vorschau kann hier erstellt werden (Konf-Seite erzeugt es ebenfalls)
    players = load_round(day_path, date_key)
    make_ranking_table(players, save_path=f"rankings/{date_key}.png", show=False)

    return "Tag erfolgreich berechnet."