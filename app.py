import streamlit as st
import importlib
import importlib.util
from pathlib import Path

st.set_page_config(page_title="Gruppo App", page_icon="⛳", layout="wide", menu_items={})

# Hide the 'app' entry in the built-in navigation where possible
st.markdown(
    """
    <style>
      a[data-testid="stSidebarNavLink"][href*="?page=app"] { display: none !important; }
      a[data-testid^="stPageLink"][href*="?page=app"] { display: none !important; }
    </style>
    <script>
    (function(){
      function hideAppLinks(root){
        try {
          const query = 'a[data-testid="stSidebarNavLink"], a[data-testid^="stPageLink"]';
          root.querySelectorAll(query).forEach(a => {
            const href = a.getAttribute('href') || '';
            const txt = (a.innerText || '').trim().toLowerCase();
            if (href.includes('?page=app') || txt === 'app') {
              const li = a.closest('li') || a;
              li.style.display = 'none';
            }
          });
        } catch(e) {}
      }
      const root = window.parent?.document || document;
      hideAppLinks(root);
      const obs = new MutationObserver(() => hideAppLinks(root));
      obs.observe(root, { subtree: true, childList: true });
      setTimeout(() => hideAppLinks(root), 600);
    })();
    </script>
    """,
    unsafe_allow_html=True,
)

# Fallback: if 'app' still appears/clicked, show Stats content here
try:
    stats_module = importlib.import_module("pages.stats")
except ModuleNotFoundError:
    # Try to load numbered stats page by path (e.g., pages/1_stats.py)
    stats_path = Path(__file__).parent / "pages" / "1_stats.py"
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
    st.error("Seite 'Stats' hat keine gültige render(st)-Funktion.")
