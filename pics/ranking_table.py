# ranking_table.py
import json
import matplotlib.pyplot as plt
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
        ])

    # Sortieren nach Platz (aufsteigend)
    rows.sort(key=lambda r: r[0])

    col_labels = ["Platz", "Spieler", "Netto", "Ges.Hcp", "Birdies", "Pars", "Bogies", "Strich"]

    # Tabelle plotten
    fig, ax = plt.subplots(figsize=(5, len(rows) * 0.3 + 0))
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
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"[ok] Saved ranking table to {save_path}")
    if show:
        plt.show()
    plt.close(fig)


def main():
    json_file = "allrounds.json"
    date_key = "02.10.2023"  # gewünschtes Datum

    # Load JSON data from a file
    with open(json_file, 'r') as file:
        data = json.load(file)  # Parse the JSON file into a Python dictionary

    # Loop over all the first-level keys
    for key in data.keys():
        print(f"Key: {key}")
        players = load_round(json_file, key)
        make_ranking_table(players, save_path=f"rankings/{key}.png", show=False)

if __name__ == "__main__":
    main()
