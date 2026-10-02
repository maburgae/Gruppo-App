import json
import os
import base64
import requests
import subprocess  # für Bulk Git Commit
from datetime import date

from actions.neue_runde import main as neue_runde_main
from actions.upload_scorecard import main as upload_scorecard_main
from actions.berechne_den_tag import main as berechne_den_tag_main
from actions.tag_to_alle_runden import main as tag_to_alle_runden_main
from actions.erzeuge_stats import main as erzeuge_stats_main
import os

DEFAULT_PLAYERS_STR = '["Marc","Andy","Bernie","Jens","Heiko","Markus","Buffy"]'
ROUND_PLAYERS = ["Marc", "Andy", "Bernie", "Jens", "Markus", "Buffy"]
UPLOAD_MODEL_OPTIONS = [
    "gpt-5-mini",
    "gpt-5",
    "gpt-4.1",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-5-nano",
]

def _init_state():
    import streamlit as st
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
        st.session_state.konf_preprocess = True
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
        html, body, p, ol, ul, dl, span, div,
        [data-testid='stMarkdownContainer'] p,
        [data-testid='stMarkdownContainer'] span,
        h1, h2, h3, h4, h5, h6,
        [data-testid='stHeader'] h1,
        label,
        .stButton > button,
        .stDownloadButton > button,
        .stTextInput label,
        .stSelectbox label,
        .stFileUploader label {
            font-size: 15px !important;
        }
        .compact-player-grid div[data-testid='stCheckbox'] {
            margin-bottom: 0.1rem !important;
        }
        .compact-player-grid div[data-testid='stSelectbox'] {
            margin-top: -0.2rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    def text15(s: str):
        st.markdown(f"<span style='font-size:15px'>{s}</span>", unsafe_allow_html=True)

    _init_state()

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

    text15("Konfiguration")

    # Vorab vorhandenen Ort laden (falls vorhanden) um Platzname vorzubelegen
    existing_ort = ""
    try:
        with open("json/golf_df/golf_df.json", "r", encoding="utf-8") as _f_ort:
            _gdf_tmp = json.load(_f_ort)
        if isinstance(_gdf_tmp, dict) and len(_gdf_tmp) > 0:
            _dk = next(iter(_gdf_tmp.keys()))
            existing_ort = _gdf_tmp[_dk].get("Ort", "") or ""
    except Exception:
        pass

    if not st.session_state.get("konf_platzname_val"):
        if existing_ort:
            st.session_state["konf_platzname_val"] = existing_ort
            st.session_state["konf_platzname"] = existing_ort

    # Eingabefeld Platzname (voreingestellt mit vorhandenem Ort)
    platzname = st.text_input(
        "Platzname",
        key="konf_platzname",
        value=st.session_state.get("konf_platzname_val", existing_ort)
    )
    st.session_state["konf_platzname_val"] = platzname

    # Datum für die neue Runde (default: heute, aber änderbar)
    round_date = st.date_input("Datum", key="konf_round_date")

    # Feste Spielerauswahl mit Flight-Dropdown je Spieler
    st.markdown("**Spieler**")
    flight_values = {}
    selected_players = []
    st.markdown("<div class='compact-player-grid'>", unsafe_allow_html=True)
    player_cols = st.columns(len(ROUND_PLAYERS), gap="small")
    for col, pname in zip(player_cols, ROUND_PLAYERS):
        checked = col.checkbox(pname, key=f"konf_player_{pname}")
        col.selectbox("Flight", options=["1", "2"], key=f"flight_{pname}")
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
            st.session_state.konf_output = result

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

    # Dropdown-Editor für Par, Hcp und Scores aller Spieler
    with open("json/golf_df/golf_df.json", "r", encoding="utf-8") as f:
        golf_data = json.load(f)
    key = list(golf_data.keys())[0]
    data = golf_data[key]
    text15("Scorecard Eingabe (Dropdowns)")

    PAR_OPTIONS = [3, 4, 5]
    HCP_OPTIONS = list(range(1, 19))
    SCORE_OPTIONS = [None] + list(range(1, 11))

    def _norm_list(vals, fill=None):
        out = list(vals or [])
        while len(out) < 18:
            out.append(fill)
        return out[:18]

    def _coerce_for_options(value, options):
        if value in options:
            return value
        if value is None:
            return options[0]
        try:
            iv = int(value)
            if iv in options:
                return iv
        except Exception:
            pass
        return options[0]

    def _draw_score_section(container, section_title: str, start_idx: int, end_idx: int,
                            par_values: list, hcp_values: list, player_values: dict):
        container.markdown(f"**{section_title}**")

        # Header row (holes)
        header_cols = container.columns([1.8] + [1] * 9)
        header_cols[0].markdown("&nbsp;", unsafe_allow_html=True)
        for c, hole_idx in enumerate(range(start_idx, end_idx), start=1):
            header_cols[c].markdown(f"<b>{hole_idx + 1}</b>", unsafe_allow_html=True)

        def _draw_row(row_label: str, key_prefix: str, values: list, options: list):
            cols = container.columns([1.8] + [1] * 9)
            cols[0].markdown(f"<b>{row_label}</b>", unsafe_allow_html=True)
            picked = []
            norm_values = _norm_list(values)
            for c, hole_idx in enumerate(range(start_idx, end_idx), start=1):
                v = _coerce_for_options(norm_values[hole_idx], options)
                idx = options.index(v) if v in options else 0
                picked.append(cols[c].selectbox(
                    f"{row_label} {hole_idx+1}",
                    options=options,
                    index=idx,
                    key=f"{key_prefix}_{hole_idx+1}",
                    format_func=(lambda x: "" if x is None else str(x)),
                    label_visibility="collapsed",
                ))
            return picked

        section_par = _draw_row("PAR", "konf_par", par_values, PAR_OPTIONS)
        section_hcp = _draw_row("HCP", "konf_hcp", hcp_values, HCP_OPTIONS)

        section_scores = {}
        for player_name, score_vals in player_values.items():
            section_scores[player_name] = _draw_row(player_name, f"konf_score_{player_name}", score_vals, SCORE_OPTIONS)

        return section_par, section_hcp, section_scores

    current_par = _norm_list(data.get("Par", []))
    current_hcp = _norm_list(data.get("Hcp", []))
    players_present = list(data.get("Spieler", {}).keys())
    current_scores = {
        player: _norm_list(data["Spieler"].get(player, {}).get("Score", []))
        for player in players_present
    }

    new_par = list(current_par)
    new_hcp = list(current_hcp)
    new_scores = {player: list(vals) for player, vals in current_scores.items()}

    left_par, left_hcp, left_scores = _draw_score_section(
        st, "Löcher 1-9", 0, 9, current_par, current_hcp, current_scores
    )
    right_par, right_hcp, right_scores = _draw_score_section(
        st, "Löcher 10-18", 9, 18, current_par, current_hcp, current_scores
    )

    for i in range(9):
        new_par[i] = left_par[i]
        new_hcp[i] = left_hcp[i]
        new_par[i + 9] = right_par[i]
        new_hcp[i + 9] = right_hcp[i]

    for player in players_present:
        left_vals = left_scores.get(player, [None] * 9)
        right_vals = right_scores.get(player, [None] * 9)
        for i in range(9):
            new_scores[player][i] = left_vals[i]
            new_scores[player][i + 9] = right_vals[i]

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
        st.success("Änderung gespeichert.")

    # Separate heavy computation button
    if st.button("Berechne den Tag"):
        try:
            result = berechne_den_tag_main()
            result2 = erzeuge_stats_main()
            st.session_state.konf_output = f"Berechne:{result}, Pics: {result2}"
            # Nach Berechnung: Previews in pics/ aktualisieren
            try:
                import shutil
                with open("json/golf_df/golf_df.json", "r", encoding="utf-8") as f:
                    _tag = json.load(f)
                date_key = next(iter(_tag.keys()))
                os.makedirs("rankings", exist_ok=True)
                os.makedirs("scorecards", exist_ok=True)
                src_front = f"scorecards/{date_key}_front.png"
                src_back = f"scorecards/{date_key}_back.png"
                src_rank = f"rankings/{date_key}.png"
               
            except Exception:
                pass
            st.success("Tag berechnet und Previews aktualisiert.")
        except Exception as e:
            st.error(f"Fehler bei der Tagesberechnung: {e}")

        shown_any = False
        if os.path.exists(src_front):
            st.image(src_front, caption="Scorecard Front", width='stretch')
            shown_any = True
        if os.path.exists(src_back):
            st.image(src_back, caption="Scorecard Back", width='stretch')
            shown_any = True

        if os.path.exists(src_rank):
            st.image(src_rank, caption="Ranking", width='stretch')

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
