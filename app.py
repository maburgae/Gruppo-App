import streamlit as st

st.set_page_config(page_title="Alltime Stats", page_icon="⛳", layout="wide", menu_items={})

# Keep sidebar menu typography stable across pages.
st.markdown(
    """
    <style>
    [data-testid='stSidebarNav'] * {
        font-size: 15px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def _mk_page(path: str, title: str, url_path: str, default: bool = False):
    try:
        return st.Page(path, title=title, url_path=url_path, default=default)
    except TypeError:
        # Fallback for Streamlit variants without url_path/default params.
        return st.Page(path, title=title)


navigation = st.navigation([
    _mk_page("alltime_stats_page.py", "Alltime Stats", "Alltime_Stats", default=True),
    _mk_page("pages/2_Runden.py", "Runden", "Runden"),
    _mk_page("pages/3_Urlaub.py", "Urlaub", "Urlaub"),
    _mk_page("pages/7_Abrechnung.py", "Abrechnung", "Abrechnung"),
    _mk_page("pages/8_Konfig.py", "Konfig", "Konfig"),
])

navigation.run()
