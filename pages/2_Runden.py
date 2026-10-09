import json
from datetime import datetime
from html import escape

import streamlit as st


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

    def _shots_received_on_hole(player_hcp, stroke_index):
        if player_hcp is None or stroke_index is None or player_hcp <= 0:
            return 0
        base = player_hcp // 18
        extra = 1 if stroke_index <= (player_hcp % 18) else 0
        return base + extra

    def _zero_point_stroke(par, player_hcp, stroke_index):
        if par is None:
            return None
        shots = _shots_received_on_hole(player_hcp, stroke_index)
        return par + shots + 2

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
        player_hcp = _safe_int(day_hcp)
        if player_hcp is None:
            player_hcp = _safe_int(pdata.get("Gesp.Hcp"))
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
            si = _safe_int(hcps[hole_idx])
            bg = _score_bg(sc, par)
            txt = "x" if scores[hole_idx] in (None, 0) else _fmt_cell(scores[hole_idx])
            html.append(f"<td style='background:{bg};color:#111;font-weight:700'>{escape(txt)}</td>")
            if sc is not None and sc > 0:
                add_score = sc
            else:
                add_score = _zero_point_stroke(par, player_hcp, si)
            if add_score is not None:
                front_sum += add_score
                front_has = True
        html.append(f"<td class='sum-col' style='font-weight:700'>{escape(_fmt_cell(front_sum if front_has else None))}</td>")
        for hole_idx in range(9, 18):
            sc = _safe_int(scores[hole_idx])
            par = _safe_int(pars[hole_idx])
            si = _safe_int(hcps[hole_idx])
            bg = _score_bg(sc, par)
            txt = "x" if scores[hole_idx] in (None, 0) else _fmt_cell(scores[hole_idx])
            html.append(f"<td style='background:{bg};color:#111;font-weight:700'>{escape(txt)}</td>")
            if sc is not None and sc > 0:
                add_score = sc
            else:
                add_score = _zero_point_stroke(par, player_hcp, si)
            if add_score is not None:
                back_sum += add_score
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


def render(st_obj):
    st_obj.markdown(
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
        .rt-table, .sc-table {
            border-collapse: collapse;
            width: auto;
            margin: 0.3rem 0 1rem 0;
        }
        .rt-table {
            table-layout: fixed;
        }
        .sc-table {
            table-layout: auto;
        }
        .rt-table th, .rt-table td, .sc-table th, .sc-table td {
            border: 1px solid #d5d5d5;
            padding: 0.12rem 0.16rem;
            text-align: center;
            line-height: 1.1;
            color: #111;
            background: #fff;
        }
        .rt-table th,
        .rt-table td {
            font-size: 17px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
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
        .sc-table th,
        .sc-table td {
            font-size: 17px;
        }
        .rt-table th, .sc-table th {
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
            .rt-table th, .rt-table td, .sc-table th, .sc-table td {
                color: #111 !important;
            }
            .rt-table {
                width: 100% !important;
                table-layout: fixed !important;
                margin-left: 0 !important;
                margin-right: 0 !important;
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
            .rt-table th, .rt-table td, .sc-table th, .sc-table td {
                font-size: 13px !important;
            }
            .sc-table th,
            .sc-table td {
                padding: 0.08rem 0.10rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    json_path = "json/allrounds.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            allrounds = json.load(f)
    except FileNotFoundError:
        st_obj.error("allrounds.json nicht gefunden.")
        return
    except Exception as e:
        st_obj.error(f"Fehler beim Lesen von allrounds.json: {e}")
        return

    if not isinstance(allrounds, dict) or len(allrounds) == 0:
        st_obj.info("Keine Runden in allrounds.json gefunden.")
        return

    def _date_sort_key(d):
        try:
            return datetime.strptime(d, "%d.%m.%Y")
        except Exception:
            return datetime.min

    round_dates = sorted(allrounds.keys(), key=_date_sort_key, reverse=True)

    for date_key in round_dates:
        rd = allrounds.get(date_key, {}) or {}
        ort = rd.get("Ort", "")
        title = f"{date_key} ({ort})" if ort else date_key
        st_obj.markdown(f"<b style='font-size:15px'>{escape(title)}</b>", unsafe_allow_html=True)

        players = rd.get("Spieler", {}) or {}
        if players:
            st_obj.markdown(_render_ranking_html(players), unsafe_allow_html=True)
            st_obj.markdown(_render_specials_line(players), unsafe_allow_html=True)

            st_obj.markdown(_render_scorecard_html(rd), unsafe_allow_html=True)
        else:
            st_obj.caption("Keine Spieler-Daten vorhanden.")


if __name__ == "__main__":
    render(st)
