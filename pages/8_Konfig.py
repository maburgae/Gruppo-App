import json
import os
import base64
import requests
import subprocess  # für Bulk Git Commit
from datetime import date, datetime
from html import escape

from actions.neue_runde import main as neue_runde_main
from actions.upload_scorecard import main as upload_scorecard_main
from actions.berechne_den_tag import main as berechne_den_tag_main
from actions.tag_to_alle_runden import main as tag_to_alle_runden_main
import os

DEFAULT_PLAYERS_STR = '["Marc","Andy","Bernie","Jens","Markus","Buffy"]'
ROUND_PLAYERS = ["Marc", "Andy", "Bernie", "Jens", "Markus", "Buffy"]
UPLOAD_MODEL_OPTIONS = [
    "gpt-5-mini",
    "gpt-5.6-sol",
    "gpt-5",
    "gpt-5.6-terra",
    "gpt-5.6-luna",
    "gpt-5-nano",
]
NO_SHOW_JSON_PATH = "json/no_show_players.json"


def _load_no_show_players() -> list[str]:
    try:
        with open(NO_SHOW_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            players = data.get("players", [])
        elif isinstance(data, list):
            players = data
        else:
            players = []
        out = []
        for p in players:
            if isinstance(p, str):
                pn = p.strip()
                if pn and pn not in out:
                    out.append(pn)
        return out
    except Exception:
        return []


def _save_no_show_players(players: list[str]) -> None:
    cleaned = []
    for p in players:
        if isinstance(p, str):
            pn = p.strip()
            if pn and pn not in cleaned:
                cleaned.append(pn)
    os.makedirs("json", exist_ok=True)
    with open(NO_SHOW_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump({"players": cleaned}, f, ensure_ascii=False, indent=2)


def _clear_no_show_players() -> None:
    _save_no_show_players([])

def _init_state():
    import streamlit as st
    if "konf_platzname" not in st.session_state:
        st.session_state.konf_platzname = ""
    if "konf_players" not in st.session_state:
        st.session_state.konf_players = json.dumps(ROUND_PLAYERS, ensure_ascii=False)
    if "konf_file_id" not in st.session_state:
        st.session_state.konf_file_id = ""
    if "konf_output" not in st.session_state:
        st.session_state.konf_output = ""
    # Track uploads to avoid re-processing on every rerun
    if "konf_uploaded_name" not in st.session_state:
        st.session_state.konf_uploaded_name = ""
    if "konf_preprocess" not in st.session_state:
        st.session_state.konf_preprocess = False
    if "konf_upload_model" not in st.session_state:
        st.session_state.konf_upload_model = UPLOAD_MODEL_OPTIONS[0]
    if "konf_round_date" not in st.session_state:
        st.session_state.konf_round_date = date.today()
    for _player in ROUND_PLAYERS:
        check_key = f"konf_player_{_player}"
        if check_key not in st.session_state:
            st.session_state[check_key] = True
        flight_key = f"flight_{_player}"
        if flight_key not in st.session_state:
            st.session_state[flight_key] = "1"
        elif st.session_state[flight_key] not in ("1", "2"):
            st.session_state[flight_key] = "1"


def render(st):
    # Global CSS for 15px font across common text elements and labels/buttons
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
        [data-testid='stAppViewContainer'] [data-testid='stMain'] [data-testid='stHeader'] h1,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] label,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] .stButton > button,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] .stDownloadButton > button,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] .stTextInput label,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] .stSelectbox label,
        [data-testid='stAppViewContainer'] [data-testid='stMain'] .stFileUploader label {
            font-size: 15px !important;
        }
        .compact-player-grid div[data-testid='stCheckbox'] {
            margin-bottom: 0.1rem !important;
        }
        .compact-player-grid div[data-testid='stCheckbox'] label {
            white-space: nowrap !important;
            padding-right: 0 !important;
        }
        .compact-player-grid div[data-testid='stSelectbox'] {
            margin-top: -0.2rem !important;
            max-width: 39px !important;
            min-width: 39px !important;
        }
        .compact-player-grid div[data-testid='stSelectbox'] [data-baseweb='select'] {
            width: 39px !important;
            min-width: 39px !important;
            max-width: 39px !important;
        }
        .compact-player-grid div[data-testid='stSelectbox'] [data-baseweb='select'] > div {
            min-height: 30px !important;
            padding-left: 6px !important;
            padding-right: 18px !important;
        }
        .score-row-label {
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.2 !important;
            white-space: nowrap !important;
            font-weight: 700 !important;
        }
        .score-row-label p {
            margin: 0 !important;
            padding: 0 !important;
        }
        @media (max-width: 900px) {
            div[data-testid='stHorizontalBlock'] {
                flex-wrap: wrap !important;
                gap: 0.25rem !important;
            }
            .compact-player-grid div[data-testid='column'] {
                flex: 0 0 calc(33.33% - 0.25rem) !important;
                width: calc(33.33% - 0.25rem) !important;
                min-width: calc(33.33% - 0.25rem) !important;
                max-width: calc(33.33% - 0.25rem) !important;
            }
            .compact-player-grid div[data-testid='stCheckbox'] {
                min-width: 100% !important;
                max-width: 100% !important;
            }
            .compact-player-grid div[data-testid='stSelectbox'] {
                max-width: 44px !important;
                min-width: 44px !important;
            }
            .compact-player-grid div[data-testid='stSelectbox'] [data-baseweb='select'] {
                width: 44px !important;
                min-width: 44px !important;
                max-width: 44px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    def text15(s: str):
        st.markdown(f"<span style='font-size:15px'>{s}</span>", unsafe_allow_html=True)

    st.markdown(
        """
        <style>
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

    _init_state()

    flash_msg = st.session_state.pop("konf_flash_msg", None)
    if flash_msg:
        st.success(flash_msg)

    # Simple password protection for this page
    if "konf_authed" not in st.session_state:
        st.session_state.konf_authed = False
    if not st.session_state.konf_authed:
        with st.form("konf_auth_form"):
            pwd = st.text_input("Passwort", type="password")
            ok = st.form_submit_button("Login")
        if ok:
            if pwd == "9":
                st.session_state.konf_authed = True
                st.success("Eingeloggt.")
            else:
                st.error("Falsches Passwort.")
                st.stop()
        else:
            st.stop()

    def _mark_meta_dirty():
        st.session_state["konf_meta_user_dirty"] = True

    # Aktuelle Runde laden (Quelle fuer alle Vorbelegungen)
    with open("json/golf_df/golf_df.json", "r", encoding="utf-8") as f:
        golf_data = json.load(f)
    key = list(golf_data.keys())[0]
    data = golf_data[key]

    def _is_active_player_entry(pdata):
        if not isinstance(pdata, dict):
            return False
        score_vals = pdata.get("Score")
        if isinstance(score_vals, list) and any(isinstance(v, (int, float)) for v in score_vals):
            return True
        relevant_fields = (
            "Flight", "DayHcp", "Netto", "Gesp.Hcp", "Birdies", "Pars", "Bogies", "Strich", "Platz", "LD", "N2TP", "Ladies"
        )
        for fld in relevant_fields:
            val = pdata.get(fld)
            if val not in (None, ""):
                return True
        return False

    # Dynamische Spielerliste: bekannte Spieler + angelegte Spieler aus golf_df
    default_players = []
    try:
        default_players = json.loads(DEFAULT_PLAYERS_STR)
    except Exception:
        default_players = []
    players_obj_for_ui = data.get("Spieler", {}) or {}
    ui_players = []
    for pname in (ROUND_PLAYERS + default_players + list(players_obj_for_ui.keys())):
        if isinstance(pname, str):
            pn = pname.strip()
            if pn and pn not in ui_players:
                ui_players.append(pn)

    # Beim Laden der Seite alle Eingabefelder aus golf_df vorbelegen
    def _file_meta_signature():
        sig = [
            (data.get("Ort", "") or "").strip() if isinstance(data.get("Ort", ""), str) else "",
        ]
        for pname in ui_players:
            pdata = players_obj_for_ui.get(pname, {}) or {}
            checked = _is_active_player_entry(pdata)
            flight_val = str(pdata.get("Flight", "")).strip()
            flight_val = flight_val if flight_val in ("1", "2") else "1"
            sig.append((pname, checked, flight_val))
        return tuple(sig)

    def _state_meta_signature():
        sig = [
            (st.session_state.get("konf_platzname", "") or "").strip() if isinstance(st.session_state.get("konf_platzname", ""), str) else "",
        ]
        for pname in ui_players:
            checked = bool(st.session_state.get(f"konf_player_{pname}", False))
            flight_val = st.session_state.get(f"flight_{pname}", "1")
            if isinstance(flight_val, str):
                flight_val = flight_val.strip()
            flight_val = flight_val if flight_val in ("1", "2") else "1"
            sig.append((pname, checked, flight_val))
        return tuple(sig)

    should_prefill = st.session_state.get("konf_loaded_round_key") != key
    if not should_prefill and not st.session_state.get("konf_meta_user_dirty", False):
        should_prefill = _state_meta_signature() != _file_meta_signature()

    if should_prefill:
        ort_from_file = data.get("Ort", "")
        st.session_state.konf_platzname = ort_from_file if isinstance(ort_from_file, str) else ""

        try:
            st.session_state.konf_round_date = datetime.strptime(key, "%d.%m.%Y").date()
        except Exception:
            pass

        for pname in ui_players:
            check_key = f"konf_player_{pname}"
            flight_key = f"flight_{pname}"
            pdata = players_obj_for_ui.get(pname, {}) or {}
            st.session_state[check_key] = _is_active_player_entry(pdata)
            flight_val = str(pdata.get("Flight", "")).strip()
            st.session_state[flight_key] = flight_val if flight_val in ("1", "2") else "1"

        st.session_state.konf_loaded_round_key = key
        st.session_state["konf_meta_user_dirty"] = False

    text15("Konfiguration")

    # Eingabefeld Platzname (ohne Defaultwert)
    platzname = st.text_input("Platzname", key="konf_platzname", on_change=_mark_meta_dirty)

    # Datum für die neue Runde (default: heute, aber änderbar)
    round_date = st.date_input("Datum", key="konf_round_date")

    # Feste Spielerauswahl mit Flight-Dropdown je Spieler
    st.markdown("**Spieler**")
    flight_values = {}
    selected_players = []
    st.markdown("<div class='compact-player-grid'>", unsafe_allow_html=True)
    player_cols = st.columns(len(ui_players), gap="small") if ui_players else []
    for col, pname in zip(player_cols, ui_players):
        check_key = f"konf_player_{pname}"
        flight_key = f"flight_{pname}"
        if check_key not in st.session_state:
            st.session_state[check_key] = False
        if flight_key not in st.session_state or st.session_state[flight_key] not in ("1", "2"):
            st.session_state[flight_key] = "1"
        checked = col.checkbox(pname, key=f"konf_player_{pname}", on_change=_mark_meta_dirty)
        col.selectbox("Flight", options=["1", "2"], key=f"flight_{pname}", label_visibility="collapsed", on_change=_mark_meta_dirty)
        if checked:
            selected_players.append(pname)
            flight_values[pname] = st.session_state.get(f"flight_{pname}", "1")
    st.markdown("</div>", unsafe_allow_html=True)

    # Kompatibel halten: JSON-String aus den gecheckten Spielern bauen
    st.session_state.konf_players = json.dumps(selected_players, ensure_ascii=False)
    st.caption(f"Spieler JSON: {st.session_state.konf_players}")

    # Knopf "Neue Runde"
    if st.button("Neue Runde"):
        if len(selected_players) == 0:
            st.session_state.konf_output = "Fehler: Bitte mindestens einen Spieler auswählen."
        else:
            date_key = round_date.strftime("%d.%m.%Y")
            result = neue_runde_main(selected_players, flights=flight_values, ort=platzname.strip(), round_date=date_key)
            _clear_no_show_players()
            st.session_state.konf_output = result
            st.success("No-show Liste für die neue Runde geleert.")

    # Option: Preprocess vor Upload
    st.checkbox("Bild vor Upload vorverarbeiten (empfohlen)", key="konf_preprocess", value=st.session_state.get("konf_preprocess", True))
    st.selectbox(
        "AI Modell (Scorecard Upload)",
        options=UPLOAD_MODEL_OPTIONS,
        key="konf_upload_model",
        index=UPLOAD_MODEL_OPTIONS.index(st.session_state.get("konf_upload_model", UPLOAD_MODEL_OPTIONS[0]))
        if st.session_state.get("konf_upload_model", UPLOAD_MODEL_OPTIONS[0]) in UPLOAD_MODEL_OPTIONS else 0,
    )

    # Knopf "Upload Scorecard" mit Dateiupload
    uploaded_file = st.file_uploader("Scorecard Datei auswählen", type=["jpg", "jpeg", "png"], key="konf_uploader")
    if uploaded_file is not None:
        st.image(uploaded_file, caption=f"Upload Vorschau: {uploaded_file.name}", width='stretch')
        # Expliziter Start: erlaubt erneute Verarbeitung auch mit identischem Dateinamen
        if st.button("Scorecard an AI senden", key="konf_upload_process_btn"):
            file_path = f"{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            # Pass user choice for preprocessing
            result = upload_scorecard_main(
                file_path,
                pre_process=st.session_state.get("konf_preprocess", True),
                model_name=st.session_state.get("konf_upload_model", UPLOAD_MODEL_OPTIONS[0]),
            )
            st.session_state.konf_output = result
            st.session_state.konf_file_id = result  # Store returned file_id
            st.session_state.konf_uploaded_name = uploaded_file.name
            st.success(f"Upload verarbeitet mit Modell: {st.session_state.get('konf_upload_model', UPLOAD_MODEL_OPTIONS[0])}")

    # Zwei Tabellen-Editoren (1-9 und 10-18) für Par, Hcp und Scores aller Spieler
    text15("Scorecard Eingabe (Tabelle)")

    def _norm_list(vals, fill=None):
        out = list(vals or [])
        while len(out) < 18:
            out.append(fill)
        return out[:18]

    def _coerce_int(value):
        if value is None:
            return None
        try:
            return int(value)
        except Exception:
            return None

    def _has_numeric_score(pdata):
        if not isinstance(pdata, dict):
            return False
        scores = pdata.get("Score")
        if not isinstance(scores, list):
            return False
        return any(isinstance(v, (int, float)) for v in scores)

    def _to_int_money(val):
        if isinstance(val, (int, float)):
            return int(val)
        if val in (None, ""):
            return 0
        try:
            return int(float(str(val).replace(",", ".")))
        except Exception:
            return 0

    no_show_players = _load_no_show_players()
    no_show_set = set(no_show_players)

    current_par = _norm_list(data.get("Par", []))
    current_hcp = _norm_list(data.get("Hcp", []))
    all_players_map = data.get("Spieler", {}) or {}

    # Sofort-Sync: Platzname + Spieler/Fights direkt nach UI-Aenderungen speichern
    instant_meta_changed = False

    ort_input_now = st.session_state.get("konf_platzname", "")
    if isinstance(ort_input_now, str):
        ort_input_now = ort_input_now.strip()
    else:
        ort_input_now = ""
    current_ort = data.get("Ort")
    current_ort = current_ort.strip() if isinstance(current_ort, str) else ""
    if ort_input_now != current_ort:
        data["Ort"] = ort_input_now
        instant_meta_changed = True

    for player in ui_players:
        checked = player in selected_players
        flight_state_key = f"flight_{player}"
        flight_val = st.session_state.get(flight_state_key, "1")
        if isinstance(flight_val, str):
            flight_val = flight_val.strip()
        if flight_val not in ("1", "2"):
            flight_val = "1"

        pdata = all_players_map.get(player)
        if checked:
            if not isinstance(pdata, dict):
                all_players_map[player] = {
                    "Flight": flight_val,
                    "Score": [None] * 18,
                }
                instant_meta_changed = True
            else:
                if pdata.get("Flight") != flight_val:
                    pdata["Flight"] = flight_val
                    instant_meta_changed = True
        else:
            # Nur inaktiven, leeren Eintrag entfernen (gespielte / no-show Daten bleiben erhalten)
            if isinstance(pdata, dict) and player not in no_show_set:
                has_score = _has_numeric_score(pdata)
                has_other_values = any(
                    pdata.get(k) not in (None, "", 0)
                    for k in ("DayHcp", "Netto", "Gesp.Hcp", "Birdies", "Pars", "Bogies", "Strich", "Platz", "Ladies", "LD", "N2TP")
                )
                money_val = _to_int_money(pdata.get("Geld"))
                if (not has_score) and (not has_other_values) and money_val == 0:
                    all_players_map.pop(player, None)
                    instant_meta_changed = True

    # No-show Spieler (ohne numerischen Score) nicht als reguläre Spieler behandeln
    players_present = [
        player
        for player, pdata in all_players_map.items()
        if not (player in no_show_set and not _has_numeric_score(pdata))
    ]

    # Sicherheitsnetz: no-show Einträge in golf_df als reiner Geld-Eintrag halten
    no_show_cleanup_changed = False
    for player in no_show_players:
        pdata = all_players_map.get(player)
        if not isinstance(pdata, dict) or _has_numeric_score(pdata):
            continue
        money_val = _to_int_money(pdata.get("Geld"))
        if list(pdata.keys()) != ["Geld"] or pdata.get("Geld") != money_val:
            all_players_map[player] = {"Geld": money_val}
            no_show_cleanup_changed = True

    if no_show_cleanup_changed:
        with open("json/golf_df/golf_df.json", "w", encoding="utf-8") as f:
            json.dump(golf_data, f, ensure_ascii=False, indent=2)

    if instant_meta_changed:
        with open("json/golf_df/golf_df.json", "w", encoding="utf-8") as f:
            json.dump(golf_data, f, ensure_ascii=False, indent=2)
        st.session_state["konf_meta_user_dirty"] = False
        st.session_state["konf_flash_msg"] = "Konfig sofort gespeichert."
        st.rerun()

    current_scores = {
        player: _norm_list(data["Spieler"].get(player, {}).get("Score", []))
        for player in players_present
    }

    front_hole_columns = [str(i) for i in range(1, 10)]
    back_hole_columns = [str(i) for i in range(10, 19)]

    def _build_table_rows(hole_columns):
        rows = []
        par_row = {"Typ": "PAR"}
        hcp_row = {"Typ": "HCP"}
        for col in hole_columns:
            idx = int(col) - 1
            par_row[col] = _coerce_int(current_par[idx])
            hcp_row[col] = _coerce_int(current_hcp[idx])
        rows.append(par_row)
        rows.append(hcp_row)

        for player in players_present:
            row = {"Typ": player}
            vals = current_scores.get(player, [None] * 18)
            for col in hole_columns:
                idx = int(col) - 1
                row[col] = _coerce_int(vals[idx])
            rows.append(row)
        return rows

    front_table_rows = _build_table_rows(front_hole_columns)
    back_table_rows = _build_table_rows(back_hole_columns)

    st.caption("Loecher 1-9")
    edited_front = st.data_editor(
        front_table_rows,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key="konf_score_editor_table_front",
        column_config={
            "Typ": st.column_config.TextColumn("Typ", disabled=True),
            **{col: st.column_config.NumberColumn(col, min_value=0, max_value=18, step=1) for col in front_hole_columns},
        },
    )

    st.caption("Loecher 10-18")
    edited_back = st.data_editor(
        back_table_rows,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key="konf_score_editor_table_back",
        column_config={
            "Typ": st.column_config.TextColumn("Typ", disabled=True),
            **{col: st.column_config.NumberColumn(col, min_value=0, max_value=18, step=1) for col in back_hole_columns},
        },
    )

    if hasattr(edited_front, "to_dict"):
        edited_rows_front = edited_front.to_dict(orient="records")
    elif isinstance(edited_front, list):
        edited_rows_front = edited_front
    else:
        edited_rows_front = front_table_rows

    if hasattr(edited_back, "to_dict"):
        edited_rows_back = edited_back.to_dict(orient="records")
    elif isinstance(edited_back, list):
        edited_rows_back = edited_back
    else:
        edited_rows_back = back_table_rows

    row_map_front = {str(r.get("Typ", "")): r for r in edited_rows_front if isinstance(r, dict)}
    row_map_back = {str(r.get("Typ", "")): r for r in edited_rows_back if isinstance(r, dict)}

    row_map = {}
    for typ in ["PAR", "HCP"] + players_present:
        merged_row = {"Typ": typ}
        merged_row.update(row_map_front.get(typ, {}))
        merged_row.update(row_map_back.get(typ, {}))
        row_map[typ] = merged_row

    new_par = list(current_par)
    new_hcp = list(current_hcp)
    new_scores = {player: list(vals) for player, vals in current_scores.items()}

    par_row_new = row_map.get("PAR", {})
    hcp_row_new = row_map.get("HCP", {})
    for i in range(18):
        col = str(i + 1)
        p = _coerce_int(par_row_new.get(col))
        h = _coerce_int(hcp_row_new.get(col))
        if p is not None:
            new_par[i] = p
        if h is not None:
            new_hcp[i] = h

    for player in players_present:
        row = row_map.get(player, {})
        for i in range(18):
            col = str(i + 1)
            v = _coerce_int(row.get(col))
            new_scores[player][i] = None if v in (None, 0) else v

    # Auto-save: direkt speichern, sobald ein Dropdown-Wert geändert wurde
    needs_save = (new_par != current_par) or (new_hcp != current_hcp)
    if not needs_save:
        for player in players_present:
            if new_scores.get(player, []) != current_scores.get(player, []):
                needs_save = True
                break

    if needs_save:
        data["Par"] = new_par
        data["Hcp"] = new_hcp
        for player in data.get("Spieler", {}):
            if player in no_show_set and not _has_numeric_score(data["Spieler"].get(player, {})):
                # no-show Einträge bleiben strikt bei Geld-only
                pdata = data["Spieler"].get(player, {}) or {}
                data["Spieler"][player] = {"Geld": _to_int_money(pdata.get("Geld"))}
                continue
            if player in new_scores:
                data["Spieler"][player]["Score"] = new_scores[player]
            # Flight Werte aus den Eingabefeldern übernehmen
            flight_state_key = f"flight_{player}"
            flight_val = st.session_state.get(flight_state_key, "")
            if isinstance(flight_val, str):
                flight_val = flight_val.strip()
            data["Spieler"][player]["Flight"] = flight_val if flight_val else None

        # Ort aktualisieren falls Eingabe vorhanden
        _platz_eingabe = st.session_state.get("konf_platzname", "").strip()
        if _platz_eingabe:
            data["Ort"] = _platz_eingabe

        with open("json/golf_df/golf_df.json", "w", encoding="utf-8") as f:
            json.dump(golf_data, f, ensure_ascii=False, indent=2)
        st.session_state["konf_flash_msg"] = "Änderung gespeichert."
        st.rerun()

    # Extras pro Spieler: nur gespielte Spieler
    st.caption("Ladies")

    def _is_marked(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            v = value.strip().lower()
            return v in ("1", "true", "yes", "x")
        return False

    played_players = [
        player
        for player in players_present
        if any(isinstance(v, (int, float)) for v in current_scores.get(player, []))
    ]

    extras_rows = []
    current_ladies_map = {}
    for player in played_players:
        pdat = data.get("Spieler", {}).get(player, {}) or {}
        l_raw = pdat.get("Ladies")
        l_val = _coerce_int(l_raw)
        if l_val is None:
            l_val = 0
        current_ladies_map[player] = l_val
        extras_rows.append({"Spieler": player, "Ladies": l_val})

    selected_ld = "-"
    selected_n2tp = "-"
    current_ld_choice = "-"
    current_n2tp_choice = "-"
    new_ladies_map = dict(current_ladies_map)

    if played_players:
        edited_extras = st.data_editor(
            extras_rows,
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            key="konf_extras_ladies_table",
            column_config={
                "Spieler": st.column_config.TextColumn("Spieler", disabled=True),
                "Ladies": st.column_config.NumberColumn("Ladies", min_value=0, step=1),
            },
        )

        if hasattr(edited_extras, "to_dict"):
            edited_extras_rows = edited_extras.to_dict(orient="records")
        elif isinstance(edited_extras, list):
            edited_extras_rows = edited_extras
        else:
            edited_extras_rows = extras_rows

        for row in edited_extras_rows:
            if not isinstance(row, dict):
                continue
            pname = str(row.get("Spieler", "")).strip()
            if pname not in new_ladies_map:
                continue
            lv = _coerce_int(row.get("Ladies"))
            new_ladies_map[pname] = 0 if lv is None else lv

        for player in played_players:
            pdat = data.get("Spieler", {}).get(player, {}) or {}
            if _is_marked(pdat.get("LD")):
                current_ld_choice = player
            if _is_marked(pdat.get("N2TP")):
                current_n2tp_choice = player

        extra_cols = st.columns(2)
        with extra_cols[0]:
            selected_ld = st.selectbox(
                "LD",
                options=["-"] + played_players,
                index=(["-"] + played_players).index(current_ld_choice) if current_ld_choice in (["-"] + played_players) else 0,
                key="konf_ld_player",
            )
        with extra_cols[1]:
            selected_n2tp = st.selectbox(
                "N2TP",
                options=["-"] + played_players,
                index=(["-"] + played_players).index(current_n2tp_choice) if current_n2tp_choice in (["-"] + played_players) else 0,
                key="konf_n2tp_player",
            )
    else:
        st.caption("Keine gespielten Spieler vorhanden.")

    extras_changed = new_ladies_map != current_ladies_map
    if not extras_changed:
        extras_changed = (selected_ld != current_ld_choice) or (selected_n2tp != current_n2tp_choice)

    if extras_changed:
        for player in played_players:
            pdat = data.get("Spieler", {}).get(player)
            if not isinstance(pdat, dict):
                data["Spieler"][player] = {}
                pdat = data["Spieler"][player]
            pdat["Ladies"] = int(new_ladies_map.get(player, 0))
            pdat["LD"] = 1 if selected_ld == player else 0
            pdat["N2TP"] = 1 if selected_n2tp == player else 0

        with open("json/golf_df/golf_df.json", "w", encoding="utf-8") as f:
            json.dump(golf_data, f, ensure_ascii=False, indent=2)
        st.session_state["konf_flash_msg"] = "Ladies/LD/N2TP gespeichert."
        st.rerun()

    # No-show Geld hinzufügen (z.B. Spieler hat nicht gespielt, zahlt aber mit)
    no_show_options = sorted(set(ui_players + players_present + no_show_players))
    ns_cols = st.columns([1.2, 2.0])
    with ns_cols[1]:
        no_show_name = st.selectbox("No-show Spieler", options=no_show_options, key="konf_noshow_name")
    with ns_cols[0]:
        add_no_show = st.button("No-show hinzufügen")

    if add_no_show:
        try:
            no_show_players = _load_no_show_players()
            if no_show_name not in no_show_players:
                no_show_players.append(no_show_name)
            _save_no_show_players(no_show_players)
            st.success(f"No-show gespeichert in separater Datei: {no_show_name} (Geld wird bei Berechnung gesetzt)")
        except Exception as e:
            st.error(f"Fehler beim Speichern des No-show Eintrags: {e}")

    current_no_shows = _load_no_show_players()
    if current_no_shows:
        rm_cols = st.columns([1.2, 2.0])
        with rm_cols[1]:
            no_show_remove_name = st.selectbox(
                "No-show entfernen",
                options=current_no_shows,
                key="konf_noshow_remove_name",
            )
        with rm_cols[0]:
            remove_no_show = st.button("No-show entfernen")

        if remove_no_show:
            try:
                remaining_no_shows = [p for p in current_no_shows if p != no_show_remove_name]
                _save_no_show_players(remaining_no_shows)
                st.success(f"No-show entfernt: {no_show_remove_name}")
                st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Entfernen des No-show Eintrags: {e}")

    if current_no_shows:
        st.caption("Aktuelle No-show Liste")
        st.markdown(", ".join(current_no_shows))
    else:
        st.caption("Aktuelle No-show Liste: leer")

    # Separate heavy computation button
    if st.button("Berechne den Tag"):
        try:
            result = berechne_den_tag_main()
            st.session_state.konf_output = f"Berechne: {result}"
            with open("json/golf_df/golf_df.json", "r", encoding="utf-8") as f:
                _tag = json.load(f)
            date_key = next(iter(_tag.keys()))
            round_obj = _tag.get(date_key, {}) or {}
            players_obj = round_obj.get("Spieler", {}) or {}
            st.success("Tag berechnet. Ausgabe als HTML-Tabellen aktualisiert.")
            st.markdown(f"<b style='font-size:15px'>{escape(date_key)}</b>", unsafe_allow_html=True)
            st.markdown(_render_ranking_html(players_obj), unsafe_allow_html=True)
            st.markdown(_render_specials_line(players_obj), unsafe_allow_html=True)
            st.markdown(_render_scorecard_html(round_obj), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Fehler bei der Tagesberechnung: {e}")

    # Download golf_df.json
    try:
        with open("json/golf_df/golf_df.json", "r", encoding="utf-8") as f:
            _golfdf = f.read()
        st.download_button(
            label="Download golf_df.json",
            data=_golfdf,
            file_name="golf_df.json",
            mime="application/json",
            key="download_golf_df_json",
        )
    except Exception:
        pass

    # Download allrounds.json
    try:
        with open("json/allrounds.json", "r", encoding="utf-8") as f:
            _allrounds = f.read()
        st.download_button(
            label="Download allrounds.json",
            data=_allrounds,
            file_name="allrounds.json",
            mime="application/json",
            key="download_allrounds_json",
        )
    except Exception:
        pass

    # Download abrechnung.json (Expenses)
    try:
        with open("json/abrechnung.json", "r", encoding="utf-8") as f:
            _abrechnung = f.read()
        st.download_button(
            label="Download abrechnung.json",
            data=_abrechnung,
            file_name="abrechnung.json",
            mime="application/json",
            key="download_abrechnung_json",
        )
    except Exception:
        pass

    # Neuer Knopf: Schlüssel aus golf_df nach allrounds.json übernehmen
    if st.button("Key aus Tag in allrounds.json übernehmen"):
        try:
            # Quelle lesen (aktueller Tag)
            with open("json/golf_df/golf_df.json", "r", encoding="utf-8") as f:
                tag_data = json.load(f)
            if not isinstance(tag_data, dict) or len(tag_data) == 0:
                raise ValueError("golf_df.json enthält keinen gültigen Schlüssel")
            date_key = next(iter(tag_data.keys()))
            round_obj = tag_data[date_key]

            # Ziel lesen (alle Runden)
            allrounds_path = "json/allrounds.json"
            if os.path.exists(allrounds_path):
                with open(allrounds_path, "r", encoding="utf-8") as f:
                    allrounds = json.load(f)
                if not isinstance(allrounds, dict):
                    allrounds = {}
            else:
                allrounds = {}

            # Backup anlegen, falls vorhanden
            if os.path.exists(allrounds_path):
                import shutil
                from datetime import datetime as _dt
                ts = _dt.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"json/allrounds_backup_{ts}.json"
                shutil.copy2(allrounds_path, backup_path)

            # Einfügen/Überschreiben
            allrounds[date_key] = round_obj
            with open(allrounds_path, "w", encoding="utf-8") as f:
                json.dump(allrounds, f, ensure_ascii=False, indent=2)
            st.success(f"Datum {date_key} in allrounds.json eingefügt/aktualisiert.")
        except Exception as e:
            st.error(f"Fehler: {e}")

    # --- GitHub API Commit für mehrere JSONs (golf_df, allrounds, abrechnung) ---
    st.markdown("---")
    if st.button("JSON Dateien (golf_df, allrounds, abrechnung) zu GitHub committen (API)"):
        log = []
        files = [
            ("json/golf_df/golf_df.json", "golf_df.json"),
            ("json/allrounds.json", "allrounds.json"),
            ("json/abrechnung.json", "abrechnung.json"),
        ]
        token = getattr(st, 'secrets', {}).get("GITHUB_TOKEN") if hasattr(st, 'secrets') else None
        repo = (getattr(st, 'secrets', {}).get("REPO") if hasattr(st, 'secrets') else None) or "USER/REPO"
        branch = (getattr(st, 'secrets', {}).get("BRANCH") if hasattr(st, 'secrets') else None) or "main"
        try:
            secret_keys = list(getattr(st, 'secrets', {}).keys()) if hasattr(st, 'secrets') else []
            log.append(f"Secrets Keys: {secret_keys}")
        except Exception:
            pass
        log.append(f"Repo={repo} Branch={branch} TokenVorhanden={bool(token)}")
        if not token or repo == "USER/REPO":
            st.error("GitHub Secrets fehlen (GITHUB_TOKEN / REPO).")
        else:
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
            from hashlib import md5 as _md5
            from datetime import datetime as _dt
            updated = 0
            skipped = 0
            failed = 0
            for path, short_name in files:
                log.append(f"--- {short_name} ---")
                if not os.path.exists(path):
                    log.append("Datei fehlt lokal – übersprungen.")
                    failed += 1
                    continue
                try:
                    with open(path, "rb") as f:
                        local_bytes = f.read()
                    local_md5 = _md5(local_bytes).hexdigest()
                    local_b64 = base64.b64encode(local_bytes).decode()
                    log.append(f"Local MD5={local_md5} Bytes={len(local_bytes)}")
                except Exception as ex:
                    log.append(f"Lesefehler: {ex}")
                    failed += 1
                    continue
                api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
                sha = None
                remote_same = False
                r_get = requests.get(api_url, params={"ref": branch}, headers=headers)
                log.append(f"GET {r_get.status_code}")
                if r_get.status_code == 200:
                    try:
                        data_json = r_get.json()
                        sha = data_json.get("sha")
                        remote_content = data_json.get("content", "").strip()
                        remote_raw = "".join(remote_content.splitlines())
                        try:
                            remote_bytes = base64.b64decode(remote_raw)
                            remote_md5 = _md5(remote_bytes).hexdigest()
                            log.append(f"Remote MD5={remote_md5} Bytes={len(remote_bytes)}")
                            if remote_md5 == local_md5:
                                remote_same = True
                        except Exception as ex_md5:
                            log.append(f"Remote MD5 Fehler: {ex_md5}")
                    except Exception as ex_par:
                        log.append(f"Remote Parse Fehler: {ex_par}")
                elif r_get.status_code == 404:
                    log.append("Datei existiert remote noch nicht – wird angelegt.")
                else:
                    log.append(f"GET Fehler {r_get.status_code}: {r_get.text[:180]}")
                if remote_same:
                    log.append("Unverändert – übersprungen.")
                    skipped += 1
                    continue
                commit_msg = f"Update {short_name} {_dt.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                payload = {"message": commit_msg, "content": local_b64, "branch": branch}
                if sha:
                    payload["sha"] = sha
                r_put = requests.put(api_url, headers=headers, json=payload)
                log.append(f"PUT {r_put.status_code}")
                if r_put.status_code in (200, 201):
                    updated += 1
                elif r_put.status_code == 409:
                    log.append("409 Konflikt – Retry versuch.")
                    # Einmal SHA nachladen und erneut
                    r_get2 = requests.get(api_url, params={"ref": branch}, headers=headers)
                    if r_get2.status_code == 200:
                        try:
                            sha2 = r_get2.json().get("sha")
                            if sha2 and sha2 != sha:
                                payload["sha"] = sha2
                                r_put2 = requests.put(api_url, headers=headers, json=payload)
                                log.append(f"Retry PUT {r_put2.status_code}")
                                if r_put2.status_code in (200, 201):
                                    updated += 1
                                else:
                                    failed += 1
                            else:
                                failed += 1
                        except Exception as exr:
                            log.append(f"Retry Fehler: {exr}")
                            failed += 1
                    else:
                        failed += 1
                else:
                    log.append(f"Fehler Antwort: {r_put.text[:220]}")
                    failed += 1
            log.append(f"Ergebnis: updated={updated} skipped={skipped} failed={failed}")
        st.text_area("GitHub API Log", value="\n".join(log), height=420)

    # --- Bulk Git Commit aller Änderungen (nutzt lokales Git) ---
    st.markdown("---")
    if st.button("Alle Änderungen committen & pushen (git)"):
        log = []
        token = getattr(st, 'secrets', {}).get("GITHUB_TOKEN") if hasattr(st, 'secrets') else None
        repo = (getattr(st, 'secrets', {}).get("REPO") if hasattr(st, 'secrets') else None) or "maburgae/Gruppo-App"
        branch = (getattr(st, 'secrets', {}).get("BRANCH") if hasattr(st, 'secrets') else None) or "main"
        def run(cmd, hide=False):
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if not hide:
                    log.append(f"$ {' '.join(cmd)}\n{res.stdout}{res.stderr}")
                return res.returncode, res.stdout.strip()
            except Exception as e:
                log.append(f"FEHLER {' '.join(cmd)} -> {e}")
                return 1, ""
        # Prüfen ob Git Repo
        rc_repo, _ = run(["git", "rev-parse", "--is-inside-work-tree"])
        if rc_repo != 0:
            st.error("Kein Git-Repository verfügbar.")
        else:
            if not token:
                st.error("GITHUB_TOKEN Secret fehlt.")
            else:
                # Remote URL mit Token setzen (Token nicht ins Log schreiben!)
                safe_remote = f"https://x-access-token:***@github.com/{repo}.git"
                real_remote = f"https://x-access-token:{token}@github.com/{repo}.git"
                subprocess.run(["git", "remote", "set-url", "origin", real_remote], check=False)
                log.append(f"Remote gesetzt: {safe_remote}")
                # Git Identity sicherstellen
                rc_name, name_val = run(["git", "config", "user.name"], hide=True)
                rc_mail, mail_val = run(["git", "config", "user.email"], hide=True)
                if rc_name != 0 or not name_val:
                    run(["git", "config", "user.name", "Gruppo Streamlit Bot"])
                else:
                    log.append(f"Git user.name vorhanden: {name_val}")
                if rc_mail != 0 or not mail_val:
                    run(["git", "config", "user.email", "gruppo-bot@example.local"])
                else:
                    log.append(f"Git user.email vorhanden: {mail_val}")
                # Status anzeigen
                run(["git", "status", "-s"])
                # Änderungen hinzufügen
                run(["git", "add", "-A"])
                # Prüfen ob etwas zu committen ist
                rc_diff, diff_out = run(["git", "diff", "--cached", "--name-only"], hide=True)
                changed = [l for l in diff_out.splitlines() if l.strip()]
                if not changed:
                    log.append("Keine Änderungen zum Commit.")
                else:
                    from datetime import datetime as _dt
                    msg = f"Bulk commit via Streamlit {_dt.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    run(["git", "commit", "-m", msg])
                    # Push
                    rc_push, _ = run(["git", "push", "origin", branch])
                    if rc_push == 0:
                        st.success("Bulk Push erfolgreich.")
                    else:
                        st.error("Bulk Push fehlgeschlagen.")
        st.text_area("Bulk Git Log", value="\n".join(log), height=320)

    # Ausgabefeld "Output"
    text15("Output")
    st.text_area("Ausgabe", value=st.session_state.konf_output, key="konf_output_area", height=120)

if __name__ == "__main__":
    import streamlit as st
    render(st)
