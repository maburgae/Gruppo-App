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
    rows.append([str(h) for h in holes])
    rows.append([str(p) if p is not None else "" for p in pars])
    rows.append([str(h) if h is not None else "" for h in hcps])
    for pname, pdata in players.items():
        # Scores row
        scores = []
        score_list = pdata.get("Score", [])
        score_list = list(score_list) + [None] * (18 - len(score_list))
        for sc in score_list:
            if sc is None:
                scores.append("x")
            else:
                scores.append(str(sc))
        rows.append(scores)
        row_labels.append(pname if pdata.get("DayHcp", "") == "" else f"{pname} ({pdata['DayHcp']})")
        # NettoP row
        nettopoints = []
        np_list = pdata.get("NettoP", [])
        np_list = list(np_list) + [None] * (18 - len(np_list))
        for np in np_list:
            if np is None:
                nettopoints.append("")
            else:
                nettopoints.append(str(np))
        rows.append(nettopoints)
        row_labels.append(f"{pname} NettoP")

    # Ensure all rows are exactly 18 columns
    for i in range(len(rows)):
        if len(rows[i]) > 18:
            rows[i] = rows[i][:18]
        elif len(rows[i]) < 18:
            rows[i] += [""] * (18 - len(rows[i]))

    col_labels = [""] + [str(h) for h in holes]
    cell_data = [[label] + row for label, row in zip(row_labels, rows)]

    # Helper to render a half (start inclusive, end exclusive) of the scorecard
    def render_half(start_idx: int, end_idx: int, out_path: str | None, date_key: str):
        local_cols = end_idx - start_idx
        # Slice each row to the requested hole range
        cell_data_half = [[label] + row[start_idx:end_idx] for label, row in zip(row_labels, rows)]

        fig, ax = plt.subplots(figsize=(20, 15))
        ax.axis("off")

        # Remove extra whitespace around the table
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

        # Reduce internal cell padding
        for cell in table.get_celld().values():
            try:
                cell.set_pad(0.01)
            except Exception:
                pass

        # Make the first column wider
        for key, cell in table.get_celld().items():
            if key[1] == 0:
                cell.set_width(0.20)  # a bit wider for label column

        # Make Par values bold (row index 1)
        for col_idx in range(1, local_cols + 1):
            cell = table[(1, col_idx)]
            cell.set_text_props(weight='bold')

        # Coloring scores and nettopoints
        for row_idx, pname in enumerate(row_labels):
            if pname in ("Hole", "Par", "Hcp"):
                continue
            # Scores row
            if not pname.endswith("NettoP"):
                p_base = pname.split(" (", 1)[0]
                scores = players.get(p_base, {}).get("Score", [])
                for off in range(local_cols):
                    global_hole = start_idx + off
                    try:
                        cell = table[(row_idx, off + 1)]
                    except KeyError:
                        continue
                    sc = scores[global_hole] if global_hole < len(scores) else None
                    par = pars[global_hole] if global_hole < len(pars) else None
                    if sc is None or par is None:
                        cell.set_facecolor("red")
                        continue
                    if sc == par - 1:
                        cell.set_facecolor("violet")
                    elif sc == par:
                        cell.set_facecolor("lightgreen")
                    elif sc == par + 1:
                        pass
                    elif sc == par + 2:
                        cell.set_facecolor("khaki")
                    else:
                        cell.set_facecolor("red")
            # NettoP row: font color only, no background
            else:
                p_base = pname.replace(" NettoP", "")
                nettopoints = players.get(p_base, {}).get("NettoP", [])
                for off in range(local_cols):
                    global_hole = start_idx + off
                    try:
                        cell = table[(row_idx, off + 1)]
                    except KeyError:
                        continue
                    np = nettopoints[global_hole] if global_hole < len(nettopoints) else None
                    cell.set_facecolor("white")  # No background
                    text = cell.get_text()
                    text.set_weight('bold')
                    if np == 0:
                        text.set_color("red")
                    elif np == 1:
                        text.set_color("yellow")
                    elif np == 2:
                        text.set_color("black")
                    elif isinstance(np, int) and np >= 3:
                        text.set_color("green")
                    else:
                        text.set_color("black")

        # Save cropped exactly to table
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
