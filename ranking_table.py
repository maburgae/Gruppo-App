# ranking_table.py
import json
import matplotlib.pyplot as plt
from pathlib import Path
from show_scorecard import show_scorecard
import math  # hinzugefügt für Score-Prüfung


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
    # Daten aufbauen (nur Spieler mit Platz / reguläre Wertung)
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

    # Spieler ohne Score aber mit Geld erfassen
    def _no_score(pdata: dict) -> bool:
        sc = pdata.get("Score")
        if not isinstance(sc, list) or len(sc) == 0:
            return True
        # alle Einträge None oder NaN?
        for v in sc:
            if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)):
                return False
        return True

    n_s_rows = []
    for name, pdata in players.items():
        if pdata.get("Platz") is not None:
            continue  # bereits in regulärer Liste
        geld = pdata.get("Geld")
        try:
            geld_val = float(geld) if isinstance(geld, (int, float, str)) and str(geld).strip() != "" else None
        except Exception:
            geld_val = None
        if geld_val is not None and geld_val != 0 and _no_score(pdata):
            # Format: Platz, Name, Net, G.Hcp, Bird, Par, Bog., Strich, Geld, L, LD, N2
            n_s_rows.append([
                "n/s",
                name,
                "",
                "",
                "",
                "",
                "",
                "",
                int(geld_val),  # Geld jetzt als Integer ohne Nachkommastellen
                "",
                "",
                ""
            ])

    # Sortieren nach Platz (aufsteigend), fehlende Werte ans Ende
    def _platz_key(row):
        p = row[0]
        return p if isinstance(p, int) else 9999
    rows.sort(key=_platz_key)

    # n/s Spieler unten anhängen
    if n_s_rows:
        rows.extend(n_s_rows)

    col_labels = ["P", "Name", "Net", "G.Hcp", "Bird", "Par", "Bog.", "Str.", "Geld", "L", "LD", "N2"]

    # Per-column width variables (tweak as needed)
    width = 0.15
    WIDTH_PLATZ = width*0.3
    WIDTH_NAME = width*1.3
    WIDTH_NETTO = width*1.2
    WIDTH_GHCP = width*1.3
    WIDTH_BIRDIES = width*1.2
    WIDTH_PARS = width
    WIDTH_BOGIES = width*1.3
    WIDTH_STRICH = width
    WIDTH_GELD = width*0.8
    WIDTH_L = width*0.5
    WIDTH_LD = width*0.6
    WIDTH_N2TP = width*0.6
    COL_WIDTHS = {
        "Platz": WIDTH_PLATZ,
        "Name": WIDTH_NAME,
        "Netto": WIDTH_NETTO,
        "G.Hcp": WIDTH_GHCP,
        "Birdies": WIDTH_BIRDIES,
        "Pars": WIDTH_PARS,
        "Bogies": WIDTH_BOGIES,
        "Strich": WIDTH_STRICH,
        "Geld": WIDTH_GELD,
        "L": WIDTH_L,
        "LD": WIDTH_LD,
        "N2TP": WIDTH_N2TP,
    }

    # Tabelle plotten
    fig, ax = plt.subplots(figsize=(7, len(rows) * 0.4 + 0))
    ax.axis("off")

    table = ax.table(
        cellText=rows,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(20)
    table.scale(1.2, 2.2)  # increase row height by 20%

    # Apply individual column widths
    try:
        n_rows = len(rows) + 1  # +1 for header row
        for j, label in enumerate(col_labels):
            width = COL_WIDTHS.get(label)
            if width is None:
                continue
            for i in range(n_rows):
                try:
                    table[(i, j)].set_width(width)
                except KeyError:
                    pass
    except Exception:
        pass

    if save_path:
        plt.savefig(save_path, dpi=100, bbox_inches="tight")
        print(f"[ok] Saved ranking table to {save_path}")
    if show:
        plt.show()
    plt.close(fig)


def main():
    json_file = "json/allrounds.json"
    with open(json_file, 'r') as file:
        data = json.load(file)
    for key in data.keys():
        #if key == "06.10.2025": # Beispiel: nur für ein bestimmtes Datum
            print(f"Key: {key}")
            players = load_round(json_file, key)
            #make_ranking_table(players, save_path=f"rankings/{key}.png", show=False)
            show_scorecard(json_file, key, save_path=f"scorecards/{key}.png", show=False)

if __name__ == "__main__":
    main()
