# gruppo_hcp.py
import json
import matplotlib.pyplot as plt
from datetime import datetime
import math

def load_data(json_file: str):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    # sort rounds by real date (now stored as dd.mm.yyyy)
    rounds = sorted(
        data.items(),
        key=lambda kv: datetime.strptime(kv[0], "%d.%m.%Y")
    )
    return rounds


def get_last_six_hcps(rounds, players):
    results = {p: [] for p in players}

    # iterate newest → oldest
    for date_str, info in reversed(rounds):
        for p in players:
            if len(results[p]) >= 6:
                continue
            stats = info.get("Spieler", {}).get(p)
            if stats:
                h = stats.get("Gesp.Hcp")
                if isinstance(h, int):
                    results[p].append((date_str, h))

    # oldest → newest for display
    for p in players:
        results[p] = list(reversed(results[p]))
    return results


def make_table_plot(results: dict[str, list[tuple[str, int]]], save_path=None, show=True, round_avg=True):
    players = list(results.keys())
    nrows = max(len(v) for v in results.values())
    row_labels = []
    table_data = []

    # build rows for up to 6 rounds
    for i in range(nrows):
        row_label = None
        row_vals = []
        for p in players:
            if i < len(results[p]):
                date_str, hcp = results[p][i]
                # input date is dd.mm.yyyy → display as dd.mm.yy
                date_fmt = datetime.strptime(date_str, "%d.%m.%Y").strftime("%d.%m.%y")
                # bold Hcp values
                val = f"{date_fmt}\n" + r"$\mathbf{" + str(hcp) + "}$"
                if not row_label:
                    row_label = f"Round {i+1}"
            else:
                val = "-"
            row_vals.append(val)
        row_labels.append(row_label)
        table_data.append(row_vals)

    # add average row
    avg_vals = []
    for p in players:
        hcps = [hcp for _, hcp in results[p]]
        if hcps:
            avg = sum(hcps) / len(hcps)
            if round_avg:
                # commercial rounding: always round .5 up
                avg = math.floor(avg + 0.5)
                avg_str = str(avg)
            else:
                avg_str = f"{avg:.2f}"
            avg_vals.append(r"$\mathbf{" + avg_str + "}$")
        else:
            avg_vals.append("-")
    row_labels.append("Average")
    table_data.append(avg_vals)

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(len(players) * 1.5, 6))
    ax.axis("off")

    table = ax.table(
        cellText=table_data,
        rowLabels=row_labels,
        colLabels=players,
        loc="center",
        cellLoc="center"
    )

    # formatting
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(0.9, 2.0)  # smaller width, double row height

    plt.title("GruppoHcp – Last 6 Rounds per Player", fontsize=12, pad=20)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"[ok] Saved plot to {save_path}")
    if show:
        plt.show()
    plt.close(fig)


def main():
    json_file = "allrounds.json"
    players = ["Marc", "Heiko", "Andy", "Bernie", "Buffy", "Jens", "Markus"]

    rounds = load_data(json_file)
    results = get_last_six_hcps(rounds, players)
    make_table_plot(results, save_path="gruppo_hcp.png", show=True, round_avg=True)


if __name__ == "__main__":
    main()
