# show_scorecard.py
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def load_round(json_file: str, date_key: str):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    if date_key not in data:
        raise ValueError(f"Date {date_key} not found in {json_file}. Available: {list(data.keys())}")
    return data[date_key]


def show_scorecard(json_file: str, date_key: str, save_path=None, show=True):
    rd = load_round(json_file, date_key)

    pars = rd.get("Par", [])
    hcps = rd.get("Hcp", [])
    players = rd.get("Spieler", {})
    
    if pars is None:
        print(f"No scorecard:{date_key}")
        return 0

    holes = list(range(1, 19))

    # build table data
    row_labels = ["Hole", "Par", "Hcp"]
    rows = []
    rows.append([str(h) for h in holes])          # Hole numbers
    rows.append([str(p) if p is not None else "" for p in pars])  # Par
    rows.append([str(h) if h is not None else "" for h in hcps])  # Hcp

    # Separator row after Hcp for visual separation (blank label handled later)
    rows.append(["" for _ in range(18)])
    row_labels.append("")

    # Helper to decide if player has any score
    def _has_score(pdata):
        sc = pdata.get("Score", []) or []
        if not sc:
            return False
        for v in sc:
            if isinstance(v, (int, float)):
                return True
        return False

    # Build player rows (Score + Netto) and insert separator rows
    for pname, pdata in players.items():
        if not _has_score(pdata):
            continue  # skip players without any score values
        # Scores row
        score_list = list(pdata.get("Score", []) or [])
        score_list = score_list + [None] * (18 - len(score_list))
        scores = [ ("x" if sc is None else str(sc)) for sc in score_list ]
        rows.append(scores)
        row_labels.append(pname if pdata.get("DayHcp", "") == "" else f"{pname} ({pdata['DayHcp']})")
        # Netto row (label only 'Netto')
        np_list = list(pdata.get("NettoP", []) or [])
        np_list = np_list + [None] * (18 - len(np_list))
        nettopoints = [ ("" if np is None else str(np)) for np in np_list ]
        rows.append(nettopoints)
        row_labels.append("Netto")
        # Separator row (blank) for visual spacing
        rows.append(["" for _ in range(18)])
        row_labels.append("")  # marker for separator

    # Ensure all rows are exactly 18 columns
    for i in range(len(rows)):
        if len(rows[i]) > 18:
            rows[i] = rows[i][:18]
        elif len(rows[i]) < 18:
            rows[i] += [""] * (18 - len(rows[i]))

    col_labels = [""] + [str(h) for h in holes]
    cell_data = [[label] + row for label, row in zip(row_labels, rows)]

    # Helper to render a half (start inclusive, end exclusive) of the scorecard with extra Net column
    def render_half(start_idx: int, end_idx: int, out_path: str | None, date_key: str):
        hole_count = end_idx - start_idx  # 9
        # Build sliced data + additional Net column (sum of Netto row for that half)
        cell_data_half = []
        for label, full_row in zip(row_labels, rows):
            slice_part = full_row[start_idx:end_idx]
            # Determine extra cell content
            extra = ""
            if label == "Netto":
                # Sum numeric entries in slice_part
                s = 0
                for v in slice_part:
                    try:
                        if v != "":
                            s += int(v)
                    except Exception:
                        pass
                extra = str(s)
            cell_data_half.append([label] + slice_part + [extra])

        # Figure with +1 extra column
        fig, ax = plt.subplots(figsize=(20, 15))
        ax.axis("off")
        try:
            fig.tight_layout(pad=0)
        except Exception:
            pass
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        ax.set_position([0, 0, 1, 1])

        table = ax.table(cellText=cell_data_half, cellLoc="center", loc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(40)
        table.scale(1.0, 4.5)

        # Reduce padding
        for cell in table.get_celld().values():
            try:
                cell.set_pad(0.01)
            except Exception:
                pass

        # Adjust first column width
        n_rows_local = len(cell_data_half)
        n_cols_local = hole_count + 2  # label + holes + Net column
        for key, cell in table.get_celld().items():
            r, c = key
            if c == 0:
                cell.set_width(0.20)

        # Bold Par row (row index 1, after headers row 0=Hole labels). Our first three labels are Hole/Par/Hcp.
        # Par row is index 1 in cell_data_half
        for col_idx in range(1, hole_count + 1):
            try:
                table[(1, col_idx)].set_text_props(weight='bold')
            except Exception:
                pass

        # Coloring holes (exclude last Net column)
        for row_idx, label in enumerate(row_labels):
            if row_idx >= n_rows_local:
                break
            if label in ("Hole", "Par", "Hcp", ""):
                continue
            # Separator row (empty label)
            if label == "":
                continue
            # Scores row (not Netto and not blank)
            if label not in ("Netto") and not label.endswith("Netto") and label not in ("Hole", "Par", "Hcp"):
                # Associated player base name
                p_base = label.split(" (", 1)[0]
                scores = players.get(p_base, {}).get("Score", [])
                for off in range(hole_count):
                    global_hole = start_idx + off
                    try:
                        cell = table[(row_idx, off + 1)]
                    except KeyError:
                        continue
                    par = pars[global_hole] if global_hole < len(pars) else None
                    sc = scores[global_hole] if global_hole < len(scores) else None
                    if sc is None or par is None:
                        cell.set_facecolor("red")
                        continue
                    if sc == par - 1:
                        cell.set_facecolor("violet")
                    elif sc == par:
                        cell.set_facecolor("lightgreen")
                    elif sc == par + 2:
                        cell.set_facecolor("khaki")
                    elif sc > par + 2:
                        cell.set_facecolor("red")
            elif label == "Netto":
                # Netto row styling (text colors only)
                nettos = table[(row_idx, 1):(row_idx, hole_count)] if False else None  # placeholder not used
                for off in range(hole_count):
                    try:
                        cell = table[(row_idx, off + 1)]
                    except KeyError:
                        continue
                    txt = cell.get_text()
                    val = txt.get_text().strip()
                    try:
                        ival = int(val)
                    except Exception:
                        ival = None
                    cell.set_facecolor("white")
                    txt.set_weight('bold')
                    if ival == 0:
                        txt.set_color("red")
                    elif ival == 1:
                        txt.set_color("yellow")
                    elif ival == 2:
                        txt.set_color("black")
                    elif isinstance(ival, int) and ival >= 3:
                        txt.set_color("green")
                    else:
                        txt.set_color("black")
                # Net total column (last one)
                try:
                    net_cell = table[(row_idx, hole_count + 1)]
                    net_cell.get_text().set_weight('bold')
                except Exception:
                    pass

        # Separator rows: remove borders
        for r_idx, label in enumerate(row_labels):
            if label == "":
                for c in range(n_cols_local):
                    try:
                        cell = table[(r_idx, c)]
                        cell.set_facecolor("white")
                        cell.set_edgecolor("white")
                        cell.set_linewidth(0)
                        cell.get_text().set_text("")
                    except Exception:
                        pass

        # Header row adjustments: Add header for Net column (we use 'Net')
        try:
            # Hole labels row is index 0; last column = Net header
            header_net = table[(0, hole_count + 1)]
            header_net.get_text().set_text("Net")
            header_net.set_facecolor("lightgray")
        except Exception:
            pass

        if out_path:
            fig.canvas.draw()
            bbox = table.get_window_extent(renderer=fig.canvas.get_renderer())
            bbox_inches = bbox.transformed(fig.dpi_scale_trans.inverted())
            fig.savefig(out_path, dpi=100, bbox_inches=bbox_inches, pad_inches=0)
            print(f"[ok] Saved to {out_path}")
        if show:
            plt.show()
        plt.close(fig)

    # Decide output paths for the two halves
    front_path = None
    back_path = None
    if save_path:
        import os
        root, ext = os.path.splitext(save_path)

        #front_path = save_path  # keep original path for holes 1-9
        front_path = f"scorecards/{date_key}_front{ext}"  # holes 10-18
        back_path = f"scorecards/{date_key}_back{ext}"  # holes 10-18

        print(front_path)
        print(back_path)

    # Render 1–9 and 10–18
    render_half(0, 9, front_path, date_key)
    render_half(9, 18, back_path, date_key)


def main():
    json_file = "json/allrounds.json"
    date_key = "07.10.2024"  # Schlüssel wie in deiner JSON
    show_scorecard(json_file, date_key, save_path="scorecard.png", show=True)


if __name__ == "__main__":
    main()
