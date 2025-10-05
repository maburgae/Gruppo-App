import json
import os
from datetime import datetime
import pandas as pd
import uuid  # hinzugefügt für eindeutige IDs

EXPENSE_FILE = "json/abrechnung.json"

DEFAULT_PLAYERS = ["Marc","Andy","Bernie","Jens","Heiko","Markus","Buffy"]

STYLE_CSS = """
<style>
html, body, p, span, div, label, .stButton > button, .stTextInput label, .stSelectbox label, .stCheckbox label {font-size:15px !important;}
.stButton > button {background:#0b5ed7; color:#fff; border:1px solid #084298;}
.stButton > button:hover {background:#0a53be; border-color:#06357a;}
</style>
"""

def _load_players():
    # Versuche Spieler aus aktueller Runde (golf_df) oder allrounds zu sammeln
    players = set()
    try:
        with open("json/golf_df/golf_df.json","r",encoding="utf-8") as f:
            gdf = json.load(f)
        if isinstance(gdf, dict) and gdf:
            k = next(iter(gdf.keys()))
            sp = gdf[k].get("Spieler", {})
            players.update(sp.keys())
    except Exception:
        pass
    if not players:
        try:
            with open("json/allrounds.json","r",encoding="utf-8") as f:
                allr = json.load(f)
            for _, robj in allr.items():
                for n in robj.get("Spieler", {}).keys():
                    players.add(n)
        except Exception:
            pass
    # Stelle sicher, dass Standardspieler (inkl. Heiko) immer enthalten sind
    players.update(DEFAULT_PLAYERS)
    # Reihenfolge egal laut User, daher einfache sortierte Liste zurück
    return sorted(players)


