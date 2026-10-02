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
    cols = ["P", "Name", "Net", "G.Hcp", "Bird", "Par", "Bog.", "Str.", "Geld", "L", "LD", "N2"]

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
            "ld": pdata.get("LD"),
            "n2tp": pdata.get("N2TP"),
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
        html.append(f"<td>{escape(_fmt_cell(r['ld']))}</td>")
        html.append(f"<td>{escape(_fmt_cell(r['n2tp']))}</td>")
        html.append("</tr>")
    html.append("</tbody></table>")
    return "".join(html)


def _render_scorecard_html(round_data):
    holes = list(range(1, 19))
    pars = list(round_data.get("Par", []) or [])
    hcps = list(round_data.get("Hcp", []) or [])
    players = round_data.get("Spieler", {}) or {}

    while len(pars) < 18:
        pars.append(None)
    while len(hcps) < 18:
        hcps.append(None)

    html = []
    html.append("<table class='sc-table'>")
    html.append("<thead><tr><th></th>")
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
            html.append(f"<td>{escape(_fmt_cell(v))}</td>")
        if label in ("Hole", "Hcp"):
            out_sum = None
        else:
            out_sum = _sum_slice(values, 0, 9)
        html.append(f"<td class='sum-col'>{escape(_fmt_cell(out_sum))}</td>")
        for v in values[9:18]:
            html.append(f"<td>{escape(_fmt_cell(v))}</td>")
        if label in ("Hole", "Hcp"):
            in_sum = None
            tot_sum = None
        else:
            in_sum = _sum_slice(values, 9, 18)
            tot_sum = _sum_slice(values, 0, 18)
        html.append(f"<td class='sum-col'>{escape(_fmt_cell(in_sum))}</td>")
        html.append(f"<td class='sum-col'>{escape(_fmt_cell(tot_sum))}</td></tr>")

    _fixed_row("Hole", holes)
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
        total_sum = (front_sum if front_has else 0) + (back_sum if back_has else 0)
        total_has = front_has or back_has
        html.append(f"<td class='sum-col' style='font-weight:700'>{escape(_fmt_cell(back_sum if back_has else None))}</td>")
        html.append(f"<td class='sum-col' style='font-weight:700'>{escape(_fmt_cell(total_sum if total_has else None))}</td></tr>")

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
        html, body, p, ol, ul, dl, span, div,
        [data-testid='stMarkdownContainer'] p,
        [data-testid='stMarkdownContainer'] span,
        h1, h2, h3, h4, h5, h6,
        [data-testid='stHeader'] h1 {
            font-size: 17px !important;
        }
        .rt-table, .sc-table {
            border-collapse: collapse;
            width: 100%;
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
            font-size: 13px;
            line-height: 1.1;
            color: #111;
            background: #fff;
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
            .sc-table {
                table-layout: fixed !important;
                width: 100% !important;
                margin-left: 0 !important;
                margin-right: 0 !important;
            }
            .sc-table th,
            .sc-table td {
                padding: 0.06rem 0.08rem !important;
                font-size: 9px !important;
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
                font-size: 10px !important;
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

    st_obj.markdown("<span style='font-size:15px'><b>Runden (Test, HTML)</b></span>", unsafe_allow_html=True)

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

            st_obj.markdown(_render_scorecard_html(rd), unsafe_allow_html=True)
        else:
            st_obj.caption("Keine Spieler-Daten vorhanden.")


if __name__ == "__main__":
    render(st)
