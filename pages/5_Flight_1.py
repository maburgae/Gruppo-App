import json
import pandas as pd
import os

def render(st):
    st.markdown(
        """
        <style>
        html, body, p, span, div, label, .stButton > button {font-size:15px !important;}
        /* Rote Buttons */
        div.stButton > button {
            background-color: #c00000 !important;
            color: #ffffff !important;
            border: 1px solid #900000 !important;
        }
        div.stButton > button:hover {
            background-color: #ff1a1a !important;
            border-color: #b00000 !important;
            color:#ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Flight 1")

    json_path = "json/golf_df/golf_df.json"
    if not os.path.exists(json_path):
        st.error("golf_df.json nicht gefunden.")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            golf_data = json.load(f)
    except Exception as e:
        st.error(f"Fehler beim Lesen der golf_df.json: {e}")
        return

    if not isinstance(golf_data, dict) or len(golf_data) == 0:
        st.error("golf_df.json hat kein gültiges Format.")
        return

    date_key = next(iter(golf_data.keys()))
    round_data = golf_data[date_key]
    spieler = round_data.get("Spieler", {})

    # Filter Spieler fuer Flight 1
    flight_players = {name: pdata for name, pdata in spieler.items() if str(pdata.get("Flight")) == "1"}
    if not flight_players:
        st.info("Keine Spieler mit Flight '1' vorhanden.")
        return

    # 1) Eingabetabelle (Scores)
    columns = [str(i) for i in range(1, 19)]
    df_rows = []
    index = []
    for name, pdata in flight_players.items():
        scores = pdata.get("Score", [None]*18)
        row = [v if v is None else v for v in scores]
        df_rows.append(row)
        index.append(name)
    edit_df = pd.DataFrame(df_rows, columns=columns, index=index)
    st.markdown("Eingabetabelle (Scores)")
    edited = st.data_editor(
        edit_df,
        key="flight1_editor",
        hide_index=False,
        width='stretch'
    )
    # Speichern-Button direkt unter der Score-Tabelle platzieren
    save_clicked = st.button("Speichern", key="flight1_save")

    # 2) Ladiestabelle (alle Spieler der Runde) + LD/N2TP rechts daneben
    ladies_rows = [{"Spieler": name, "Ladies": pdata.get("Ladies")} for name, pdata in spieler.items()]
    ladies_df = pd.DataFrame(ladies_rows, columns=["Spieler", "Ladies"])

    col_table, col_selects = st.columns([2,1])  # schmalere Tabelle
    with col_table:
        st.markdown("Ladiestabelle")
        FIXED_WIDTH = 230  # feste Breite in Pixel
        st.markdown(
            f"""
            <style>
            #ladies_f1 div[data-testid='stDataEditor'] {{
                width:{FIXED_WIDTH}px !important;
                min-width:{FIXED_WIDTH}px !important;
                max-width:{FIXED_WIDTH}px !important;
            }}
            #ladies_f1 div[data-testid='stDataEditor'] table {{
                width:{FIXED_WIDTH}px !important;
            }}
            #ladies_f1 div[data-testid='stDataEditor'] tbody td, 
            #ladies_f1 div[data-testid='stDataEditor'] thead th {{
                padding:2px 4px !important;
                white-space:nowrap !important;
            }}
            </style>
            <div id='ladies_f1'></div>
            """,
            unsafe_allow_html=True,
        )
        # Platzieren des Editors innerhalb des Containers durch erneutes Öffnen (CSS greift global innerhalb des Wrappers)
        ladies_edited = st.data_editor(
            ladies_df,
            key="flight1_ladies_editor",
            hide_index=True,
            width='content',
            column_config={
                "Spieler": {"width": "small"},
                "Ladies": {"width": "small"}
            }
        )
    with col_selects:
        all_player_names = list(spieler.keys())
        ld_winner = next((n for n, d in spieler.items() if str(d.get("LD")) == "1"), "Keiner")
        n2tp_winner = next((n for n, d in spieler.items() if str(d.get("N2TP")) == "1"), "Keiner")
        ld_selection = st.selectbox(
            "LD",
            ["Keiner"] + all_player_names,
            index=( ["Keiner"] + all_player_names ).index(ld_winner) if ld_winner in ( ["Keiner"] + all_player_names ) else 0,
            key="flight1_ld_select"
        )
        n2tp_selection = st.selectbox(
            "N2TP",
            ["Keiner"] + all_player_names,
            index=( ["Keiner"] + all_player_names ).index(n2tp_winner) if n2tp_winner in ( ["Keiner"] + all_player_names ) else 0,
            key="flight1_n2tp_select"
        )

    # Speichern-Logik jetzt hier (nachdem alle Widgets definiert wurden)
    if save_clicked:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                current_data = json.load(f)
            dkey = next(iter(current_data.keys()))
            rd = current_data[dkey]
            # Scores aktualisieren (nur Flight 1)
            for pname in flight_players.keys():
                if pname in edited.index:
                    row = edited.loc[pname]
                    new_scores = []
                    for col in columns:
                        val = row[col]
                        if pd.isna(val):
                            new_scores.append(None)
                        else:
                            try:
                                new_scores.append(int(val))
                            except (ValueError, TypeError):
                                new_scores.append(None)
                    rd["Spieler"][pname]["Score"] = new_scores
            # Ladies aktualisieren (alle Spieler)
            for _, row in ladies_edited.iterrows():
                pname = row.get("Spieler")
                if pname in rd["Spieler"].keys():
                    val = row.get("Ladies")
                    if pd.isna(val):
                        rd["Spieler"][pname]["Ladies"] = None
                    else:
                        try:
                            rd["Spieler"][pname]["Ladies"] = int(val)
                        except (ValueError, TypeError):
                            rd["Spieler"][pname]["Ladies"] = None
            # LD setzen
            if ld_selection == "Keiner":
                for pname in rd["Spieler"]:
                    rd["Spieler"][pname]["LD"] = None
            else:
                for pname in rd["Spieler"]:
                    rd["Spieler"][pname]["LD"] = 1 if pname == ld_selection else None
            # N2TP setzen
            if n2tp_selection == "Keiner":
                for pname in rd["Spieler"]:
                    rd["Spieler"][pname]["N2TP"] = None
            else:
                for pname in rd["Spieler"]:
                    rd["Spieler"][pname]["N2TP"] = 1 if pname == n2tp_selection else None
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)
            st.success("Scores, Ladies und Sonderwertungen für Flight 1 gespeichert.")
        except Exception as e:
            st.error(f"Fehler beim Speichern: {e}")

if __name__ == "__main__":
    import streamlit as st
    render(st)
