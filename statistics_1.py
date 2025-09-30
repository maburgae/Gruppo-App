# avg_hcp.py
import sys
import json
from collections import defaultdict

def main(in_path: str):
    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # accumulate all Hcp values per player
    hcps = defaultdict(list)

    for date, info in data.items():
        for player, stats in info.get("Spieler", {}).items():
            h = stats.get("Gesp.Hcp")
            if h is not None:
                hcps[player].append(h)

    # calculate averages
    averages = {}
    for player, values in hcps.items():
        if values:
            averages[player] = sum(values) / len(values)
        else:
            averages[player] = None

    # pretty print results
    print("Average Hcp per player (based on available rounds):")
    for player, avg in sorted(averages.items()):
        if avg is None:
            print(f"{player:15s}: no Hcp values")
        else:
            print(f"{player:15s}: {avg:.2f}")

if __name__ == "__main__":

    main("allrounds.json")
