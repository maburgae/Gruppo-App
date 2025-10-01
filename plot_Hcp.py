# plot_yearly_avg_hcp.py
import json
import matplotlib.pyplot as plt
from datetime import datetime
from statistics import mean
import streamlit as st


def collect_yearly_avg_hcp(json_file: str, players: list[str]) -> dict[str, tuple[list[int], list[float]]]:
    """
    Returns a dict: player -> (years[], avg_hcps[])
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    per_player_year = {p: {} for p in players}

    for date_str, round_data in data.items():
        try:
            # new format dd.mm.yyyy
            year = datetime.strptime(date_str, "%d.%m.%Y").year
        except ValueError:
            continue
        players_block = round_data.get("Spieler", {})
        for p in players:
            stats = players_block.get(p)
            if not stats:
                continue
            h = stats.get("Gesp.Hcp")
            if isinstance(h, int):
                per_player_year[p].setdefault(year, []).append(h)

    result = {}
    for p in players:
        if not per_player_year[p]:
            result[p] = ([], [])
            continue
        years = sorted(per_player_year[p].keys())
        avgs = [mean(per_player_year[p][y]) for y in years]
        result[p] = (years, avgs)
    return result


def plot_yearly_avg_hcp(json_file: str, players: list[str], save_path: str | None = None, show: bool = True):
    """
    Plot yearly average Hcp for the given players.
    If save_path is given, saves the plot to file.
    If show=True, displays the plot window.
    """
    data = collect_yearly_avg_hcp(json_file, players)

    fig, ax = plt.subplots(figsize=(10, 6))

    for p in players:
        years, avgs = data[p]
        if years:
            ax.plot(years, avgs, marker="o", linestyle="-", label=p)
        else:
            print(f"[info] No Hcp data for '{p}', skipping.")

    # --- Font size controls for the Yearly Average diagram ---
    TITLE_FS = 20   # Title font size (adjust here)
    LABEL_FS = 16   # Axis label font size (adjust here)
    TICK_FS = 14    # Axis tick font size (adjust here)
    LEGEND_FS = 14  # Legend font size (adjust here)

    ax.set_xlabel("Year", fontsize=LABEL_FS)
    ax.set_ylabel("Average Hcp", fontsize=LABEL_FS)
    ax.set_title("Yearly Average Hcp per Player", fontsize=TITLE_FS)

    # Ticks font size
    ax.tick_params(axis='both', labelsize=TICK_FS)

    ax.grid(True)
    ax.legend(fontsize=LEGEND_FS)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"[ok] Plot saved to: {save_path}")

    if show:
        # plt.show()
        st.pyplot(fig)

    # Close the figure to free memory
    plt.close(fig)


def main():
    json_file = "allrounds.json"   # <-- set your file name here
    players = ["Marc", "Heiko", "Andy","Buffy", "Bernie","Markus", "Jens"]  # <-- choose players here
    save_path = "hcp_yearly.png"      # <-- set to None if you don't want to save
    show = True                       # <-- set False if you only want to save

    plot_yearly_avg_hcp(json_file, players, save_path, show)


if __name__ == "__main__":
    main()
