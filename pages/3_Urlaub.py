def render(st):
    import json
    import matplotlib.pyplot as plt
    from datetime import datetime
    from html import escape

    # Global CSS and helper for 15px text
    st.markdown(
        """
        <style>
        [data-testid='stAppViewContainer'] [data-testid='stMain'] p,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] ol,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] ul,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] dl,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] span,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] div,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] [data-testid='stMarkdownContainer'] p,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] [data-testid='stMarkdownContainer'] span,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] h1,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] h2,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] h3,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] h4,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] h5,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] h6,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] [data-testid='stHeader'] h1 {
            font-size: 17px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    def text15(s: str):
        st.markdown(f"<span style='font-size:17px'>{s}</span>", unsafe_allow_html=True)

    # HTML scorecard style (same layout as Runden)
    st.markdown(
        """
        <style>
        .yr-table {
            border-collapse: collapse;
            width: auto;
            margin: 0.3rem 0 1rem 0;
            table-layout: auto;
        }
        .yr-table th, .yr-table td {
            border: 1px solid #d5d5d5;
            padding: 0.16rem 0.2rem;
            text-align: center;
            font-size: 17px;
            line-height: 1.15;
            color: #111;
            background: #fff;
            white-space: nowrap;
        }
        .yr-table th {
            background: #f2f2f2;
            font-weight: 700;
        }
        .yr-table td:first-child,
        .yr-table th:first-child {
            text-align: left;
            font-weight: 700;
        }
        .rt-table {
            border-collapse: collapse;
            width: auto;
            margin: 0.3rem 0 1rem 0;
            table-layout: fixed;
        }
        .rt-table th, .rt-table td {
            border: 1px solid #d5d5d5;
            padding: 0.12rem 0.16rem;
            text-align: center;
            font-size: 17px;
            line-height: 1.1;
            color: #111;
            background: #fff;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .rt-table th {
            background: #f2f2f2;
            font-weight: 700;
        }
        .rt-table th:nth-child(2),
        .rt-table td:nth-child(2) {
            width: 10%;
            min-width: 10%;
            max-width: 10%;
            text-align: left;
        }
        .rt-table th:nth-child(1),
        .rt-table td:nth-child(1),
        .rt-table th:nth-child(3),
        .rt-table td:nth-child(3),
        .rt-table th:nth-child(4),
        .rt-table td:nth-child(4),
        .rt-table th:nth-child(10),
        .rt-table td:nth-child(10),
        .rt-table th:nth-child(11),
        .rt-table td:nth-child(11),
        .rt-table th:nth-child(12),
        .rt-table td:nth-child(12) {
            width: 6.5%;
        }
        .rt-table th:nth-child(5),
        .rt-table td:nth-child(5),
        .rt-table th:nth-child(6),
        .rt-table td:nth-child(6),
        .rt-table th:nth-child(7),
        .rt-table td:nth-child(7),
        .rt-table th:nth-child(8),
        .rt-table td:nth-child(8),
        .rt-table th:nth-child(9),
        .rt-table td:nth-child(9) {
            width: 7.4%;
        }
        .sc-table {
            border-collapse: collapse;
            width: auto;
            margin: 0.3rem 0 1rem 0;
            table-layout: auto;
        }
        .sc-table th, .sc-table td {
            border: 1px solid #d5d5d5;
            padding: 0.12rem 0.16rem;
            text-align: center;
            font-size: 17px;
            line-height: 1.1;
            color: #111;
            background: #fff;
        }
        .sc-table th {
            background: #f2f2f2;
            font-weight: 700;
        }
        .sc-table td.left {
            text-align: left;
            white-space: nowrap;
            width: 1%;
            min-width: 0;
            max-width: none;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .sc-table th.hole-col,
        .sc-table td:not(:first-child):not(.sum-col):not(:last-child) {
            width: 1.05rem;
            min-width: 1.05rem;
            max-width: 1.05rem;
        }
        .sc-table th.sum-col,
        .sc-table td.sum-col {
            width: 1.45rem;
            min-width: 1.45rem;
            max-width: 1.45rem;
            background: #f7f7f7;
            font-weight: 700;
        }
        .sc-table th:last-child,
        .sc-table td:last-child {
            width: 1.55rem;
            min-width: 1.55rem;
            max-width: 1.55rem;
        }
        .sc-table td.label {
            font-weight: 700;
            background: #fafafa;
        }
        .sc-table td.player {
            font-weight: 700;
        }
        .sc-table td.netto {
            font-weight: 700;
            background: #fafafa;
        }
        .sc-table tr.sep td {
            border: none;
            height: 0.25rem;
            padding: 0;
            background: transparent;
        }
        .sc-table tr.sep-strong td {
            border: none;
            border-top: 2px solid #9d9d9d;
            height: 0.35rem;
            padding: 0;
            background: transparent;
        }
        @media (max-width: 900px) {
            .yr-table {
                width: 100% !important;
                table-layout: fixed !important;
                margin-left: 0 !important;
                margin-right: 0 !important;
            }
            .yr-table th,
            .yr-table td {
                font-size: clamp(11px, 3.4vw, 15px) !important;
                padding: 0.12rem 0.14rem !important;
                white-space: normal !important;
                word-break: break-word !important;
            }
            .rt-table {
                width: 100% !important;
                table-layout: fixed !important;
                margin-left: 0 !important;
                margin-right: 0 !important;
            }
            .rt-table th,
            .rt-table td,
            .sc-table th,
            .sc-table td {
                color: #111 !important;
            }
            .rt-table th,
            .rt-table td {
                font-size: clamp(11px, 3.4vw, 15px) !important;
                padding: 0.12rem 0.14rem !important;
            }
            .rt-table th:nth-child(2),
            .rt-table td:nth-child(2) {
                width: 10% !important;
                min-width: 10% !important;
                max-width: 10% !important;
            }
            .sc-table {
                table-layout: fixed !important;
                width: 100% !important;
                margin-left: 0 !important;
                margin-right: 0 !important;
            }
            .sc-table th,
            .sc-table td {
                padding: 0.08rem 0.10rem !important;
                font-size: 11px !important;
                box-sizing: border-box !important;
                color: #111 !important;
            }
            .sc-table td.left,
            .sc-table th:first-child {
                width: 14% !important;
                min-width: 14% !important;
                max-width: 14% !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }
            .sc-table th.hole-col,
            .sc-table td:not(:first-child):not(.sum-col):not(:last-child) {
                width: 3.8% !important;
                min-width: 3.8% !important;
                max-width: 3.8% !important;
            }
            .sc-table th.sum-col,
            .sc-table td.sum-col,
            .sc-table th:last-child,
            .sc-table td:last-child {
                width: 5.866% !important;
                min-width: 5.866% !important;
                max-width: 5.866% !important;
            }
        }
        @media (max-width: 900px) and (orientation: landscape) {
            .yr-table th,
            .yr-table td,
            .rt-table th,
            .rt-table td,
            .sc-table th,
            .sc-table td {
                font-size: 13px !important;
                padding: 0.08rem 0.10rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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

    def _fmt_cell(val):
        if val is None:
            return ""
        return str(val)

    def _safe_int(val):
        try:
            return int(val)
        except Exception:
            return None

    def _score_bg(score, par):
        if score is None or par is None:
            return "#ffb3b3"
        if score == par - 1:
            return "#d1b3ff"
        if score == par:
            return "#b9f6b9"
        if score == par + 2:
            return "#ffe08a"
        if score > par + 2:
            return "#ff9a9a"
        return "#ffffff"

    def _netto_style(netto):
        if netto is None:
            return "color:#111;font-weight:700;"
        if netto == 0:
            return "color:#cc0000;font-weight:700;"
        if netto == 1:
            return "color:#d4a106;font-weight:700;"
        if netto == 2:
            return "color:#111;font-weight:700;"
        if netto >= 3:
            return "color:#178a2f;font-weight:700;"
        return "color:#111;font-weight:700;"

    def _render_ranking_html(players):
        cols = ["P", "Name", "Net", "Hcp", "Bird", "Par", "Bog.", "Str.", "Geld", "L"]

        rows = []
        for name, pdata in players.items():
            rows.append({
                "platz": pdata.get("Platz"),
                "name": name,
                "netto": pdata.get("Netto"),
                "gesp": pdata.get("Gesp.Hcp"),
                "bird": pdata.get("Birdies"),
                "par": pdata.get("Pars"),
                "bog": pdata.get("Bogies"),
                "strich": pdata.get("Strich"),
                "geld": pdata.get("Geld"),
                "ladies": pdata.get("Ladies"),
            })

        def _sort_key(r):
            p = r["platz"]
            return (p is None, p if isinstance(p, int) else 9999, r["name"])

        rows.sort(key=_sort_key)

        html = []
        html.append("<table class='rt-table'>")
        html.append("<thead><tr>" + "".join(f"<th>{escape(c)}</th>" for c in cols) + "</tr></thead>")
        html.append("<tbody>")
        for r in rows:
            html.append("<tr>")
            html.append(f"<td>{escape(_fmt_cell(r['platz']))}</td>")
            html.append(f"<td style='text-align:left;font-weight:700'>{escape(_fmt_cell(r['name']))}</td>")
            html.append(f"<td>{escape(_fmt_cell(r['netto']))}</td>")
            html.append(f"<td>{escape(_fmt_cell(r['gesp']))}</td>")
            html.append(f"<td>{escape(_fmt_cell(r['bird']))}</td>")
            html.append(f"<td>{escape(_fmt_cell(r['par']))}</td>")
            html.append(f"<td>{escape(_fmt_cell(r['bog']))}</td>")
            html.append(f"<td>{escape(_fmt_cell(r['strich']))}</td>")
            html.append(f"<td>{escape(_fmt_cell(r['geld']))}</td>")
            html.append(f"<td>{escape(_fmt_cell(r['ladies']))}</td>")
            html.append("</tr>")
        html.append("</tbody></table>")
        return "".join(html)

    def _is_special_mark(v):
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return v != 0
        if isinstance(v, str):
            s = v.strip()
            return s != "" and s != "0"
        return False

    def _render_specials_line(players):
        ld_names = [name for name, pdata in players.items() if _is_special_mark((pdata or {}).get("LD"))]
        n2_names = [name for name, pdata in players.items() if _is_special_mark((pdata or {}).get("N2TP"))]
        ld_txt = ", ".join(ld_names) if ld_names else "-"
        n2_txt = ", ".join(n2_names) if n2_names else "-"
        return (
            "<div style='font-size:15px;margin:0.15rem 0 0.55rem 0'>"
            f"Longest Drive: <b>{escape(ld_txt)}</b>&nbsp;&nbsp;&nbsp;&nbsp;"
            f"N2TP: <b>{escape(n2_txt)}</b>"
            "</div>"
        )

    def _has_played_round(pdata) -> bool:
        if not isinstance(pdata, dict):
            return False
        score = pdata.get("Score")
        if isinstance(score, list) and any(isinstance(v, (int, float)) for v in score):
            return True

        # Legacy rounds (e.g. early years) can miss hole-by-hole scores but still
        # contain valid participation metrics.
        legacy_play_fields = ("Platz", "Netto", "Gesp.Hcp", "Birdies", "Pars", "Bogies", "Strich")
        return any(pdata.get(k) is not None for k in legacy_play_fields)

    def _render_scorecard_html(round_data):
        holes = list(range(1, 19))
        pars = list(round_data.get("Par", []) or [])
        hcps = list(round_data.get("Hcp", []) or [])
        players = round_data.get("Spieler", {}) or {}

        while len(pars) < 18:
            pars.append(None)
        while len(hcps) < 18:
            hcps.append(None)

        course_par_total = 0
        course_par_has = False
        for p in pars[:18]:
            pv = _safe_int(p)
            if pv is not None:
                course_par_total += pv
                course_par_has = True

        html = []
        html.append("<table class='sc-table'>")
        html.append("<thead><tr><th>Hole</th>")
        for h in holes[:9]:
            html.append(f"<th class='hole-col'>{h}</th>")
        html.append("<th class='sum-col'>F</th>")
        for h in holes[9:]:
            html.append(f"<th class='hole-col'>{h}</th>")
        html.append("<th class='sum-col'>B</th><th class='sum-col'>Tot</th></tr></thead><tbody>")

        def _sum_slice(values, start, end):
            s = 0
            has_value = False
            for v in values[start:end]:
                iv = _safe_int(v)
                if iv is not None:
                    s += iv
                    has_value = True
            return s if has_value else None

        def _fixed_row(label, values):
            html.append("<tr>")
            html.append(f"<td class='left label'>{escape(label)}</td>")
            for v in values[:9]:
                cell_style = " style='font-weight:700'" if label == "Hole" else ""
                html.append(f"<td{cell_style}>{escape(_fmt_cell(v))}</td>")
            if label in ("Hole", "Hcp"):
                out_sum = None
            else:
                out_sum = _sum_slice(values, 0, 9)
            html.append(f"<td class='sum-col'>{escape(_fmt_cell(out_sum))}</td>")
            for v in values[9:18]:
                cell_style = " style='font-weight:700'" if label == "Hole" else ""
                html.append(f"<td{cell_style}>{escape(_fmt_cell(v))}</td>")
            if label in ("Hole", "Hcp"):
                in_sum = None
                tot_sum = None
            else:
                in_sum = _sum_slice(values, 9, 18)
                tot_sum = _sum_slice(values, 0, 18)
            html.append(f"<td class='sum-col'>{escape(_fmt_cell(in_sum))}</td>")
            html.append(f"<td class='sum-col'>{escape(_fmt_cell(tot_sum))}</td></tr>")

        _fixed_row("Par", pars)
        _fixed_row("Hcp", hcps)
        html.append("<tr class='sep-strong'><td colspan='23'></td></tr>")

        for name, pdata in players.items():
            scores = list(pdata.get("Score", []) or [])
            nettos = list(pdata.get("NettoP", []) or [])
            while len(scores) < 18:
                scores.append(None)
            while len(nettos) < 18:
                nettos.append(None)

            if not any(isinstance(v, (int, float)) for v in scores):
                continue

            day_hcp = pdata.get("DayHcp")
            name_label = name if day_hcp in (None, "") else f"{name} ({day_hcp})"

            html.append("<tr>")
            html.append(f"<td class='left player'>{escape(name_label)}</td>")
            front_sum = 0
            back_sum = 0
            front_has = False
            back_has = False
            for hole_idx in range(9):
                sc = _safe_int(scores[hole_idx])
                par = _safe_int(pars[hole_idx])
                bg = _score_bg(sc, par)
                txt = "x" if scores[hole_idx] in (None, 0) else _fmt_cell(scores[hole_idx])
                html.append(f"<td style='background:{bg};color:#111;font-weight:700'>{escape(txt)}</td>")
                if sc is not None:
                    front_sum += sc
                    front_has = True
            html.append(f"<td class='sum-col' style='font-weight:700'>{escape(_fmt_cell(front_sum if front_has else None))}</td>")
            for hole_idx in range(9, 18):
                sc = _safe_int(scores[hole_idx])
                par = _safe_int(pars[hole_idx])
                bg = _score_bg(sc, par)
                txt = "x" if scores[hole_idx] in (None, 0) else _fmt_cell(scores[hole_idx])
                html.append(f"<td style='background:{bg};color:#111;font-weight:700'>{escape(txt)}</td>")
                if sc is not None:
                    back_sum += sc
                    back_has = True
            gesp_hcp = _safe_int(pdata.get("Gesp.Hcp"))
            total_target = (gesp_hcp + course_par_total) if (gesp_hcp is not None and course_par_has) else None
            html.append(f"<td class='sum-col' style='font-weight:700'>{escape(_fmt_cell(back_sum if back_has else None))}</td>")
            html.append(f"<td class='sum-col' style='font-weight:700'>{escape(_fmt_cell(total_target))}</td></tr>")

            html.append("<tr>")
            html.append("<td class='left netto'>Netto</td>")
            front_net = 0
            back_net = 0
            front_net_has = False
            back_net_has = False
            for hole_idx in range(9):
                nv = _safe_int(nettos[hole_idx])
                style = _netto_style(nv)
                html.append(f"<td style='{style}'>{escape(_fmt_cell(nv))}</td>")
                if nv is not None:
                    front_net += nv
                    front_net_has = True
            html.append(f"<td class='sum-col' style='font-weight:700'>{escape(_fmt_cell(front_net if front_net_has else None))}</td>")
            for hole_idx in range(9, 18):
                nv = _safe_int(nettos[hole_idx])
                style = _netto_style(nv)
                html.append(f"<td style='{style}'>{escape(_fmt_cell(nv))}</td>")
                if nv is not None:
                    back_net += nv
                    back_net_has = True
            net_total = (front_net if front_net_has else 0) + (back_net if back_net_has else 0)
            net_total_has = front_net_has or back_net_has
            html.append(f"<td class='sum-col' style='font-weight:700'>{escape(_fmt_cell(back_net if back_net_has else None))}</td>")
            html.append(f"<td class='sum-col' style='font-weight:700'>{escape(_fmt_cell(net_total if net_total_has else None))}</td></tr>")

            html.append("<tr class='sep'>")
            html.append("<td colspan='23'></td>")
            html.append("</tr>")

        html.append("</tbody></table>")
        return "".join(html)

    def _has_player_entries(obj: dict) -> bool:
        players = obj.get("Spieler") if isinstance(obj, dict) else None
        return isinstance(players, dict) and len(players) > 0

    def years_with_players(data: dict) -> list[int]:
        years = set()
        for d, obj in data.items():
            y = get_year(d)
            if y is None:
                continue
            if _has_player_entries(obj):
                years.add(y)
        return sorted(years)

    # Generic HTML table renderer for yearly summaries
    def display_table(headers, rows, title=None):
        if title:
            text15(title)
        html = []
        html.append("<table class='yr-table'>")
        html.append("<thead><tr>" + "".join(f"<th>{escape(_fmt_cell(h))}</th>" for h in headers) + "</tr></thead>")
        html.append("<tbody>")
        for row in rows:
            html.append("<tr>" + "".join(f"<td>{escape(_fmt_cell(cell))}</td>" for cell in row) + "</tr>")
        html.append("</tbody></table>")
        st.markdown("".join(html), unsafe_allow_html=True)

    # Load data and destinations, build year dropdown (newest first) with destination labels
    data = load_allrounds()
    try:
        with open("json/Destinations.json", "r", encoding="utf-8") as f:
            destinations = json.load(f)
    except Exception:
        destinations = {}

    years = years_with_players(data)
    if not years:
        st.info("Keine Jahre mit Spieler-Eintraegen gefunden.")
        return

    year_options = sorted(years, reverse=True)

    def fmt_year(y: int) -> str:
        dest = destinations.get(str(y))
        return f"{y} - {dest}" if dest else str(y)

    year = st.selectbox("Jahr wählen", year_options, index=0, format_func=fmt_year)

    # Filter rounds of selected year that contain player entries
    rounds_for_year = []  # list of (date_str, obj)
    for d, obj in data.items():
        y = get_year(d)
        if y == year and _has_player_entries(obj):
            rounds_for_year.append((d, obj))
    rounds_for_year.sort(key=lambda kv: datetime.strptime(kv[0], "%d.%m.%Y"))

    if not rounds_for_year:
        st.info("Keine Runden für das gewählte Jahr.")
        return

    # Teilnehmerliste: nur Spieler mit tatsächlicher Teilnahme (numerischer Score) im gewählten Jahr
    participants_set = set()
    for _, obj in rounds_for_year:
        sp = obj.get("Spieler", {}) or {}
        for pname, pdata in sp.items():
            if _has_played_round(pdata):
                participants_set.add(pname)

    # Erst bevorzugte Reihenfolge, dann weitere Teilnehmer alphabetisch
    year_players = [p for p in selected_players if p in participants_set]
    year_players.extend(sorted(participants_set - set(selected_players)))

    if not year_players:
        st.info("Keine teilnehmenden Spieler für das gewählte Jahr gefunden.")
        return

    # 1) Gespieltes Hcp der Spieler über dem Datum der Runden in diesem Jahr
    # Build table rows: each row starts with date, then Gesp.Hcp per player (or '-')
    rows = []
    for d, obj in rounds_for_year:
        date_fmt = datetime.strptime(d, "%d.%m.%Y").strftime("%d.%m")
        sp = obj.get("Spieler", {})
        row = [date_fmt]
        for p in year_players:
            h = sp.get(p, {}).get("Gesp.Hcp")
            row.append(h if isinstance(h, int) else "-")
        rows.append(row)
    display_table(["Datum"] + year_players, rows, "Gespieltes Hcp je Runde")

    # 2) Durchschnittswerte pro Runde (inkl. Avg Gesp.Hcp) – nur Jahr
    player_hcps = {p: [] for p in year_players}
    for _, obj in rounds_for_year:
        sp = obj.get("Spieler", {})
        for p in year_players:
            h = sp.get(p, {}).get("Gesp.Hcp")
            if isinstance(h, int):
                player_hcps[p].append(h)

    def yearly_avgs_for(stat_key: str) -> dict:
        counts = {p: 0 for p in year_players}
        rounds = {p: 0 for p in year_players}
        for _, obj in rounds_for_year:
            sp = obj.get("Spieler", {})
            for p in year_players:
                val = sp.get(p, {}).get(stat_key)
                if isinstance(val, int):
                    counts[p] += val
                    rounds[p] += 1
                elif val is not None:
                    rounds[p] += 1
        return {p: (counts[p] / rounds[p] if rounds[p] else 0.0) for p in year_players}

    bird = yearly_avgs_for("Birdies")
    pars = yearly_avgs_for("Pars")
    bog  = yearly_avgs_for("Bogies")
    stri = yearly_avgs_for("Strich")

    rows = []
    for p in year_players:
        vals = player_hcps[p]
        avg_hcp = f"{(sum(vals) / len(vals)):.2f}" if vals else "No data"
        rows.append([p, avg_hcp, f"{bird[p]:.2f}", f"{pars[p]:.2f}", f"{bog[p]:.2f}", f"{stri[p]:.2f}"])
    display_table(
        ["Spieler", "Avg Gesp.Hcp", "Birdies/R", "Pars/R", "Bogies/R", "Strich/R"],
        rows,
        "Durchschnittswerte pro Runde (Jahr)",
    )

    # 4) Sonderwertungen Übersicht (Jahr) – LD %, N2TP %, Ladies/R und Gesamt
    import math

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

    ld_points = {p: 0.0 for p in year_players}
    n2tp_points = {p: 0.0 for p in year_players}
    ladies_sums = {p: 0.0 for p in year_players}
    ladies_rounds_played = {p: 0 for p in year_players}

    for _, obj in rounds_for_year:
        sp = obj.get("Spieler", {})
        for p in year_players:
            pdata = sp.get(p, {})
            ld_points[p] += to_points(pdata.get("LD"))
            n2tp_points[p] += to_points(pdata.get("N2TP"))
            played = _has_played_round(pdata)
            if played:
                ladies_rounds_played[p] += 1
                v = pdata.get("Ladies")
                if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)):
                    ladies_sums[p] += float(v)

    total_ld_points = sum(ld_points.values()) or 1.0
    total_n2tp_points = sum(n2tp_points.values()) or 1.0

    rows = []
    for p in year_players:
        ld_pct = 100.0 * ld_points[p] / total_ld_points
        n2tp_pct = 100.0 * n2tp_points[p] / total_n2tp_points
        ladies_pr = (ladies_sums[p] / ladies_rounds_played[p]) if ladies_rounds_played[p] else 0.0
        rows.append([p, f"{ld_pct:.1f}%", f"{n2tp_pct:.1f}%", f"{ladies_pr:.2f}", f"{int(ladies_sums[p])}"])

    display_table(["Spieler", "LD %", "N2TP %", "Ladies/R", "L Ges."], rows, "Sonderwertungen Übersicht (Jahr)")

    # 5) Monetenkuchen (Jahr): Geld-Verteilung im Jahr
    geld_sums = {p: 0.0 for p in year_players}
    for _, obj in rounds_for_year:
        sp = obj.get("Spieler", {})
        for p in year_players:
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
        for p in year_players:
            val = geld_sums[p]
            if val > 0:
                labels.append(p)
                sizes.append(val)
                colors.append(color_map.get(p))
        if not any(colors):
            colors = None
        fig, ax = plt.subplots(figsize=(6, 6))
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
            textprops=dict(fontsize=18)  # doubled font size for labels and autopct
        )
        # total in center
        ax.text(0, 0, f"Gesamt\n€{int(round(total_geld))}", ha='center', va='center', fontsize=30, fontweight='bold')
        ax.axis('equal')
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # 6) Ranglisten und Scorecards (nur Runden des gewählten Jahres)
    text15("Ranglisten und Scorecards (Jahr)")
    rounds_rev = sorted(rounds_for_year, key=lambda kv: datetime.strptime(kv[0], "%d.%m.%Y"), reverse=True)

    # Pro Runde direkt Ranking und Scorecard hintereinander anzeigen
    for d, obj in rounds_rev:
        ort = obj.get("Ort", "")
        display_name = f"{d} ({ort})" if ort else d
        st.markdown(f"<b style='font-size:15px'>{display_name}</b>", unsafe_allow_html=True)
        players = obj.get("Spieler", {}) or {}
        if players:
            st.markdown(_render_ranking_html(players), unsafe_allow_html=True)
            st.markdown(_render_specials_line(players), unsafe_allow_html=True)
        else:
            st.caption("(Keine Ranking-Daten vorhanden)")

        # Scorecard derselben Runde direkt darunter
        st.markdown(_render_scorecard_html(obj), unsafe_allow_html=True)

if __name__ == "__main__":
    import streamlit as st
    render(st)
