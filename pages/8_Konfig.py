import json
import pandas as pd
import os
import base64
import requests

from actions.neue_runde import main as neue_runde_main
from actions.upload_scorecard import main as upload_scorecard_main
from actions.berechne_den_tag import main as berechne_den_tag_main
from actions.tag_to_alle_runden import main as tag_to_alle_runden_main
from actions.erzeuge_stats import main as erzeuge_stats_main
import os

DEFAULT_PLAYERS_STR = '["Marc","Andy","Bernie","Jens","Heiko","Markus","Buffy"]'

def _init_state():
    import streamlit as st
    if "konf_players" not in st.session_state:
        st.session_state.konf_players = DEFAULT_PLAYERS_STR
    if "konf_file_id" not in st.session_state:
        st.session_state.konf_file_id = ""
    if "konf_output" not in st.session_state:
        st.session_state.konf_output = ""
    if "golf_df" not in st.session_state:
        st.session_state.golf_df = pd.DataFrame({
            "Hole": list(range(1, 7)),
            "Par": [4,4,5,3,4,5],
            "Hcp": [9,7,11,15,13,17]
        })
    # Track uploads to avoid re-processing on every rerun
    if "konf_uploaded_name" not in st.session_state:
        st.session_state.konf_uploaded_name = ""
    if "konf_preprocess" not in st.session_state:
        st.session_state.konf_preprocess = True


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

    # Eingabefeld "Spieler"
    st.text_input(
        "Spieler (JSON-Liste)",
        value=st.session_state.get("konf_players", DEFAULT_PLAYERS_STR),
        key="konf_players",
    )
    # Eingabefeld Platzname (voreingestellt mit vorhandenem Ort)
    platzname = st.text_input(
        "Platzname",
        key="konf_platzname",
        value=st.session_state.get("konf_platzname_val", existing_ort)
    )
    st.session_state["konf_platzname_val"] = platzname

    # Dynamische Flight-Eingaben unter Neue Runde
    flight_values = {}
    existing_flights = {}
    try:
        with open("json/golf_df/golf_df.json", "r", encoding="utf-8") as _gf:
            _golf_existing = json.load(_gf)
        if isinstance(_golf_existing, dict) and len(_golf_existing) > 0:
            _date_key_exist = next(iter(_golf_existing.keys()))
            _round_exist = _golf_existing[_date_key_exist]
            for _p, _pdata in _round_exist.get("Spieler", {}).items():
                existing_flights[_p] = _pdata.get("Flight")
    except Exception:
        pass
    try:
        _player_list = json.loads(st.session_state.konf_players)
        if isinstance(_player_list, list):
            st.markdown("**Flights (optional)**")
            cols = st.columns(min(7, max(1, len(_player_list))))
            for idx, pname in enumerate(_player_list):
                col = cols[idx % len(cols)]
                state_key = f"flight_{pname}"
                if state_key not in st.session_state:
                    existing_val = existing_flights.get(pname)
                    st.session_state[state_key] = "" if existing_val in (None, "None") else str(existing_val)
                flight_values[pname] = col.text_input(f"{pname}", key=state_key)
    except Exception:
        _player_list = []

    # Knopf "Neue Runde"
    if st.button("Neue Runde"):
        try:
            players = json.loads(st.session_state.konf_players)
            if not isinstance(players, list):
                raise ValueError("Spieler muss eine JSON-Liste sein.")
        except Exception as e:
            st.session_state.konf_output = f"Fehler: Ungültiges Spieler-Format: {e}"
        else:
            result = neue_runde_main(players, flights=flight_values, ort=platzname.strip())
            st.session_state.konf_output = result

    # Option: Preprocess vor Upload
    st.checkbox("Bild vor Upload vorverarbeiten (empfohlen)", key="konf_preprocess", value=st.session_state.get("konf_preprocess", True))

    # Knopf "Upload Scorecard" mit Dateiupload
    uploaded_file = st.file_uploader("Scorecard Datei auswählen", type=["jpg", "jpeg", "png"], key="konf_uploader")
    if uploaded_file is not None:
        # Only process once per filename to avoid re-running on every rerun
        if st.session_state.konf_uploaded_name != uploaded_file.name:
            file_path = f"{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            # Pass user choice for preprocessing
            result = upload_scorecard_main(file_path, pre_process=st.session_state.get("konf_preprocess", True))
            st.session_state.konf_output = result
            st.session_state.konf_file_id = result  # Store returned file_id
            st.session_state.konf_uploaded_name = uploaded_file.name
            print("uploaded file processed once")
        else:
            # Skip re-processing; file already handled
            pass

    # Editierbare Tabelle für Par, Hcp und Scores aller Spieler
    with open("json/golf_df/golf_df.json", "r", encoding="utf-8") as f:
        golf_data = json.load(f)
    key = list(golf_data.keys())[0]
    data = golf_data[key]
    # Build DataFrame for editing (remove index column; use explicit 'Spieler' column; no 'Score ' prefixes)
    # First two rows: Par, Hcp
    edit_rows = [["Par"] + data["Par"], ["Hcp"] + data["Hcp"]]
    # Next: one row per player with their scores
    for player, pdata in data["Spieler"].items():
        edit_rows.append([player] + pdata.get("Score", []))
    # Prepare columns: Spieler + 18 holes + 3 extra columns for LD, N2TP, Ladies
    columns = ["Spieler"] + [f"{i+1}" for i in range(18)] + ["LD", "N2TP", "Ladies"]
    # Append LD, N2TP, Ladies values for each player row
    for idx, player in enumerate(data["Spieler"].keys()):
        row_idx = 2 + idx
        pdata = data["Spieler"][player]
        # Ensure row length before extending
        while len(edit_rows[row_idx]) < 1 + 18:
            edit_rows[row_idx].append(None)
        edit_rows[row_idx] += [pdata.get("LD", None), pdata.get("N2TP", None), pdata.get("Ladies", None)]
    # Pad all rows to full length
    for r in edit_rows:
        while len(r) < len(columns):
            r.append(None)
    edit_df = pd.DataFrame(edit_rows, columns=columns)
    text15("Scorecard Tabelle")
    # Configure editor: hide index, pin Spieler column to the left (if supported), narrow widths
    col_cfg = {col: {"width": "small"} for col in edit_df.columns}
    # Try to pin the Spieler column to the left; if unsupported, it's simply ignored
    col_cfg["Spieler"]["pinned"] = "left"

    # Helper: mark editor changes without triggering heavy computations
    def _mark_golf_df_dirty():
        st.session_state["golf_df_dirty"] = True

    st.session_state.golf_df = st.data_editor(
        edit_df,
        key="golf_df_editor_full",
        width='stretch',
        hide_index=True,
        column_config=col_cfg,
        on_change=_mark_golf_df_dirty,
    )

    # Knopf zum Speichern der Tabelle ins JSON
    if st.button("Tabelle speichern"):
        edited_df = st.session_state.golf_df
        def nan_to_null_int(val):
            if pd.isna(val):
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None
        new_par = [nan_to_null_int(edited_df.iloc[0, i]) for i in range(1, 19)]
        new_hcp = [nan_to_null_int(edited_df.iloc[1, i]) for i in range(1, 19)]
        new_scores = {}
        new_ld = {}
        new_n2tp = {}
        new_ladies = {}
        # Only process player rows (skip Par/Hcp)
        for idx in range(2, edited_df.shape[0]):
            row = edited_df.iloc[idx]
            player = str(row.iloc[0]).strip()
            scores = [nan_to_null_int(row.iloc[i]) for i in range(1, 19)]
            ld = nan_to_null_int(row.iloc[19])
            n2tp = nan_to_null_int(row.iloc[20])
            ladies = nan_to_null_int(row.iloc[21])
            new_scores[player] = scores
            new_ld[player] = ld
            new_n2tp[player] = n2tp
            new_ladies[player] = ladies
        with open("json/golf_df/golf_df.json", "r", encoding="utf-8") as f:
            golf_data = json.load(f)
        key = list(golf_data.keys())[0]
        data = golf_data[key]
        data["Par"] = new_par
        data["Hcp"] = new_hcp
        # Ort aktualisieren falls Eingabe vorhanden
        _platz_eingabe = st.session_state.get("konf_platzname", "").strip()
        if _platz_eingabe:
            data["Ort"] = _platz_eingabe
        for player in data["Spieler"]:
            if player in new_scores:
                data["Spieler"][player]["Score"] = new_scores[player]
            if player in new_ld:
                data["Spieler"][player]["LD"] = new_ld[player]
            if player in new_n2tp:
                data["Spieler"][player]["N2TP"] = new_n2tp[player]
            if player in new_ladies:
                data["Spieler"][player]["Ladies"] = new_ladies[player]
            # Flight Werte aus den Eingabefeldern übernehmen
            flight_state_key = f"flight_{player}"
            flight_val = st.session_state.get(flight_state_key, "")
            if isinstance(flight_val, str):
                flight_val = flight_val.strip()
            data["Spieler"][player]["Flight"] = flight_val if flight_val else None
        with open("json/golf_df/golf_df.json", "w", encoding="utf-8") as f:
            json.dump(golf_data, f, ensure_ascii=False, indent=2)
        st.session_state["golf_df_dirty"] = False
        st.success("Tabelle erfolgreich gespeichert (inkl. Ort & Flight)!")

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

    # --- GitHub API Commit für allrounds.json (ersetzt lokalen Git Push) ---
    st.markdown("---")
    if st.button("allrounds.json zu GitHub committen (API)"):
        log = []
        path = "json/allrounds.json"
        token = getattr(st, 'secrets', {}).get("GITHUB_TOKEN") if hasattr(st, 'secrets') else None
        repo = (getattr(st, 'secrets', {}).get("REPO") if hasattr(st, 'secrets') else None) or "USER/REPO"
        branch = (getattr(st, 'secrets', {}).get("BRANCH") if hasattr(st, 'secrets') else None) or "main"
        if not token or repo == "USER/REPO":
            st.error("GitHub Secrets fehlen (GITHUB_TOKEN / REPO).")
        else:
            try:
                with open(path, "rb") as f:
                    local_bytes = f.read()
                local_b64 = base64.b64encode(local_bytes).decode()
            except Exception as e:
                st.error(f"Datei kann nicht gelesen werden: {e}")
            else:
                headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
                api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
                # Remote SHA & Inhalt holen
                r_get = requests.get(api_url, params={"ref": branch}, headers=headers)
                log.append(f"GET {r_get.status_code}")
                sha = None
                remote_same = False
                if r_get.status_code == 200:
                    try:
                        data_json = r_get.json()
                        sha = data_json.get("sha")
                        remote_content = data_json.get("content", "").strip()
                        # GitHub liefert Base64 mit evtl. Zeilenumbrüchen
                        remote_raw = "".join(remote_content.splitlines())
                        remote_same = (remote_raw == local_b64)
                        if remote_same:
                            log.append("Keine Änderung: lokaler Inhalt == remote.")
                    except Exception as ex:
                        log.append(f"Remote Parse Fehler: {ex}")
                elif r_get.status_code == 404:
                    log.append("Datei existiert noch nicht remote (wird erstellt).")
                else:
                    log.append(f"Unerwarteter GET Status {r_get.status_code}: {r_get.text[:120]}")
                if remote_same:
                    st.info("Keine Änderung – Commit übersprungen.")
                else:
                    from datetime import datetime as _dt
                    commit_msg = f"Update allrounds.json {_dt.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    payload = {"message": commit_msg, "content": local_b64, "branch": branch}
                    if sha:
                        payload["sha"] = sha
                    r_put = requests.put(api_url, headers=headers, json=payload)
                    log.append(f"PUT {r_put.status_code}")
                    if r_put.status_code in (200, 201):
                        st.success("Commit erfolgreich.")
                    elif r_put.status_code == 409:
                        st.warning("409 Konflikt – versuche erneutes Laden.")
                        r_get2 = requests.get(api_url, params={"ref": branch}, headers=headers)
                        if r_get2.status_code == 200:
                            try:
                                sha2 = r_get2.json().get("sha")
                                if sha2 and sha2 != sha:
                                    payload["sha"] = sha2
                                    r_put2 = requests.put(api_url, headers=headers, json=payload)
                                    log.append(f"Retry PUT {r_put2.status_code}")
                                    if r_put2.status_code in (200, 201):
                                        st.success("Commit nach Retry erfolgreich.")
                                    else:
                                        st.error(f"Retry fehlgeschlagen ({r_put2.status_code}).")
                                else:
                                    st.error("Konflikt bleibt bestehen.")
                            except Exception as ex:
                                st.error(f"Retry Fehler: {ex}")
                        else:
                            st.error("Neuladen für Konfliktlösung fehlgeschlagen.")
                    else:
                        st.error(f"Commit fehlgeschlagen ({r_put.status_code}).")
                st.text_area("GitHub API Log", value="\n".join(log), height=260)

    # Ausgabefeld "Output"
    text15("Output")
    st.text_area("Ausgabe", value=st.session_state.konf_output, key="konf_output_area", height=120)

if __name__ == "__main__":
    import streamlit as st
    render(st)
