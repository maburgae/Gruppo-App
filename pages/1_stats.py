def render(st):
    # --- Yearly Average Hcp Plot ---
    import streamlit as st
    import plot_Hcp
    # Heading above the yearly average chart
    st.text("Jährliches Durchschnitts-Hcp pro Spieler")
    json_file = "json/allrounds.json"
    players = ["Marc", "Heiko", "Andy", "Buffy", "Bernie", "Markus", "Jens"]
    plot_Hcp.plot_yearly_avg_hcp(json_file, players, save_path=None, show=True)

    import json
    import matplotlib.pyplot as plt
    from collections import defaultdict
    from datetime import datetime
    import math

    # --- GruppoHcp Table ---
    def load_data(json_file: str):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        rounds = sorted(
            data.items(),
            key=lambda kv: datetime.strptime(kv[0], "%d.%m.%Y")
        )
        return rounds

    def get_last_six_hcps(rounds, players):
        results = {p: [] for p in players}
        for date_str, info in reversed(rounds):
            for p in players:
                if len(results[p]) >= 6:
                    continue
                stats = info.get("Spieler", {}).get(p)
                if stats:
                    h = stats.get("Gesp.Hcp")
                    if isinstance(h, int):
                        results[p].append((date_str, h))
        for p in players:
            results[p] = list(reversed(results[p]))
        return results

    def make_table_plot(results: dict[str, list[tuple[str, int]]], st, round_avg=True):
        players = list(results.keys())
        nrows = max(len(v) for v in results.values())
        table_data = []
        for i in range(nrows):
            row_vals = []
            for p in players:
                if i < len(results[p]):
                    date_str, hcp = results[p][i]
                    date_fmt = datetime.strptime(date_str, "%d.%m.%Y").strftime("%d.%m.%y")
                    # Remove mathtext formatting for table cells
                    val = f"{date_fmt}\n{hcp}"
                else:
                    val = "-"
                row_vals.append(val)
            table_data.append(row_vals)
        avg_vals = []
        for p in players:
            hcps = [hcp for _, hcp in results[p]]
            if hcps:
                avg = sum(hcps) / len(hcps)
                if round_avg:
                    avg = math.floor(avg + 0.5)
                    avg_str = str(avg)
                else:
                    avg_str = f"{avg:.2f}"
                # Remove mathtext formatting for average row
                avg_vals.append(avg_str)
            else:
                avg_vals.append("-")
        table_data.append(avg_vals)
        # Font size controls for GruppoHcp table
        BODY_FS = 30   # body font size (adjust here)
        HEADER_FS = BODY_FS  # column header font size (same as body)
        ROW_SCALE_X = 1.35
        ROW_SCALE_Y = 4.9 * 1.4  # +40% row height

        fig, ax = plt.subplots(figsize=(len(players) * 1.8, 9.5))
        ax.axis("off")
        table = ax.table(
            cellText=table_data,
            # rowLabels removed to hide the first column with 'Round x'
            colLabels=players,
            loc="center",
            cellLoc="center"
        )
        table.auto_set_font_size(False)
        table.set_fontsize(BODY_FS)  # body font size applied to all cells
        table.scale(ROW_SCALE_X, ROW_SCALE_Y)
        # Column headers font size (same as body)
        for j in range(len(players)):
            try:
                table[(-1, j)].get_text().set_fontsize(HEADER_FS)
            except Exception:
                pass
        # Ensure all non-average rows are normal weight
        try:
            nrows = len(table_data)
            ncols = len(players)
            for i in range(nrows - 1):  # all except last (Average)
                for j in range(ncols):
                    table[(i, j)].get_text().set_fontweight('normal')
        except Exception:
            pass
        # Make the last 'Average' row bold (cells only)
        try:
            avg_row_idx = len(table_data)  # last row index
            ncols = len(players)
            for j in range(ncols):
                table[(avg_row_idx, j)].get_text().set_fontweight('bold')
        except Exception:
            pass
        # Streamlit text heading above the table (no matplotlib title)
        st.text("GruppoHcp – Letzte 6 Runden")
        st.pyplot(fig)
        plt.close(fig)

    # Display GruppoHcp Table first
    gruppo_players = ["Marc", "Heiko", "Andy", "Bernie", "Buffy", "Jens", "Markus"]
    rounds = load_data("json/allrounds.json")
    results = get_last_six_hcps(rounds, gruppo_players)
    make_table_plot(results, st, round_avg=True)

    # --- Load data ---
    with open("json/allrounds.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    selected_players = ["Andy", "Marc", "Bernie", "Heiko", "Markus", "Buffy", "Jens"]

    # --- Helper to render generic tables with unified font sizes ---
    def display_table(headers, rows, title=None):
        # Font size controls for other tables
        BODY_FS = 35   # body font size (adjust here)
        HEADER_FS = BODY_FS  # header font size; same as body per requirement
        SCALE_X = 1.4
        SCALE_Y = 3.5

        fig, ax = plt.subplots(figsize=(13.5, 0.7 + 0.75 * len(rows)))
        ax.axis('off')
        table = ax.table(cellText=[headers] + rows, loc='center', cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(BODY_FS)  # apply body font size
        table.scale(SCALE_X, SCALE_Y)
        # Header row uses same font size as body
        ncols = len(headers)
        for j in range(ncols):
            try:
                table[(0, j)].get_text().set_fontsize(HEADER_FS)
            except Exception:
                pass
        if title:
            # Render heading via Streamlit instead of matplotlib title
            st.text(title)
        st.pyplot(fig)
        plt.close(fig)

    # --- 1+2. Combined Gesp.Hcp Table ---
    player_hcps = defaultdict(list)
    for round_obj in data.values():
        spieler = round_obj.get("Spieler", {})
        for name, pdata in spieler.items():
            hcp = pdata.get("Gesp.Hcp")
            if isinstance(hcp, int):
                player_hcps[name].append(hcp)
    combined_hcp_rows = []
    for name in selected_players:
        hcps = player_hcps.get(name, [])
        avg = sum(hcps) / len(hcps) if hcps else None
        min_hcp = min(hcps) if hcps else "No data"
        max_hcp = max(hcps) if hcps else "No data"
        combined_hcp_rows.append([
            name,
            f"{avg:.2f}" if avg is not None else "No data",
            min_hcp,
            max_hcp
        ])
    display_table(["Spieler", "Avg Gesp.Hcp", "Min Gesp.Hcp", "Max Gesp.Hcp"], combined_hcp_rows, "Gesp.Hcp Übersicht")

    # --- 4. Platz counts table ---
    platz_counts = defaultdict(lambda: defaultdict(int))
    all_players = set()
    for round_obj in data.values():
        spieler = round_obj.get("Spieler", {})
        min_platz = None
        for name, pdata in spieler.items():
            platz = pdata.get("Platz")
            if isinstance(platz, int):
                if min_platz is None or platz < min_platz:
                    min_platz = platz
        for name, pdata in spieler.items():
            platz = pdata.get("Platz")
            if isinstance(platz, int) and platz == min_platz and min_platz == 1:
                platz_counts[name][platz] += 1
            elif isinstance(platz, int) and 2 <= platz <= 8:
                platz_counts[name][platz] += 1
            all_players.add(name)
    filtered_players_sorted = [p for p in sorted(all_players) if p in selected_players]
    platz_rows = []
    col_sums = [0] * len(filtered_players_sorted)
    for platz in range(1, 9):
        row = [platz]
        for i, player in enumerate(filtered_players_sorted):
            val = platz_counts[player][platz]
            row.append(val)
            col_sums[i] += val
        platz_rows.append(row)
    # Removed last column 'Summe' per request
    display_table(["Platz"] + filtered_players_sorted, platz_rows, "Plätze Übersicht")

    # --- Combined Birdies, Pars, Bogies, Strich Table ---
    def get_avg_stat(stat_key):
        counts = defaultdict(int)
        rounds = defaultdict(int)
        for round_obj in data.values():
            spieler = round_obj.get("Spieler", {})
            for name, pdata in spieler.items():
                val = pdata.get(stat_key)
                if isinstance(val, int):
                    counts[name] += val
                    rounds[name] += 1
                elif val is not None:
                    rounds[name] += 1
        avgs = {}
        for player in selected_players:
            total = counts[player]
            r = rounds[player]
            avgs[player] = total / r if r else 0
        return avgs
    birdie_avgs = get_avg_stat("Birdies")
    pars_avgs = get_avg_stat("Pars")
    bogies_avgs = get_avg_stat("Bogies")
    strich_avgs = get_avg_stat("Strich")
    combined_rows = []
    for player in selected_players:
        combined_rows.append([
            player,
            f"{birdie_avgs[player]:.2f}",
            f"{pars_avgs[player]:.2f}",
            f"{bogies_avgs[player]:.2f}",
            f"{strich_avgs[player]:.2f}"
        ])
    display_table(["Spieler", "Birdies/R", "Pars/R", "Bogies/R", "Strich/R"], combined_rows, "Durchschnittswerte pro Runde")

if __name__ == "__main__":
    import streamlit as st
    render(st)
