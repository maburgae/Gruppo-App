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

    # ---------------- Allocation (Ausgaben) Table moved to top ----------------
    if expenses:
        st.markdown("**Ausgaben**")
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
                    if p in bens:
                        val = amt - share  # bezahlt & konsumiert
                    else:
                        val = amt
                elif p in bens:
                    val = -share
                totals[p] += val
                row_dict[p] = val
            alloc_rows.append(row_dict)
        from datetime import datetime as _dt
        current_year = _dt.now().year
        yearly_geld = {p: 0.0 for p in players}
        try:
            with open("json/allrounds.json", "r", encoding="utf-8") as _f_all:
                _all = json.load(_f_all)
            if isinstance(_all, dict):
                for date_key, round_obj in _all.items():
                    try:
                        parts = str(date_key).split('.')
                        year_part = int(parts[-1]) if len(parts) == 3 else None
                    except Exception:
                        year_part = None
                    if year_part != current_year:
                        continue
                    sp_map = round_obj.get("Spieler", {}) or {}
                    for pname, pdata in sp_map.items():
                        if pname in yearly_geld:
                            gval = pdata.get("Geld")
                            if isinstance(gval, (int, float)) and not isinstance(gval, bool):
                                yearly_geld[pname] += float(gval)
                            elif gval not in (None, ""):
                                try:
                                    yearly_geld[pname] += float(str(gval).replace(',', '.'))
                                except Exception:
                                    pass
        except Exception:
            pass
        if any(abs(v) > 1e-9 for v in yearly_geld.values()):
            geld_row = {"Ausgabe": f"Monetenkuchen {current_year}"}
            for p in players:
                neg_val = -yearly_geld[p]
                geld_row[p] = neg_val if abs(neg_val) > 1e-9 else 0.0
                totals[p] += geld_row[p]
            alloc_rows.append(geld_row)
        total_row = {"Ausgabe": "Gesamt"}
        for p in players:
            total_row[p] = totals[p]
        alloc_rows.append(total_row)
        import pandas as _pd
        alloc_df = _pd.DataFrame(alloc_rows)
        display_df = alloc_df.copy()
        for p in [c for c in display_df.columns if c != "Ausgabe"]:
            display_df[p] = display_df[p].apply(lambda x: ("" if abs(x) < 1e-9 else f"{x:.2f}"))
        # Build HTML table to avoid internal scroll (static rendering)
        FONT_SIZE_PX = 15
        def _cell_html(val):
            if val == "":
                return ""
            try:
                fv = float(str(val).replace(',', '.'))
            except Exception:
                # Nicht-numerisch trotzdem mit Font-Size ausgeben
                return f"<span style='font-size:{FONT_SIZE_PX}px;'>{val}</span>"
            if fv < 0:
                return f"<span style='color:red;font-size:{FONT_SIZE_PX}px;'>{val}</span>"
            return f"<span style='font-size:{FONT_SIZE_PX}px;'>{val}</span>"
        # Einheitliche Schriftgröße in gesamter Tabelle über table-level CSS
        header_html = ''.join([f"<th style='padding:4px;font-size:{FONT_SIZE_PX}px;'>{col}</th>" for col in display_df.columns])
        body_rows = []
        for _, row in display_df.iterrows():
            cells = []
            for col in display_df.columns:
                if col == 'Ausgabe':
                    cells.append(f"<td style='padding:4px;white-space:nowrap;font-size:{FONT_SIZE_PX}px;'>{row[col]}</td>")
                else:
                    cells.append(f"<td style='text-align:right;padding:4px;font-size:{FONT_SIZE_PX}px;'>{_cell_html(row[col])}</td>")
            body_rows.append('<tr>' + ''.join(cells) + '</tr>')
        table_html = f"""
        <div style='overflow-x:auto;'>
        <table style='border-collapse:collapse;width:100%;font-size:{FONT_SIZE_PX}px;'>
            <thead><tr>{header_html}</tr></thead>
            <tbody>
                {''.join(body_rows)}
            </tbody>
        </table>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("Noch keine Ausgaben vorhanden.")

    st.markdown("---")

    # ---------------- Formular (Neue Ausgabe) now after table ----------------
    st.markdown("**Neue Ausgabe hinzufügen**")
    payer = st.selectbox("Bezahlt von", players, key="abrechnung_payer")
    st.markdown("Betroffene / Profitierer:")
    beneficiary_flags = {}
    cols = st.columns(min(6, max(1, len(players))))
    for i, p in enumerate(players):
        beneficiary_flags[p] = cols[i % len(cols)].checkbox(p, value=True, key=f"ab_ben_{p}")
    amount_str = st.text_input("Betrag", value="", key="ab_betrag", help="Numerischer Betrag (Komma oder Punkt)")
    descr = st.text_input("Beschreibung", value="", key="ab_descr")
    add_clicked = st.button("Ausgabe speichern")
    if add_clicked:
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
        try:
            st.rerun()
        except Exception:
            pass

    # ---------------- Edit/Delete (keine gesonderte Tabelle mehr) ----------------
    if not expenses:
        return
    st.markdown("---")
    st.markdown("**Einträge bearbeiten / löschen**")
    # Bearbeitungsstatus aus Session State
    if "ab_edit_id" not in st.session_state:
        st.session_state.ab_edit_id = None
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
                edit_payer = st.selectbox(
                    "Bezahlt von (Edit)",
                    _load_players(),
                    index=_load_players().index(e.get("payer","")) if e.get("payer") in _load_players() else 0,
                    key=f"edit_payer_{e['id']}"
                )
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
