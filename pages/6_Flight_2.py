import json
import pandas as pd
import os

def render(st):
    st.markdown(
        """
        <style>
        html, body, p, span, div, label, .stButton > button {font-size:15px !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Flight 2")

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

    # Filter Spieler fuer Flight 2
    flight_players = {name: pdata for name, pdata in spieler.items() if str(pdata.get("Flight")) == "2"}
    if not flight_players:
        st.info("Keine Spieler mit Flight '2' vorhanden.")
        return

    # DataFrame bauen: Zeilen = Spieler, Spalten = 1..18 mit bestehenden Scores
    columns = [str(i) for i in range(1, 19)]
    df_rows = []
    index = []
    for name, pdata in flight_players.items():
        scores = pdata.get("Score", [None]*18)
        row = []
        for v in scores:
            row.append(v if v is None else v)
        df_rows.append(row)
        index.append(name)
    edit_df = pd.DataFrame(df_rows, columns=columns, index=index)

    st.markdown("Eingabetabelle (Scores)")
    edited = st.data_editor(
        edit_df,
        key="flight2_editor",
        hide_index=False,
        width='stretch'
    )

    if st.button("Speichern", key="flight2_save"):
        # Beim Speichern nur die Scores für Flight 2 Spieler aktualisieren
        try:
            # Frische Version erneut laden
            with open(json_path, "r", encoding="utf-8") as f:
                current_data = json.load(f)
            dkey = next(iter(current_data.keys()))
            rd = current_data[dkey]
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
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)
            st.success("Scores für Flight 2 gespeichert.")
        except Exception as e:
            st.error(f"Fehler beim Speichern: {e}")

if __name__ == "__main__":
    import streamlit as st
    render(st)
