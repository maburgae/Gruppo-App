def render(st):
    import json
    import matplotlib.pyplot as plt
    from datetime import datetime

    # Global CSS and helper for 15px text
    st.markdown(
        """
        <style>
        html, body, p, ol, ul, dl, span, div,
        [data-testid='stMarkdownContainer'] p,
        [data-testid='stMarkdownContainer'] span,
        h1, h2, h3, h4, h5, h6,
        [data-testid='stHeader'] h1 {
            font-size: 15px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    def text15(s: str):
        st.markdown(f"<span style='font-size:15px'>{s}</span>", unsafe_allow_html=True)

    text15("Urlaub")

    # Data source
    JSON_PATH = "json/allrounds.json"

    # Player order consistent with stats page
    selected_players = ["Andy", "Marc", "Bernie", "Heiko", "Markus", "Buffy", "Jens"]

    # Helpers
    def load_allrounds():
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_year(date_str: str) -> int | None:
        try:
            return datetime.strptime(date_str, "%d.%m.%Y").year
        except Exception:
            return None

    def years_with_par(data: dict) -> list[int]:
        years = set()
        for d, obj in data.items():
            y = get_year(d)
            if y is None:
                continue
            if obj.get("Par") is not None:
                years.add(y)
        return sorted(years)

    # Generic matplotlib-table renderer (same style as stats)
    def display_table(headers, rows, title=None):
        BODY_FS = 35
        HEADER_FS = BODY_FS
        SCALE_X = 1.4
        SCALE_Y = 3.5
        fig, ax = plt.subplots(figsize=(13.5, 0.7 + 0.75 * len(rows)))
        ax.axis('off')
        table = ax.table(cellText=[headers] + rows, loc='center', cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(BODY_FS)
        table.scale(SCALE_X, SCALE_Y)
        # header font size
        for j in range(len(headers)):
            try:
                table[(0, j)].get_text().set_fontsize(HEADER_FS)
            except Exception:
                pass
        if title:
            text15(title)
        st.pyplot(fig)
        plt.close(fig)

    # Load data and build year dropdown
    data = load_allrounds()
    years = years_with_par(data)
    if not years:
        st.info("Keine Jahre mit Par-Daten gefunden.")
        return

    year = st.selectbox("Jahr wählen", years, index=len(years) - 1)

    # Filter rounds of selected year (and with Par not None)
    rounds_for_year = []  # list of (date_str, obj)
    for d, obj in data.items():
        y = get_year(d)
        if y == year and obj.get("Par") is not None:
            rounds_for_year.append((d, obj))
    rounds_for_year.sort(key=lambda kv: datetime.strptime(kv[0], "%d.%m.%Y"))

    if not rounds_for_year:
        st.info("Keine Runden für das gewählte Jahr.")
        return

    # 1) Gespieltes Hcp der Spieler über dem Datum der Runden in diesem Jahr
    # Build table rows: each row starts with date, then Gesp.Hcp per player (or '-')
    rows = []
    for d, obj in rounds_for_year:
        date_fmt = datetime.strptime(d, "%d.%m.%Y").strftime("%d.%m")
        sp = obj.get("Spieler", {})
        row = [date_fmt]
        for p in selected_players:
            h = sp.get(p, {}).get("Gesp.Hcp")
            row.append(h if isinstance(h, int) else "-")
        rows.append(row)
    display_table(["Datum"] + selected_players, rows, "Gespieltes Hcp je Runde")

    # 2) Gesp.Hcp Übersicht (nur Runden im Jahr)
    player_hcps = {p: [] for p in selected_players}
    for _, obj in rounds_for_year:
        sp = obj.get("Spieler", {})
        for p in selected_players:
            h = sp.get(p, {}).get("Gesp.Hcp")
            if isinstance(h, int):
                player_hcps[p].append(h)
    rows = []
    for p in selected_players:
        vals = player_hcps[p]
        if vals:
            avg = sum(vals) / len(vals)
            rows.append([p, f"{avg:.2f}", min(vals), max(vals)])
        else:
            rows.append([p, "No data", "No data", "No data"])
    display_table(["Spieler", "Avg Gesp.Hcp", "Min Gesp.Hcp", "Max Gesp.Hcp"], rows, "Gesp.Hcp Übersicht (Jahr)")

    # 3) Durchschnittswerte pro Runde (Birdies/Pars/Bogies/Strich) – nur Jahr
    def yearly_avgs_for(stat_key: str) -> dict:
        counts = {p: 0 for p in selected_players}
        rounds = {p: 0 for p in selected_players}
        for _, obj in rounds_for_year:
            sp = obj.get("Spieler", {})
            for p in selected_players:
                val = sp.get(p, {}).get(stat_key)
                if isinstance(val, int):
                    counts[p] += val
                    rounds[p] += 1
                elif val is not None:
                    rounds[p] += 1
        return {p: (counts[p] / rounds[p] if rounds[p] else 0.0) for p in selected_players}

    bird = yearly_avgs_for("Birdies")
    pars = yearly_avgs_for("Pars")
    bog  = yearly_avgs_for("Bogies")
    stri = yearly_avgs_for("Strich")

    rows = []
    for p in selected_players:
        rows.append([p, f"{bird[p]:.2f}", f"{pars[p]:.2f}", f"{bog[p]:.2f}", f"{stri[p]:.2f}"])
    display_table(["Spieler", "Birdies/R", "Pars/R", "Bogies/R", "Strich/R"], rows, "Durchschnittswerte pro Runde (Jahr)")

    # 4) Sonderwertungen Übersicht (Jahr) – LD %, N2TP %, Ladies/R und Gesamt
    import math
    def is_present(v):
        if v is None:
            return False
        if isinstance(v, (int, float)):
            return not (isinstance(v, float) and math.isnan(v)) and v != 0
        if isinstance(v, str):
            return v.strip() != ""
        if isinstance(v, bool):
            return v
        return False

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

    ld_points = {p: 0.0 for p in selected_players}
    n2tp_points = {p: 0.0 for p in selected_players}
    ladies_sums = {p: 0.0 for p in selected_players}
    ladies_rounds_played = {p: 0 for p in selected_players}

    for _, obj in rounds_for_year:
        sp = obj.get("Spieler", {})
        for p in selected_players:
            pdata = sp.get(p, {})
            ld_points[p] += to_points(pdata.get("LD"))
            n2tp_points[p] += to_points(pdata.get("N2TP"))
            score = pdata.get("Score")
            played = isinstance(score, list) and len(score) > 0
            if played:
                ladies_rounds_played[p] += 1
                v = pdata.get("Ladies")
                if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)):
                    ladies_sums[p] += float(v)

    total_ld_points = sum(ld_points.values()) or 1.0
    total_n2tp_points = sum(n2tp_points.values()) or 1.0

    rows = []
    for p in selected_players:
        ld_pct = 100.0 * ld_points[p] / total_ld_points
        n2tp_pct = 100.0 * n2tp_points[p] / total_n2tp_points
        ladies_pr = (ladies_sums[p] / ladies_rounds_played[p]) if ladies_rounds_played[p] else 0.0
        rows.append([p, f"{ld_pct:.1f}%", f"{n2tp_pct:.1f}%", f"{ladies_pr:.2f}", f"{int(ladies_sums[p])}"])

    display_table(["Spieler", "LD %", "N2TP %", "Ladies/R", "L Ges."], rows, "Sonderwertungen Übersicht (Jahr)")

    # 5) Monetenkuchen (Jahr): Geld-Verteilung im Jahr
    geld_sums = {p: 0.0 for p in selected_players}
    for _, obj in rounds_for_year:
        sp = obj.get("Spieler", {})
        for p in selected_players:
            v = sp.get(p, {}).get("Geld")
            if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)):
                geld_sums[p] += float(v)

    labels, sizes = [], []
    try:
        cycle_colors = plt.rcParams['axes.prop_cycle'].by_key().get('color', [])
    except Exception:
        cycle_colors = []
    base_players_order = ["Marc", "Heiko", "Andy", "Buffy", "Bernie", "Markus", "Jens"]
    color_map = {name: cycle_colors[i] for i, name in enumerate(base_players_order) if i < len(cycle_colors)}
    colors = []

    total_geld = sum(geld_sums.values())
    text15("Monetenkuchen (Jahr)")
    if total_geld <= 0:
        st.info("Keine Geld-Daten für dieses Jahr vorhanden.")
    else:
        for p in selected_players:
            val = geld_sums[p]
            if val > 0:
                labels.append(p)
                sizes.append(val)
                colors.append(color_map.get(p))
        if not any(colors):
            colors = None
        fig, ax = plt.subplots(figsize=(8, 8))
        def fmt_euro(pct):
            abs_val = pct * sum(sizes) / 100.0
            return f"€{int(round(abs_val))}"
        ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct=fmt_euro,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(linewidth=1, edgecolor='white'),
            textprops=dict(fontsize=15)  # set label and autopct font sizes to 15
        )
        # total in center
        ax.text(0, 0, f"Gesamt\n€{int(round(total_geld))}", ha='center', va='center', fontsize=15, fontweight='bold')
        ax.axis('equal')
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # 6) Ranglisten und Scorecards (nur Runden des gewählten Jahres)
    import os
    from PIL import Image
    text15("Ranglisten und Scorecards (Jahr)")
    directory1 = "rankings/"
    directory2 = "scorecards/"

    # Show in reverse chronological order like Runden page
    for d, obj in sorted(rounds_for_year, key=lambda kv: datetime.strptime(kv[0], "%d.%m.%Y"), reverse=True):
        ort = obj.get("Ort", "")
        display_name = f"{d} ({ort})" if ort else d
        st.markdown(f"<b style='font-size:15px'>{display_name}</b>", unsafe_allow_html=True)

        # Ranking image
        rank_path = os.path.join(directory1, f"{d}.png")
        if os.path.exists(rank_path):
            try:
                image_rank = Image.open(rank_path)
                st.image(image_rank, width='stretch')
            except Exception:
                pass

        # Scorecards: prefer split images; fallback to single
        front_path = os.path.join(directory2, f"{d}_front.png")
        back_path = os.path.join(directory2, f"{d}_back.png")
        single_path = os.path.join(directory2, f"{d}.png")

        shown_any = False
        if os.path.exists(front_path):
            try:
                image_front = Image.open(front_path)
                st.image(image_front, width='stretch')
                shown_any = True
            except Exception:
                pass
        if os.path.exists(back_path):
            try:
                image_back = Image.open(back_path)
                st.image(image_back, width='stretch')
                shown_any = True
            except Exception:
                pass
        if not shown_any and os.path.exists(single_path):
            try:
                image_single = Image.open(single_path)
                st.image(image_single, width='stretch')
            except Exception:
                pass


if __name__ == "__main__":
    import streamlit as st
    render(st)
