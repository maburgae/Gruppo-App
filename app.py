import streamlit as st
import importlib

st.set_page_config(page_title="Gruppo App", page_icon="⛳", layout="wide", menu_items={})

# --- Menü als Buttons oben (smartphonefreundlich) ---
MENU_PAGES = ["Runden", "Stats", "2025", "Konf"]
MENU_MODULES = {
    "Runden": "pages.runden",
    "Stats": "pages.stats",
    "2025": "pages.y2025",
    "Konf": "pages.konf",
}

col1, col2, col3, col4 = st.columns(4)
menu_clicked = None
with col1:
    if st.button("Runden"):
        menu_clicked = "Runden"
with col2:
    if st.button("Stats"):
        menu_clicked = "Stats"
with col3:
    if st.button("2025"):
        menu_clicked = "2025"
with col4:
    if st.button("Konf"):
        menu_clicked = "Konf"

if menu_clicked:
    st.session_state["menu"] = menu_clicked
elif "menu" not in st.session_state:
    st.session_state["menu"] = "Runden"

menu = st.session_state["menu"]

# --- Load and render the active page ---
module_path = MENU_MODULES.get(menu, "pages.runden")
page_module = importlib.import_module(module_path)

# Each page exposes a render(st) function
if hasattr(page_module, "render") and callable(page_module.render):
    page_module.render(st)
else:
    st.error(f"Seite '{menu}' hat keine gültige render(st)-Funktion.")
