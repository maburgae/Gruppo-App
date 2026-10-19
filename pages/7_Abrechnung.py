import json
import os
import base64
import io
import sys
import requests
from datetime import datetime
import pandas as pd
import uuid  # hinzugefügt für eindeutige IDs

EXPENSE_FILE = "json/abrechnung.json"
SETTINGS_FILE = "json/abrechnung_settings.json"

DEFAULT_PLAYERS = ["Marc","Andy","Bernie","Jens","Markus","Buffy"]

STYLE_CSS = """
<style>
[data-testid='stAppViewContainer'] [data-testid='stMain'] p,
[data-testid='stAppViewContainer'] [data-testid='stMain'] span,
[data-testid='stAppViewContainer'] [data-testid='stMain'] div,
[data-testid='stAppViewContainer'] [data-testid='stMain'] label,
[data-testid='stAppViewContainer'] [data-testid='stMain'] .stButton > button,
[data-testid='stAppViewContainer'] [data-testid='stMain'] .stTextInput label,
[data-testid='stAppViewContainer'] [data-testid='stMain'] .stSelectbox label,
[data-testid='stAppViewContainer'] [data-testid='stMain'] .stCheckbox label {font-size:15px !important;}
.stButton > button {background:#0b5ed7; color:#fff; border:1px solid #084298;}
.stButton > button:hover {background:#0a53be; border-color:#06357a;}

@media (max-width: 900px) {
    /* Keep checkbox rows in 3 columns on mobile instead of collapsing to 1 column. */
    [data-testid='stHorizontalBlock']:has([data-testid='stCheckbox']) {
        display: grid !important;
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        gap: 0.2rem 0.6rem !important;
        align-items: start !important;
    }

    [data-testid='stHorizontalBlock']:has([data-testid='stCheckbox']) > [data-testid='column'] {
        min-width: 0 !important;
        width: 100% !important;
        flex: 0 0 auto !important;
    }

    [data-testid='stHorizontalBlock']:has([data-testid='stCheckbox']) [data-testid='stCheckbox'] label {
        white-space: nowrap;
    }
}
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


def _load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_settings(settings: dict):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def _load_spende_player():
    settings = _load_settings()
    val = settings.get("spende_player")
    return val if isinstance(val, str) else None


def _save_spende_player(player: str):
    settings = _load_settings()
    settings["spende_player"] = player
    _save_settings(settings)


def _safe_secrets(st):
    try:
        return st.secrets
    except Exception:
        return {}


def _push_file_to_github_api(st, file_path: str, commit_prefix: str):
    """Push one local JSON file via GitHub Contents API."""
    token = _safe_secrets(st).get("GITHUB_TOKEN")
    repo = _safe_secrets(st).get("REPO") or "USER/REPO"
    branch = _safe_secrets(st).get("BRANCH") or "main"

    if not token or repo == "USER/REPO":
        return False, "GitHub Secrets fehlen (GITHUB_TOKEN / REPO)."
    if not os.path.exists(file_path):
        return False, f"Datei fehlt: {file_path}"

    try:
        with open(file_path, "rb") as f:
            local_bytes = f.read()
        local_b64 = base64.b64encode(local_bytes).decode()

        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
        api_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"

        sha = None
        r_get = requests.get(api_url, params={"ref": branch}, headers=headers)
        if r_get.status_code == 200:
            sha = r_get.json().get("sha")
        elif r_get.status_code != 404:
            return False, f"GitHub GET Fehler {r_get.status_code}: {r_get.text[:160]}"

        commit_msg = f"{commit_prefix} {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        payload = {"message": commit_msg, "content": local_b64, "branch": branch}
        if sha:
            payload["sha"] = sha

        r_put = requests.put(api_url, headers=headers, json=payload)
        if r_put.status_code in (200, 201):
            return True, f"GitHub Push fuer {file_path} erfolgreich."
        return False, f"GitHub PUT Fehler {r_put.status_code}: {r_put.text[:200]}"
    except Exception as e:
        return False, f"GitHub Push Ausnahme: {e}"


def _push_abrechnung_to_github_api(st):
    """Push json/abrechnung.json via GitHub Contents API."""
    return _push_file_to_github_api(st, EXPENSE_FILE, "Update abrechnung.json")


def _push_abrechnung_settings_to_github_api(st):
    """Push json/abrechnung_settings.json via GitHub Contents API."""
    return _push_file_to_github_api(st, SETTINGS_FILE, "Update abrechnung_settings.json")


def _load_bank_details():
    bank_file = "json/Bank.json"
    if not os.path.exists(bank_file):
        return {}
    try:
        with open(bank_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _normalize_iban(iban: str):
    if not isinstance(iban, str):
        return ""
    return "".join(ch for ch in iban.upper() if ch.isalnum())


def _epc_text(value: str, max_len: int):
    # EPC character set mapping/sanitizing.
    text = str(value or "")
    repl = {
        "Ä": "AE", "Ö": "OE", "Ü": "UE", "ß": "SS",
        "ä": "ae", "ö": "oe", "ü": "ue",
    }
    for src, dst in repl.items():
        text = text.replace(src, dst)
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789/*-?:().,'+ "
    cleaned = "".join(ch for ch in text if ch in allowed)
    return cleaned[:max_len]


def _build_epc_payload(recipient_name: str, iban: str, amount: float, remittance: str, bic: str = "", purpose: str = ""):
    # EPC069-12 (SCT) payload, line based.
    norm_iban = _normalize_iban(iban)
    if len(norm_iban) < 15 or len(norm_iban) > 34 or not norm_iban.isalnum():
        raise ValueError("Ungültige IBAN für EPC QR.")

    amount_val = round(float(amount), 2)
    if amount_val <= 0:
        raise ValueError("Betrag muss größer als 0 sein.")

    bic_norm = _epc_text((bic or "").upper(), 11)
    if bic_norm and len(bic_norm) not in (8, 11):
        raise ValueError("Ungültiger BIC (8 oder 11 Zeichen).")

    name_norm = _epc_text(recipient_name, 70)
    if not name_norm:
        raise ValueError("Empfängername fehlt für EPC QR.")

    purpose_norm = _epc_text(purpose, 4)
    remittance_norm = _epc_text(remittance, 140)

    lines = [
        "BCD",                 # Service Tag
        "002",                 # Version
        "1",                   # Character set: UTF-8
        "SCT",                 # SEPA Credit Transfer
        bic_norm,               # BIC (optional)
        name_norm,              # Name
        norm_iban,              # IBAN
        f"EUR{amount_val:.2f}",
        purpose_norm,           # Purpose code (optional)
        remittance_norm,        # Unstructured remittance
        "",                    # Structured remittance (optional)
        "",                    # Information (optional)
    ]
    payload = "\n".join(lines)
    return payload, {
        "name": name_norm,
        "iban": norm_iban,
        "bic": bic_norm,
        "amount": amount_val,
        "purpose": purpose_norm,
        "betreff": remittance_norm,
    }


def _build_qr_png_bytes(payload: str):
    try:
        import importlib
        qrcode = importlib.import_module("qrcode")
    except ModuleNotFoundError as e:
        raise RuntimeError(
            f"QR-Code Paket fehlt im aktiven Interpreter ({sys.executable}). Bitte dort 'qrcode[pil]' installieren."
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"QR-Code Importfehler im Interpreter {sys.executable}: {e}"
        ) from e

    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        raise RuntimeError(
            "QR-Code konnte nicht erzeugt werden. Bitte qrcode[pil] im aktiven Interpreter installieren. "
            f"Interpreter: {sys.executable}. Fehler: {e}"
        ) from e


def _build_settlement_transfers(saldos: dict):
    """Erzeuge Ueberweisungen: groesstes Minus zahlt an groesstes Plus, dann weiter."""
    debtors = []
    creditors = []

    # In Cent rechnen, damit Rundungsfehler bei Floats keine Restbetraege erzeugen.
    for player, balance in saldos.items():
        cents = int(round(float(balance) * 100))
        if cents < 0:
            debtors.append([player, -cents])
        elif cents > 0:
            creditors.append([player, cents])

    # Groesstes Minus zuerst, groesstes Plus zuerst.
    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)

    transfers = []
    i = 0
    j = 0
    while i < len(debtors) and j < len(creditors):
        debtor_name, debtor_open = debtors[i]
        creditor_name, creditor_open = creditors[j]
        pay = min(debtor_open, creditor_open)

        if pay > 0:
            transfers.append({
                "von": debtor_name,
                "an": creditor_name,
                "betrag": pay / 100.0,
            })

        debtors[i][1] -= pay
        creditors[j][1] -= pay

        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1

    return transfers


def render(st):
    st.markdown(STYLE_CSS, unsafe_allow_html=True)
    st.markdown("### Abrechnung")

    players = _load_players()
    expenses = _load_expenses()
    saved_spende_player = _load_spende_player()
    donation_player = st.session_state.get("abrechnung_spende_player")
    if donation_player not in players:
        donation_player = saved_spende_player
    if donation_player not in players and players:
        donation_player = players[0]
    if donation_player:
        st.session_state["abrechnung_spende_player"] = donation_player
    if "abrechnung_spende_player_prev" not in st.session_state:
        st.session_state["abrechnung_spende_player_prev"] = donation_player

    # ---------------- Allocation (Ausgaben) Table moved to top ----------------
    if expenses:
        st.markdown("**Ausgaben**")
        alloc_rows = []
        outlay_totals = {p: 0.0 for p in players}
        umlage_totals = {p: 0.0 for p in players}
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
            if payer_name in outlay_totals:
                outlay_totals[payer_name] += amt
            for b in bens:
                umlage_totals[b] += share
            row_label = f"{payer_name} {":"} {e.get('description','').strip()} ({amt:.2f})".strip()
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
        geld_row = {"Ausgabe": "Monetenkuchen"}
        for p in players:
            neg_val = -yearly_geld[p]
            geld_row[p] = neg_val if abs(neg_val) > 1e-9 else 0.0
            umlage_totals[p] += yearly_geld[p]
        alloc_rows.append(geld_row)
        monetenkuchen_total = sum(yearly_geld.values())
        spende_row = {"Ausgabe": "Spende"}
        spende_totals = {p: 0.0 for p in players}
        for p in players:
            spende_row[p] = 0.0
        if donation_player in players:
            spende_row[donation_player] = monetenkuchen_total
            spende_totals[donation_player] = monetenkuchen_total
        alloc_rows.append(spende_row)

        outlay_row = {"Ausgabe": "Auslage"}
        for p in players:
            outlay_row[p] = outlay_totals[p]
        alloc_rows.append(outlay_row)

        kosten_row = {"Ausgabe": "Kosten"}
        for p in players:
            kosten_row[p] = -umlage_totals[p]
        alloc_rows.append(kosten_row)

        total_row = {"Ausgabe": "Saldo"}
        for p in players:
            total_row[p] = kosten_row[p] + outlay_totals[p] + spende_totals[p]
        alloc_rows.append(total_row)
        saldo_totals = {p: total_row[p] for p in players}
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
        summary_rows = {"Monetenkuchen", "Spende", "Auslage", "Kosten", "Saldo"}
        body_rows = []
        for _, row in display_df.iterrows():
            row_name = str(row.get("Ausgabe", "")).strip()
            is_summary = row_name in summary_rows
            row_bg = "background:#e2e8f0;" if is_summary else ""
            border_top = "border-top:2px solid #94a3b8;" if is_summary else ""
            row_text = "color:#111827;" if is_summary else "color:inherit;"
            row_weight = "font-weight:600;" if is_summary else ""
            if row_name == "Monetenkuchen":
                border_top = "border-top:3px solid #64748b;"
            cells = []
            for col in display_df.columns:
                if col == 'Ausgabe':
                    cells.append(
                        f"<td style='padding:4px;white-space:nowrap;font-size:{FONT_SIZE_PX}px;"
                        f"border-bottom:1px solid #e5e7eb;{row_bg}{border_top}{row_text}{row_weight}'>{row[col]}</td>"
                    )
                else:
                    cells.append(
                        f"<td style='text-align:right;padding:4px;font-size:{FONT_SIZE_PX}px;"
                        f"border-bottom:1px solid #e5e7eb;{row_bg}{border_top}{row_text}{row_weight}'>{_cell_html(row[col])}</td>"
                    )
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
        if players:
            selected_spende_player = st.selectbox(
                "Wer spendet?",
                players,
                index=players.index(donation_player) if donation_player in players else 0,
                key="abrechnung_spende_player",
            )
            prev_spende_player = st.session_state.get("abrechnung_spende_player_prev")
            if selected_spende_player != prev_spende_player:
                _save_spende_player(selected_spende_player)
                ok_push, msg_push = _push_abrechnung_settings_to_github_api(st)
                if ok_push:
                    st.success(msg_push)
                else:
                    st.warning(msg_push)
                st.session_state["abrechnung_spende_player_prev"] = selected_spende_player

        st.markdown("**Konten ausgleichen**")
        transfers = _build_settlement_transfers(saldo_totals)
        bank_details = _load_bank_details()
        if transfers:
            selected_idx = None
            for idx, t in enumerate(transfers):
                try:
                    with st.container(border=True):
                        st.markdown(
                            (
                                "<p style='color:#b91c1c;margin:0;'>"
                                f"<strong><u>{t['von']}</u></strong> überweist {t['betrag']:.2f} EUR an "
                                f"<strong><u>{t['an']}</u></strong>"
                                "</p>"
                            ),
                            unsafe_allow_html=True,
                        )
                        btn_col, _spacer_col = st.columns([2, 18], gap="small")
                        if btn_col.button("QR-Code", key=f"ab_qr_btn_{idx}"):
                            selected_idx = idx
                except TypeError:
                    st.markdown(
                        (
                            "<p style='color:#b91c1c;margin:0;'>"
                            f"<strong><u>{t['von']}</u></strong> überweist {t['betrag']:.2f} EUR an "
                            f"<strong><u>{t['an']}</u></strong>"
                            "</p>"
                        ),
                        unsafe_allow_html=True,
                    )
                    btn_col, _spacer_col = st.columns([2, 18], gap="small")
                    if btn_col.button("QR-Code", key=f"ab_qr_btn_{idx}"):
                        selected_idx = idx
                    st.markdown("---")

            if selected_idx is not None and 0 <= selected_idx < len(transfers):
                t = transfers[selected_idx]
                rec_key = t["an"]
                rec_bank = bank_details.get(rec_key, {}) if isinstance(bank_details, dict) else {}
                rec_iban = rec_bank.get("IBAN", "")
                rec_name = rec_bank.get("Name", rec_key)
                rec_bic = rec_bank.get("BIC", "")

                err_msg = None
                qr_png = None
                epc_meta = {}
                try:
                    epc_payload, epc_meta = _build_epc_payload(
                        recipient_name=rec_name,
                        iban=rec_iban,
                        amount=t["betrag"],
                        remittance="Grupporeise",
                        bic=rec_bic,
                        purpose="",
                    )
                    qr_png = _build_qr_png_bytes(epc_payload)
                except Exception as e:
                    err_msg = str(e)

                def _render_qr_popup_content():
                    st.markdown("### EPC QR Überweisung")
                    st.write(f"Von: {t['von']}")
                    st.write(f"An: {t['an']}")
                    if err_msg:
                        st.error(err_msg)
                        if not rec_bank:
                            st.info("In json/Bank.json fehlen die Bankdaten für den Empfänger.")
                    else:
                        st.image(qr_png, caption="SEPA EPC QR")
                        st.write(f"Betrag: EUR {epc_meta['amount']:.2f}")
                        st.write(f"Betreff: {epc_meta['betreff']}")
                        st.write(f"Empfänger: {epc_meta['name']}")
                        st.write(f"IBAN: {epc_meta['iban']}")

                if hasattr(st, "dialog"):
                    @st.dialog("Überweisung QR")
                    def _show_qr_dialog():
                        _render_qr_popup_content()
                    _show_qr_dialog()
                else:
                    with st.expander("Überweisung QR", expanded=True):
                        _render_qr_popup_content()
        else:
            st.info("Alle Konten sind bereits ausgeglichen.")
    else:
        st.info("Noch keine Ausgaben vorhanden.")

    st.markdown("---")

    # ---------------- Formular (Neue Ausgabe) now after table ----------------
    st.markdown("**Neue Ausgabe hinzufügen**")
    payer = st.selectbox("Bezahlt von", players, key="abrechnung_payer")
    st.markdown("Betroffene / Profitierer:")
    beneficiary_flags = {}
    for row_start in range(0, len(players), 3):
        row_players = players[row_start:row_start + 3]
        cols = st.columns(3)
        for i in range(3):
            if i < len(row_players):
                p = row_players[i]
                beneficiary_flags[p] = cols[i].checkbox(p, value=True, key=f"ab_ben_{p}")
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
        ok_push, msg_push = _push_abrechnung_to_github_api(st)
        if ok_push:
            st.success(msg_push)
        else:
            st.warning(msg_push)
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
                ok_push, msg_push = _push_abrechnung_to_github_api(st)
                if ok_push:
                    st.success(msg_push)
                else:
                    st.warning(msg_push)
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
                current_bens = set(e.get("beneficiaries", []))
                for row_start in range(0, len(players), 3):
                    row_players = players[row_start:row_start + 3]
                    ben_cols = st.columns(3)
                    for i in range(3):
                        if i < len(row_players):
                            p = row_players[i]
                            ben_flags[p] = ben_cols[i].checkbox(
                                p,
                                value=(p in current_bens),
                                key=f"edit_ben_{e['id']}_{p}",
                            )
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
                            ok_push, msg_push = _push_abrechnung_to_github_api(st)
                            if ok_push:
                                st.success(msg_push)
                            else:
                                st.warning(msg_push)
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
