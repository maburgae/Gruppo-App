Lade allrounds.json, golf_df.json und abrechnung.json nach Github per Knopdruck
    Knopf schon vorhanden, tut aber noch nicht

abrechnung speichern und löschen mit commit und push nach github

Platz lesen von json in Konfig seite

no shows in allrounds json eintragen

anzeige anzahl schläge mit salso








In the allrounds.json file. There are rounds where only the head data is available. like Gesp. Hcp, Pars, etc.
Simulate the Par, Hcp and Scores for this rounds for every player. Put Par and Hcp in the file and then invents score that the overall result is exactly reflected like Gesp. Hcp, Pars, Bogies, Strich.

Here are the courses you need to add the numbers to the json:

Mennagio:
Hole	1	2	3	4	5	6	7	8	9	
Par	    4	3	3	4	5	4	3	4	4	
Hcp	    3	13	17	15	7	11	9	5	1	

Hole	10	11	12	13	14	15	16	17	18
Par	    3	4	4	5	5	3	4	4	4
Hcp	    6	4	10	12	8	16	2	14	18	

D'Este and Varese are in the json already at another day. Take Pars and Hcps from there.

For Lindau, Verona and Rovedine make assumptions for Par and Hcp like at a tyical Golf course.

Check if all empty rounds are now considered.

