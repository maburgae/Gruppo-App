from datetime import date, datetime
from calc_the_day import apply_dayhcps_from_json, update_round_for_date
from DayHcp import calc_dayhcps_for_players_before_date
from calc_the_day import update_round_for_date
from functions import calculate_money_for_players
import json


def _is_money_only_player_entry(pdata: dict) -> bool:
    return isinstance(pdata, dict) and set(pdata.keys()) == {"Geld"}


def _extract_no_show_players(players: dict) -> list[str]:
    out = []
    for pname, pdata in (players or {}).items():
        if not isinstance(pname, str):
            continue
        if _is_money_only_player_entry(pdata):
            pn = pname.strip()
            if pn and pn not in out:
                out.append(pn)
    return out


def _has_numeric_score(pdata: dict) -> bool:
    scores = pdata.get("Score")
    if not isinstance(scores, list):
        return False
    return any(isinstance(v, (int, float)) and v > 0 for v in scores)


def _to_int_money(value) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    if value in (None, ""):
        return 0
    try:
        return int(float(str(value).replace(",", ".")))
    except Exception:
        return 0


def _normalize_money_value(value):
    if value in (None, ""):
        return None
    return _to_int_money(value)


def _prepare_no_show_players_for_calculation(json_path: str, date_key: str, no_show_players: list[str]) -> None:
    """No-show players are excluded from ranking and kept as money-only records."""
    if len(no_show_players) == 0:
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if date_key not in data or "Spieler" not in data[date_key]:
        return

    players = data[date_key]["Spieler"]
    changed = False
    for pname in no_show_players:
        if pname not in players:
            continue
        old_money = players[pname].get("Geld") if isinstance(players[pname], dict) else None
        geld = _normalize_money_value(old_money)
        if players[pname] != {"Geld": geld}:
            players[pname] = {"Geld": geld}
            changed = True

    if changed:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def _append_no_show_players_with_daily_max(json_path: str, date_key: str, no_show_players: list[str]) -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if date_key not in data or "Spieler" not in data[date_key]:
        return

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

    no_show_players = []
    try:
        round_players = (day_data.get(date_key, {}) or {}).get("Spieler", {}) if isinstance(day_data, dict) else {}
        no_show_players = _extract_no_show_players(round_players)
    except Exception:
        no_show_players = []

    calc_dayhcps_for_players_before_date(date_key)

    apply_dayhcps_from_json(day_path, "json/DayHcp.json")

    # No-show Spieler vor der Tagesberechnung aus der Wertung nehmen.
    _prepare_no_show_players_for_calculation(day_path, date_key, no_show_players)

    # Runde für den Tag berechnen/aktualisieren
    update_round_for_date(day_path, date_key)

    # Geld berechnen
    calculate_money_for_players(day_path, date_key)

    # No-show Spieler mit Tages-Maximalbetrag nachträglich einfügen
    _append_no_show_players_with_daily_max(day_path, date_key, no_show_players)

    return "Tag erfolgreich berechnet."