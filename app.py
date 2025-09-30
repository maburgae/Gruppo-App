import streamlit as st
import importlib

st.set_page_config(page_title="Gruppo App", page_icon="⛳", layout="wide")

# --- Menü als Buttons oben (smartphonefreundlich) ---
MENU_PAGES = ["Runden", "Stats", "2025", "Konf"]
MENU_MODULES = {
    "Runden": "pages.runden",
    "Stats": "pages.stats",
    "2025": "pages.y2025",
    "Konf": "pages.konf",
}

col1, col2, col3, col4 = st.columns(4)
with col1:
    btn_runden = st.button("Runden")
with col2:
    btn_stats = st.button("Stats")
with col3:
    btn_2025 = st.button("2025")
with col4:
    btn_konf = st.button("Konf")

if "menu" not in st.session_state:
    st.session_state["menu"] = "Runden"

if btn_runden:
    st.session_state["menu"] = "Runden"
if btn_stats:
    st.session_state["menu"] = "Stats"
if btn_2025:
    st.session_state["menu"] = "2025"
if btn_konf:
    st.session_state["menu"] = "Konf"

menu = st.session_state["menu"]

# --- Load and render the active page ---
module_path = MENU_MODULES.get(menu, "pages.runden")
page_module = importlib.import_module(module_path)

# Each page exposes a render(st) function
if hasattr(page_module, "render") and callable(page_module.render):
    page_module.render(st)
else:
    st.error(f"Seite '{menu}' hat keine gültige render(st)-Funktion.")
