import json
import pandas as pd

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

def render(st):
    _init_state()

    st.header("Konfiguration")

    # Knopf "Neue Runde"
    if st.button("Neue Runde"):
        try:
            players = json.loads(st.session_state.konf_players)
            if not isinstance(players, list):
                raise ValueError("Spieler muss eine JSON-Liste sein.")
        except Exception as e:
            st.session_state.konf_output = f"Fehler: Ungültiges Spieler-Format: {e}"
        else:
            result = neue_runde_main(players)
            st.session_state.konf_output = result

    # Eingabefeld "Spieler"
    st.text_input("Spieler (JSON-Liste)", value=st.session_state.konf_players, key="konf_players")

    # Knopf "Upload Scorecard" mit Dateiupload
    uploaded_file = st.file_uploader("Scorecard Datei auswählen", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        file_path = f"pics/{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        result = upload_scorecard_main(file_path)
        st.session_state.konf_output = result
        st.session_state.konf_file_id = result  # Store returned file_id
        print("uploaded file is not none")

    # Editierbare Tabelle für Par, Hcp und Scores aller Spieler
    import pandas as pd
    import json
    with open("json/golf_df/golf_df.json", "r", encoding="utf-8") as f:
        golf_data = json.load(f)
    key = list(golf_data.keys())[0]
    data = golf_data[key]
    # Build DataFrame for editing
    # First two rows: Par, Hcp
    edit_rows = [ ["Par"] + data["Par"], ["Hcp"] + data["Hcp"] ]
    # Next: Score rows for each player
    for player, pdata in data["Spieler"].items():
        edit_rows.append([f"Score {player}"] + pdata["Score"])
    # Prepare columns: 18 holes + 3 extra columns for LD, N2TP, Ladies
    columns = ["Type"] + [f"{i+1}" for i in range(18)] + ["LD", "N2TP", "Ladies"]
    # Add LD, N2TP, Ladies values for each player to their score row
    for idx, player in enumerate(data["Spieler"].keys()):
        score_row_idx = 2 + idx
        pdata = data["Spieler"][player]
        edit_rows[score_row_idx] += [pdata.get("LD", None), pdata.get("N2TP", None), pdata.get("Ladies", None)]
    edit_df = pd.DataFrame(edit_rows, columns=columns)
    st.subheader("golf_df (Par, Hcp, Scores, LD, N2TP, Ladies)")
    st.session_state.golf_df = st.data_editor(edit_df, key="golf_df_editor_full", width='stretch', column_config={col: {"width": "small"} for col in edit_df.columns})

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
        new_par = [nan_to_null_int(x) for x in list(edited_df.iloc[0, 1:19])]
        new_hcp = [nan_to_null_int(x) for x in list(edited_df.iloc[1, 1:19])]
        new_scores = {}
        new_ld = {}
        new_n2tp = {}
        new_ladies = {}
        # Only process score rows (skip Par/Hcp)
        for idx in range(2, edited_df.shape[0]):
            row = edited_df.iloc[idx]
            player = row[0].replace("Score ", "")
            scores = [nan_to_null_int(x) for x in list(row[1:19])]
            ld = nan_to_null_int(row[19])
            n2tp = nan_to_null_int(row[20])
            ladies = nan_to_null_int(row[21])
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
        for player in data["Spieler"]:
            if player in new_scores:
                data["Spieler"][player]["Score"] = new_scores[player]
            if player in new_ld:
                data["Spieler"][player]["LD"] = new_ld[player]
            if player in new_n2tp:
                data["Spieler"][player]["N2TP"] = new_n2tp[player]
            if player in new_ladies:
                data["Spieler"][player]["Ladies"] = new_ladies[player]
        with open("json/golf_df/golf_df.json", "w", encoding="utf-8") as f:
            json.dump(golf_data, f, ensure_ascii=False, indent=2)
        st.success("Tabelle erfolgreich gespeichert!")

    # Knopf "Berechne den Tag"
    if st.button("Berechne den Tag"):
        result = berechne_den_tag_main()
        st.session_state.konf_output = result

    # Show a picture only if the file exists
    if os.path.exists("pics/scorecard.png"):
        st.image("pics/scorecard.png", caption="Scorecard", use_column_width=True)

    if os.path.exists("pics/ranking.png"):
        st.image("pics/ranking.png", caption="Ranking", use_column_width=True)


    # Knopf: "Tag -> Alle Runden"
    if st.button("Tag -> Alle Runden"):
        result = tag_to_alle_runden_main()
        st.session_state.konf_output = result

    # Knopf: "Erzeuge Stats"
    if st.button("Erzeuge Stats"):
        result = erzeuge_stats_main()
        st.session_state.konf_output = result

    # Ausgabefeld "Output"
    st.subheader("Output")
    st.text_area("Ausgabe", value=st.session_state.konf_output, key="konf_output_area", height=120)
