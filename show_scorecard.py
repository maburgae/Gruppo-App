# show_scorecard.py
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def load_round(json_file: str, date_key: str):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    if date_key not in data:
        raise ValueError(f"Date {date_key} not found in {json_file}. Available: {list(data.keys())}")
    return data[date_key]


def show_scorecard(json_file: str, date_key: str, save_path=None, show=True):
    rd = load_round(json_file, date_key)

    pars = rd.get("Par", [])
    hcps = rd.get("Hcp", [])
    players = rd.get("Spieler", {})
    
    if pars is None:
        print(f"No scorecard:{date_key}")
        return 0

    holes = list(range(1, 19))

    # build table data
    row_labels = ["Hole", "Par", "Hcp"]
    rows = []
    rows.append([str(h) for h in holes])
    rows.append([str(p) if p is not None else "" for p in pars])
    rows.append([str(h) if h is not None else "" for h in hcps])
    for pname, pdata in players.items():
        # Scores row
        scores = []
        score_list = pdata.get("Score", [])
        score_list = list(score_list) + [None] * (18 - len(score_list))
        for sc in score_list:
            if sc is None:
                scores.append("x")
            else:
                scores.append(str(sc))
        rows.append(scores)
        row_labels.append(pname if pdata.get("DayHcp", "") == "" else f"{pname} ({pdata['DayHcp']})")
        # NettoP row
        nettopoints = []
        np_list = pdata.get("NettoP", [])
        np_list = list(np_list) + [None] * (18 - len(np_list))
        for np in np_list:
            if np is None:
                nettopoints.append("")
            else:
                nettopoints.append(str(np))
        rows.append(nettopoints)
        row_labels.append(f"{pname} NettoP")

    # Ensure all rows are exactly 18 columns
    for i in range(len(rows)):
        if len(rows[i]) > 18:
            rows[i] = rows[i][:18]
        elif len(rows[i]) < 18:
            rows[i] += [""] * (18 - len(rows[i]))

    col_labels = [""] + [str(h) for h in holes]
    cell_data = [[label] + row for label, row in zip(row_labels, rows)]

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.axis("off")

    # Reduce space above and below the table
    plt.subplots_adjust(top=0.85, bottom=0.15)

    table = ax.table(cellText=cell_data, cellLoc="center", loc="center")

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.5)

    # Make the first column wider
    for key, cell in table.get_celld().items():
        if key[1] == 0:
            cell.set_width(0.15)  # Increase width of first column

    # Make Par values bold
    for col_idx in range(1, len(holes)+1):
        cell = table[(1, col_idx)]  # Par row is index 1
        cell.set_text_props(weight='bold')

    # Coloring scores and nettopoints
    for row_idx, pname in enumerate(row_labels):
        if pname in ("Hole", "Par", "Hcp"):
            continue
        # Scores row
        if not pname.endswith("NettoP"):
            scores = players[pname.split(" (", 1)[0]]["Score"]
            for hole_idx in range(18):
                try:
                    cell = table[(row_idx, hole_idx + 1)]
                except KeyError:
                    continue
                sc = scores[hole_idx] if hole_idx < len(scores) else None
                par = pars[hole_idx] if hole_idx < len(pars) else None
                if sc is None:
                    cell.set_facecolor("red")
                    continue
                if par is None:
                    cell.set_facecolor("red")
                    continue
                if sc == par - 1:
                    cell.set_facecolor("violet")
                elif sc == par:
                    cell.set_facecolor("lightgreen")
                elif sc == par + 1:
                    pass
                elif sc == par + 2:
                    cell.set_facecolor("khaki")
                else:
                    cell.set_facecolor("red")
        # NettoP row: font color only, no background
        else:
            nettopoints = players[pname.replace(" NettoP","")]["NettoP"]
            for hole_idx in range(18):
                try:
                    cell = table[(row_idx, hole_idx + 1)]
                except KeyError:
                    continue
                np = nettopoints[hole_idx] if hole_idx < len(nettopoints) else None
                cell.set_facecolor("white")  # No background
                text = cell.get_text()
                text.set_weight('bold')  # Make NettoP numbers bold
                if np == 0:
                    text.set_color("red")
                elif np == 1:
                    text.set_color("yellow")
                elif np == 2:
                    text.set_color("black")
                elif isinstance(np, int) and np >= 3:
                    text.set_color("green")
                else:
                    text.set_color("black")

    plt.title(f"Scorecard – {date_key}", fontsize=14, pad=10)  # Reduce pad for less space above table

    # Add legend
    legend_elements = [
        Patch(facecolor="violet", label="Birdie"),
        Patch(facecolor="lightgreen", label="Par"),
        Patch(facecolor="none", edgecolor="black", label="Bogey"),
        Patch(facecolor="khaki", label="Double Bogey"),
        Patch(facecolor="red", label="Alles andere / x"),
    ]
    ax.legend(handles=legend_elements, loc="upper center", bbox_to_anchor=(0.5, -0.13),
              ncol=3, frameon=False)  # Move legend closer to table

    if save_path:
        plt.savefig(save_path, dpi=100, bbox_inches="tight")
        print(f"[ok] Saved to {save_path}")
    if show:
        plt.show()
    plt.close(fig)


def main():
    json_file = "json/allrounds.json"
    date_key = "07.09.2002"  # Schlüssel wie in deiner JSON
    show_scorecard(json_file, date_key, save_path="scorecard.png", show=True)


if __name__ == "__main__":
    main()
