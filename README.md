# Streamlit Golf App (Smartphone-optimiert)

## Start
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Struktur
- `app.py` – Hauptdatei mit Top-Menü (Runden, Stats, 2025, Konf)
- `pages/` – vier Seiten, jede mit `render(st)`:
  - `runden.py`
  - `stats.py`
  - `y2025.py`
  - `konf.py`
- `actions/` – je **ein** Datei pro Button auf der **Konf**-Seite, **ohne** Streamlit-Code, jeweils mit `main(...)`:
  - `neue_runde.py`
  - `upload_scorecard.py`
  - `berechne_den_tag.py`
  - `tag_to_alle_runden.py`
  - `erzeuge_stats.py`
- `assets/placeholder_*.png` – Platzhalterbilder
