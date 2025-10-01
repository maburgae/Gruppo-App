import streamlit as st
import importlib
import importlib.util
from pathlib import Path

st.set_page_config(page_title="Gruppo App", page_icon="⛳", layout="wide", menu_items={})

# Prefer redirecting to the built-in multipage 'Alltime Stats' page to avoid duplication
try:
    # Streamlit 1.22+ provides switch_page
    st.switch_page("pages/1_Alltime_Stats.py")
except Exception:
    # Fallback: render Stats content on the main 'app' page
    try:
        # load by path (renamed file)
        stats_path = Path(__file__).parent / "pages" / "1_Alltime_Stats.py"
        if stats_path.exists():
            spec = importlib.util.spec_from_file_location("stats_page", str(stats_path))
            stats_module = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(stats_module)
        else:
            stats_module = None
    except Exception:
        stats_module = None

    if stats_module and hasattr(stats_module, "render") and callable(stats_module.render):
        stats_module.render(st)
    else:
        st.error("Seite 'Alltime Stats' hat keine gültige render(st)-Funktion.")
