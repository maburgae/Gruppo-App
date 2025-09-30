import json
from collections import defaultdict

with open("json/allrounds.json", "r", encoding="utf-8") as f:
    data = json.load(f)

player_hcps = defaultdict(list)

for round_obj in data.values():
    spieler = round_obj.get("Spieler", {})
    for name, pdata in spieler.items():
        hcp = pdata.get("Gesp.Hcp")
        if isinstance(hcp, int):
            player_hcps[name].append(hcp)

selected_players = ["Andy", "Marc", "Bernie", "Heiko", "Markus", "Buffy", "Jens"]

# Filtered player_hcps
print("Average Gesp.Hcp for each player:")
for name in selected_players:
    hcps = player_hcps.get(name, [])
    avg = sum(hcps) / len(hcps) if hcps else None
    print(f"{name}: {avg:.2f}" if avg is not None else f"{name}: No data")

print("\nLowest and Highest Gesp.Hcp for each player:")
header = "Spieler\tMin Gesp.Hcp\tMax Gesp.Hcp"
print(header)
for name in selected_players:
    hcps = player_hcps.get(name, [])
    if hcps:
        min_hcp = min(hcps)
        max_hcp = max(hcps)
        print(f"{name}\t{min_hcp}\t{max_hcp}")
    else:
        print(f"{name}\tNo data\tNo data")

# Calculate average Platz for each player
player_platz = defaultdict(list)
for round_obj in data.values():
    spieler = round_obj.get("Spieler", {})
    for name, pdata in spieler.items():
        platz = pdata.get("Platz")
        if isinstance(platz, int):
            player_platz[name].append(platz)

# Filtered average Platz
print("\nAverage Platz for each player:")
for name in selected_players:
    platz_list = player_platz.get(name, [])
    avg_platz = sum(platz_list) / len(platz_list) if platz_list else None
    print(f"{name}: {avg_platz:.2f}" if avg_platz is not None else f"{name}: No data")

# Count how often each player has each Platz (1-8)
platz_counts = defaultdict(lambda: defaultdict(int))
all_players = set()
for round_obj in data.values():
    # Finde den/die Spieler mit Platz 1 pro Runde
    spieler = round_obj.get("Spieler", {})
    min_platz = None
    for name, pdata in spieler.items():
        platz = pdata.get("Platz")
        if isinstance(platz, int):
            if min_platz is None or platz < min_platz:
                min_platz = platz
    # Zähle nur den/die Spieler mit Platz 1 pro Runde
    for name, pdata in spieler.items():
        platz = pdata.get("Platz")
        if isinstance(platz, int) and platz == min_platz and min_platz == 1:
            platz_counts[name][platz] += 1
        elif isinstance(platz, int) and 2 <= platz <= 8:
            platz_counts[name][platz] += 1
        all_players.add(name)

# Prepare sorted list of players
players_sorted = sorted(all_players)

# Filtered Platz table
filtered_players_sorted = [p for p in players_sorted if p in selected_players]
header = "Platz" + "\t" + "\t".join(filtered_players_sorted) + "\tSumme"
print(header)
row_sums = []
col_sums = [0] * len(filtered_players_sorted)
for platz in range(1, 9):
    row = [str(platz)]
    row_sum = 0
    for i, player in enumerate(filtered_players_sorted):
        val = platz_counts[player][platz]
        row.append(str(val))
        row_sum += val
        col_sums[i] += val
    row.append(str(row_sum))
    row_sums.append(row_sum)
    print("\t".join(row))
# Print column sums
sum_row = ["Summe"] + [str(s) for s in col_sums] + [str(sum(row_sums))]
print("\t".join(sum_row))

# Birdie-Tabelle
birdie_counts = defaultdict(int)
birdie_rounds = defaultdict(int)
for round_obj in data.values():
    spieler = round_obj.get("Spieler", {})
    for name, pdata in spieler.items():
        birdies = pdata.get("Birdies")
        if isinstance(birdies, int):
            birdie_counts[name] += birdies
            birdie_rounds[name] += 1
        elif birdies is not None:
            birdie_rounds[name] += 1

print("\nBirdies pro Spieler:")
header = "Spieler\tBirdies\tRunden\tBirdies/Runde"
print(header)
for player in selected_players:
    total = birdie_counts[player]
    rounds = birdie_rounds[player]
    avg = total / rounds if rounds else 0
    print(f"{player}\t{total}\t{rounds}\t{avg:.2f}")

# Pars-Tabelle
pars_counts = defaultdict(int)
pars_rounds = defaultdict(int)
for round_obj in data.values():
    spieler = round_obj.get("Spieler", {})
    for name, pdata in spieler.items():
        pars = pdata.get("Pars")
        if isinstance(pars, int):
            pars_counts[name] += pars
            pars_rounds[name] += 1
        elif pars is not None:
            pars_rounds[name] += 1

print("\nPars pro Spieler:")
header = "Spieler\tPars\tRunden\tPars/Runde"
print(header)
for player in selected_players:
    total = pars_counts[player]
    rounds = pars_rounds[player]
    avg = total / rounds if rounds else 0
    print(f"{player}\t{total}\t{rounds}\t{avg:.2f}")

# Bogies-Tabelle
bogies_counts = defaultdict(int)
bogies_rounds = defaultdict(int)
for round_obj in data.values():
    spieler = round_obj.get("Spieler", {})
    for name, pdata in spieler.items():
        bogies = pdata.get("Bogies")
        if isinstance(bogies, int):
            bogies_counts[name] += bogies
            bogies_rounds[name] += 1
        elif bogies is not None:
            bogies_rounds[name] += 1

print("\nBogies pro Spieler:")
header = "Spieler\tBogies\tRunden\tBogies/Runde"
print(header)
for player in selected_players:
    total = bogies_counts[player]
    rounds = bogies_rounds[player]
    avg = total / rounds if rounds else 0
    print(f"{player}\t{total}\t{rounds}\t{avg:.2f}")

# Strich-Tabelle
strich_counts = defaultdict(int)
strich_rounds = defaultdict(int)
for round_obj in data.values():
    spieler = round_obj.get("Spieler", {})
    for name, pdata in spieler.items():
        strich = pdata.get("Strich")
        if isinstance(strich, int):
            strich_counts[name] += strich
            strich_rounds[name] += 1
        elif strich is not None:
            strich_rounds[name] += 1

print("\nStrich pro Spieler:")
header = "Spieler\tStrich\tRunden\tStrich/Runde"
print(header)
for player in selected_players:
    total = strich_counts[player]
    rounds = strich_rounds[player]
    avg = total / rounds if rounds else 0
    print(f"{player}\t{total}\t{rounds}\t{avg:.2f}")
