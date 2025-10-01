def render(st):
    # --- Yearly Average Hcp Plot ---
    import streamlit as st
    import plot_Hcp

    # Global CSS to clamp typical text elements to 15px
    st.markdown(
        """
        <style>
        html, body, p, ol, ul, dl, span, div,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] span,
        h1, h2, h3, h4, h5, h6,
        [data-testid="stHeader"] h1 {
          font-size: 15px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Helper for 15px text outputs
    def text15(s: str):
        st.markdown(f"<span style='font-size:15px'>{s}</span>", unsafe_allow_html=True)

    # Heading above the yearly average chart
    text15("Jährliches Durchschnitts-Hcp pro Spieler")
    json_file = "json/allrounds.json"
    players = ["Marc", "Heiko", "Andy", "Buffy", "Bernie", "Markus", "Jens"]
    plot_Hcp.plot_yearly_avg_hcp(json_file, players, save_path=None, show=True)

    import json
    import matplotlib.pyplot as plt
    from collections import defaultdict
    from datetime import datetime
    import math

    # --- Jährlicher Mittelwert aller Gesp.Hcp (alle Spieler) ---
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            all_data = json.load(f)
        per_year_vals = defaultdict(list)
        # consider only these players for the yearly mean
        mean_players = ["Marc", "Heiko", "Andy", "Buffy", "Bernie", "Markus"]
        for date_str, round_obj in all_data.items():
            try:
                year = datetime.strptime(date_str, "%d.%m.%Y").year
            except ValueError:
                continue
            spieler = round_obj.get("Spieler", {})
            for name, pdata in spieler.items():
                if name not in mean_players:
                    continue
                h = pdata.get("Gesp.Hcp")
                if isinstance(h, (int, float)) and not (isinstance(h, float) and math.isnan(h)):
                    per_year_vals[year].append(float(h))
        years = sorted(per_year_vals.keys())
        means = [sum(per_year_vals[y]) / len(per_year_vals[y]) for y in years]
        if years:
            text15("Jährlicher Mittelwert Gesp.Hcp aller Spieler")
            fig, ax = plt.subplots(figsize=(10, 6))
            # Styling similar to Verlauf Hcp
            LABEL_FS = 16
            TICK_FS = 14
            LEGEND_FS = 14
            ax.plot(years, means, marker="o", linestyle="-", label="Mittelwert")
            # Trendlinie (linear)
            try:
                import numpy as np
                if len(years) >= 2:
                    coef = np.polyfit(years, means, 1)
                    trend = np.polyval(coef, years)
                    ax.plot(years, trend, linestyle="--", color="tab:red", linewidth=2, label="Trend")
            except Exception:
                pass
            ax.set_xlabel("Year", fontsize=LABEL_FS)
            ax.set_ylabel("Average Gesp.Hcp", fontsize=LABEL_FS)
            ax.tick_params(axis='both', labelsize=TICK_FS)
            ax.grid(True)
            ax.legend(fontsize=LEGEND_FS)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
    except Exception:
        pass

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
        text15("GruppoHcp – Letzte 6 Runden")
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
            text15(title)
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

    # --- Sonderwertungen: LD, N2TP, Ladies Übersicht ---
    def is_present(v):
        # consider values present if not None/empty and not zero for counting events
        if v is None:
            return False
        if isinstance(v, (int, float)):
            try:
                import math as _m
                if isinstance(v, float) and _m.isnan(v):
                    return False
            except Exception:
                pass
            return v != 0
        if isinstance(v, str):
            return v.strip() != ""
        return True

    # helper: value is defined if not None and not NaN (zero counts as defined)
    def has_defined_number(v):
        return (v is not None) and not (isinstance(v, float) and math.isnan(v))

    # helper: convert a metric value to numeric points
    def to_points(v) -> float:
        if v is None:
            return 0.0
        if isinstance(v, bool):
            return 1.0 if v else 0.0
        if isinstance(v, (int, float)):
            if isinstance(v, float) and math.isnan(v):
                return 0.0
            return float(v)
        if isinstance(v, str):
            return 1.0 if v.strip() != "" else 0.0
        return 0.0

    # Collect rounds where any player has LD/N2TP/Ladies present (optional filter; zero contributes nothing)
    ld_round_keys, n2tp_round_keys, ladies_round_keys = [], [], []
    for date_key, round_obj in data.items():
        sp = round_obj.get("Spieler", {})
        if any(is_present(sp.get(p, {}).get("LD")) for p in sp.keys()):
            ld_round_keys.append(date_key)
        if any(is_present(sp.get(p, {}).get("N2TP")) for p in sp.keys()):
            n2tp_round_keys.append(date_key)
        if any(has_defined_number(sp.get(p, {}).get("Ladies")) for p in sp.keys()):
            ladies_round_keys.append(date_key)

    # Aggregate points per player
    ld_points = {p: 0.0 for p in selected_players}
    n2tp_points = {p: 0.0 for p in selected_players}
    # Ladies aggregation based on played rounds (Score is a non-empty array)
    ladies_sums = {p: 0.0 for p in selected_players}
    ladies_rounds_played = {p: 0 for p in selected_players}

    # LD points
    for dk in ld_round_keys:
        sp = data[dk].get("Spieler", {})
        for p in selected_players:
            ld_points[p] += to_points(sp.get(p, {}).get("LD"))

    # N2TP points
    for dk in n2tp_round_keys:
        sp = data[dk].get("Spieler", {})
        for p in selected_players:
            n2tp_points[p] += to_points(sp.get(p, {}).get("N2TP"))

    # Ladies: per player, count played rounds (Score non-empty list) and sum Ladies over those rounds
    for date_key, round_obj in data.items():
        sp = round_obj.get("Spieler", {})
        for p in selected_players:
            pdata = sp.get(p, {})
            score = pdata.get("Score")
            played = isinstance(score, list) and len(score) > 0
            if played:
                ladies_rounds_played[p] += 1
                v = pdata.get("Ladies")
                if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)):
                    ladies_sums[p] += float(v)

    # Totals over the selected players so LD% + N2TP% sum to 100%
    total_ld_points = sum(ld_points.values()) or 1.0
    total_n2tp_points = sum(n2tp_points.values()) or 1.0

    specials_rows = []
    for p in selected_players:
        ld_pct = 100.0 * ld_points[p] / total_ld_points
        n2tp_pct = 100.0 * n2tp_points[p] / total_n2tp_points
        ladies_pr = (ladies_sums[p] / ladies_rounds_played[p]) if ladies_rounds_played[p] else 0.0
        specials_rows.append([
            p,
            f"{ld_pct:.1f}%",
            f"{n2tp_pct:.1f}%",
            f"{ladies_pr:.2f}",
            f"{int(ladies_sums[p])}"
        ])

    display_table(["Spieler", "LD %", "N2TP %", "Ladies/R", "L Ges."], specials_rows, "Sonderwertungen Übersicht")

    # --- Kuchendiagramm: Geld-Verteilung ---
    # Sum Geld per selected player
    geld_sums = {p: 0.0 for p in selected_players}
    for round_obj in data.values():
        sp = round_obj.get("Spieler", {})
        for p in selected_players:
            v = sp.get(p, {}).get("Geld")
            if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)):
                geld_sums[p] += float(v)

    # Filter players with > 0 geld to avoid zero-slices
    labels = []
    sizes = []
    # Build color mapping to match Verlauf Hcp colors (matplotlib default cycle order by initial players list)
    try:
        cycle_colors = plt.rcParams['axes.prop_cycle'].by_key().get('color', [])
    except Exception:
        cycle_colors = []
    base_players_order = ["Marc", "Heiko", "Andy", "Buffy", "Bernie", "Markus", "Jens"]
    color_map = {}
    for idx, name in enumerate(base_players_order):
        if idx < len(cycle_colors):
            color_map[name] = cycle_colors[idx]
    colors = []

    total_geld = sum(geld_sums.values())
    if total_geld <= 0:
        text15("Geld-Verteilung (Summe)")
        st.info("Keine Geld-Daten vorhanden.")
    else:
        for p in selected_players:
            val = geld_sums[p]
            if val > 0:
                labels.append(p)
                sizes.append(val)
                colors.append(color_map.get(p))
        # Ensure colors list populated (fallback)
        if not any(colors):
            colors = None
        text15("Monetenkuchen Alltime")
        fig, ax = plt.subplots(figsize=(8, 8))
        def fmt_euro(pct):
            abs_val = pct * sum(sizes) / 100.0
            return f"€{int(round(abs_val))}"
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct=fmt_euro,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(linewidth=1, edgecolor='white'),
            textprops=dict(fontsize=15)  # Ensure all pie texts (labels + autopct) are 15
        )
        # Add total sum in the center of the pie
        total_label = f"Gesamt\n€{int(round(total_geld))}"
        ax.text(0, 0, total_label, ha='center', va='center', fontsize=15, fontweight='bold')
        ax.axis('equal')
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

if __name__ == "__main__":
    import streamlit as st
    render(st)