def _load_expenses():
    if not os.path.exists(EXPENSE_FILE):
        return []
    try:
        with open(EXPENSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            # IDs nachrüsten falls fehlen
            changed = False
            for e in data:
                if "id" not in e:
                    e["id"] = str(uuid.uuid4())
                    changed = True
            if changed:
                _save_expenses(data)
            return data
    except Exception:
        pass
    return []


def _save_expenses(expenses: list):
    os.makedirs(os.path.dirname(EXPENSE_FILE), exist_ok=True)
    with open(EXPENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(expenses, f, ensure_ascii=False, indent=2)


def render(st):
    st.markdown(STYLE_CSS, unsafe_allow_html=True)
    st.markdown("### Abrechnung")

    players = _load_players()
    expenses = _load_expenses()

    # Formular-Bereich
    st.markdown("**Neue Ausgabe**")
    payer = st.selectbox("Bezahlt von", players, key="abrechnung_payer")
    st.markdown("Betroffene / Profitierer:")
    beneficiary_flags = {}
    cols = st.columns(min(6, max(1, len(players))))
    for i, p in enumerate(players):
        beneficiary_flags[p] = cols[i % len(cols)].checkbox(p, value=True, key=f"ab_ben_{p}")
    amount_str = st.text_input("Betrag", value="", key="ab_betrag", help="Numerischer Betrag (Komma oder Punkt)")
    descr = st.text_input("Beschreibung", value="", key="ab_descr")

    add_clicked = st.button("Ausgabe hinzufügen")

    if add_clicked:
        # Validierung
        try:
            amount_clean = amount_str.replace(",", ".").strip()
            amount = float(amount_clean)
        except Exception:
            st.error("Ungültiger Betrag.")
            return
        beneficiaries = [p for p, flag in beneficiary_flags.items() if flag]
        if not beneficiaries:
            st.error("Mindestens ein Profitierer auswählen.")
            return
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "payer": payer,
            "beneficiaries": beneficiaries,
            "amount": amount,
            "description": descr.strip(),
        }
        expenses.append(entry)
        _save_expenses(expenses)
        st.success("Ausgabe gespeichert.")
        # Rerun (Streamlit >=1.32: st.rerun())
        try:
            st.rerun()
        except Exception:
            try:
                st.experimental_rerun()  # fallback for older versions
            except Exception:
                pass

    # Verteilungstabelle unterhalb des Speicherns
    if expenses:
        st.markdown("**Verteilung (Netto je Spieler)**")
        # Alle Spieler (bereits in players)
        alloc_rows = []
        totals = {p: 0.0 for p in players}
        for e in expenses:
            amt = e.get("amount", 0.0) or 0.0
            try:
                amt = float(amt)
            except Exception:
                amt = 0.0
            bens = e.get("beneficiaries", []) or []
            bens = [b for b in bens if b in players]
            n_bens = len(bens) if len(bens) > 0 else 1
            share = amt / n_bens
            payer_name = e.get("payer", "")
            row_label = f"{payer_name} {e.get('description','').strip()} ({amt:.2f})".strip()
            row_dict = {"Ausgabe": row_label}
            for p in players:
                val = 0.0
                if p == payer_name:
                    # Payer bekommt alle negativen Shares der Begünstigten; ist selbst evtl. auch Begünstigter
                    if p in bens:
                        val = amt - share  # bezahlt und konsumiert Anteil
                    else:
                        val = amt  # bezahlt für andere, bekommt alles zurück
                elif p in bens:
                    val = -share
                # Summen tracken
                totals[p] += val
                row_dict[p] = val
            alloc_rows.append(row_dict)
        # Totals row
        total_row = {"Ausgabe": "Gesamt"}
        for p in players:
            total_row[p] = totals[p]
        alloc_rows.append(total_row)
        alloc_df = pd.DataFrame(alloc_rows)
        # Anzeige DataFrame mit Formatierung (leer für 0)
        display_df = alloc_df.copy()
        for p in [c for c in display_df.columns if c != "Ausgabe"]:
            display_df[p] = display_df[p].apply(lambda x: ("" if abs(x) < 1e-9 else f"{x:.2f}"))
        def style_neg(val):
            try:
                fv = float(val.replace(",","."))
            except Exception:
                return ""
            if fv < 0:
                return "color:red;"
            return ""  # keine Farbe für positive Werte
        FONT_SIZE_PX = 30  # doppelte Schriftgröße
        styler = (
            display_df.style
            .applymap(style_neg, subset=[c for c in display_df.columns if c != "Ausgabe"])  # type: ignore
            .set_table_styles([
                {"selector": "th", "props": [("font-size", f"{FONT_SIZE_PX}px")]},
                {"selector": "td", "props": [("font-size", f"{FONT_SIZE_PX}px")]},
            ])
        )
        st.dataframe(styler, width='stretch')

    st.markdown("---")
    st.markdown("**Gespeicherte Ausgaben**")
    expenses = _load_expenses()  # reload after possible save
    if not expenses:
        st.info("Noch keine Ausgaben gespeichert.")
        return

    # Bearbeitungsstatus aus Session State
    if "ab_edit_id" not in st.session_state:
        st.session_state.ab_edit_id = None

    # DataFrame bauen
    table_rows = []
    for e in expenses:
        table_rows.append({
            "Datum": e.get("timestamp",""),
            "Bezahlt von": e.get("payer",""),
            "Betrag": e.get("amount",0),
            "Beschreibung": e.get("description",""),
            "Profitierer": ", ".join(e.get("beneficiaries", [])),
            "ID": e.get("id",""),
        })
    df = pd.DataFrame(table_rows)
    st.dataframe(df.drop(columns=["ID"]), width='stretch')

    st.markdown("**Einträge bearbeiten / löschen**")
    for e in expenses:
        with st.expander(f"{e.get('timestamp','')} | {e.get('payer','')} -> {e.get('amount',0)} €"):
            cols_btn = st.columns(3)
            if cols_btn[0].button("Bearbeiten", key=f"edit_{e['id']}"):
                st.session_state.ab_edit_id = e["id"]
            if cols_btn[1].button("Löschen", key=f"del_{e['id']}"):
                new_list = [x for x in expenses if x["id"] != e["id"]]
                _save_expenses(new_list)
                st.success("Eintrag gelöscht.")
                try:
                    st.rerun()
                except Exception:
                    pass
            if st.session_state.ab_edit_id == e["id"]:
                st.markdown("***Bearbeitung***")
                # Vorbelegung
                edit_payer = st.selectbox("Bezahlt von (Edit)", _load_players(), index=_load_players().index(e.get("payer","")) if e.get("payer") in _load_players() else 0, key=f"edit_payer_{e['id']}")
                edit_amount = st.text_input("Betrag (Edit)", value=str(e.get("amount","")), key=f"edit_amount_{e['id']}")
                edit_descr = st.text_input("Beschreibung (Edit)", value=e.get("description",""), key=f"edit_descr_{e['id']}")
                st.markdown("Profitierer (Edit):")
                ben_flags = {}
                ben_cols = st.columns(min(6, max(1, len(players))))
                current_bens = set(e.get("beneficiaries", []))
                for i, p in enumerate(players):
                    ben_flags[p] = ben_cols[i % len(ben_cols)].checkbox(p, value=(p in current_bens), key=f"edit_ben_{e['id']}_{p}")
                save_edit = st.button("Änderungen speichern", key=f"save_edit_{e['id']}")
                cancel_edit = st.button("Abbrechen", key=f"cancel_edit_{e['id']}")
                if save_edit:
                    try:
                        amt_clean = edit_amount.replace(",", ".").strip()
                        amt_val = float(amt_clean)
                    except Exception:
                        st.error("Ungültiger Betrag.")
                    else:
                        new_bens = [p for p, fl in ben_flags.items() if fl]
                        if not new_bens:
                            st.error("Mindestens ein Profitierer auswählen.")
                        else:
                            # Update
                            for idx, orig in enumerate(expenses):
                                if orig["id"] == e["id"]:
                                    expenses[idx]["payer"] = edit_payer
                                    expenses[idx]["amount"] = amt_val
                                    expenses[idx]["description"] = edit_descr.strip()
                                    expenses[idx]["beneficiaries"] = new_bens
                                    break
                            _save_expenses(expenses)
                            st.success("Eintrag aktualisiert.")
                            st.session_state.ab_edit_id = None
                            try:
                                st.rerun()
                            except Exception:
                                pass
                if cancel_edit:
                    st.session_state.ab_edit_id = None
                    try:
                        st.rerun()
                    except Exception:
                        pass

if __name__ == "__main__":
    import streamlit as st
    render(st)
