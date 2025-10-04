# ranking_table.py
import json
import matplotlib.pyplot as plt
from pathlib import Path
from show_scorecard import show_scorecard


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


def make_ranking_table(players: dict, save_path: str | None = None, show: bool = True):
    # Daten aufbauen
    rows = []
    for name, pdata in players.items():
        if pdata.get("Platz") is None:
            continue
        rows.append([
            pdata.get("Platz", "-"),
            name,
            pdata.get("Netto", 0),
            pdata.get("Gesp.Hcp", 0),
            pdata.get("Birdies", 0),
            pdata.get("Pars", 0),
            pdata.get("Bogies", 0),
            pdata.get("Strich", 0),
            pdata.get("Geld", 0),
            pdata.get("Ladies", 0),
            pdata.get("LD", 0),
            pdata.get("N2TP", 0)
        ])

    # Sortieren nach Platz (aufsteigend)
    rows.sort(key=lambda r: r[0])

    col_labels = ["Platz", "Spieler", "Netto", "Ges.Hcp", "Birdies", "Pars", "Bogies", "Strich", "Geld", "Ladies", "LD", "N2TP"]

    # Tabelle plotten
    fig, ax = plt.subplots(figsize=(8, len(rows) * 0.4 + 0))
    ax.axis("off")

    table = ax.table(
        cellText=rows,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)

    # plt.title("Ranking of the Day", fontsize=14, pad=20)

    if save_path:
        plt.savefig(save_path, dpi=100, bbox_inches="tight")
        print(f"[ok] Saved ranking table to {save_path}")
    if show:
        plt.show()
    plt.close(fig)


def main():
    #json_file = "json/allrounds.json"
    json_file = "json/golf_df/golf_df.json"
    # Erwartung: genau ein Datumsschlüssel in golf_df.json
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

    date_key = keys[0]
    try:
        players = load_round(json_file, date_key)
    except Exception as e:
        return f"Fehler beim Laden der Runde: {e}"

    make_ranking_table(players, save_path=f"rankings/{date_key}.png", show=False)
    show_scorecard(json_file, date_key, save_path=f"scorecards/{date_key}.png", show=False)
    return "Stats generated!"

if __name__ == "__main__":
    main()

