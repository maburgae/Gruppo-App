from openai import OpenAI
import pandas as pd
import json
from openpyxl import load_workbook
import cv2
import numpy as np
from pathlib import Path
from get_from_icloud import download_and_convert_scorecards, login
from pathlib import Path
from preprocess_pic import preprocess
from functions import calculate_money_for_players, copy_scorecard_to_golf_df,create_default_golf_json, merge_golf_df_jsons, merge_json_files_on_date, clean_json_arrays, upload_image_for_vision, query_vision_model, print_scorecard_table_from_json, write_scorecard_to_excel
from show_scorecard import show_scorecard
from datetime import date, datetime
from calc_the_day import apply_dayhcps_from_json, update_round_for_date
from DayHcp import calc_dayhcps_for_players_before_date


# Path to your Excel file
# excel_file = "2025_Malaga_SPORTIVO_STATISTIKO (Kopie).xlsm"

# Path to the scorecard image
# #image_path = "IMG_0055.jpg"   # file-QUUL2qwCqHKnTM4AFQe4vm  Buffy Marc Bernie Andy
# image_path = "IMG_0060.jpg"     # file-8mmR171eCLG3PjorUVjMgD Buffy Marc Jens Bernie

# Set model type
gpt_model = "gpt-5-mini"  # Vision-capable model

# Login to iCloud and download scorecards
# api = login("marc@burgaezi.de")
# download_and_convert_scorecards(api, Path.home())

# Preprocess image
# out_path = Path(image_path).with_stem(Path(image_path).stem + "_proc").with_suffix(".png")
#preprocess(image_path, image_path)
#image_path = out_path

# Upload file to ai
image_id = upload_image_for_vision(image_path)
image_id = "file-8mmR171eCLG3PjorUVjMgD"

# If the file was already uploaded, you can read the file_id from param.json
# image_id = json.load(open("param.json", "r", encoding="utf-8")).get("file_id", "")

# Prepare prompt for Vision API
prompt = (
    "Extract all relevant golf scorecard data from the image and return it in EXACTLY the following nested JSON structure."
    "The output must be ONE single JSON object, not a list or multiple objects."
    "The key in the json must be 'Hole','Par','Hcp' and the names of the Players"
    "The value must be a dict with keys: 'Hole' (list of 18 par values), 'Par' (list of 18 par values), 'Hcp' (list of 18 hcp values), and one key for each player with the name (list of 18 par score values)."
    "The hole values must be from 1 to 18 in order. The par values must be integers between 3 and 5. The hcp values must be integers between 1 and 18. The score values must be integers or null (for no score) or 0 for 'x', '-', '/' or similar unclear values."
    "For the player names include only these names if found: Marc, Andy, Bernie, Buffy, Heiko, Jens, Markus."
    "Do NOT add, remove, or rename any keys. Do NOT change the nesting. Do NOT output any explanation, markdown, or text before or after the JSON. Do NOT output an array, do NOT split the keys into separate objects. The output must be directly parsable by json.loads()."
    "If a player name is on the card but no scores, but 18 nulls in the Score array. The player names are handwritten."
    "Follow this example structure EXACTLY:{\"Hole\": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18], \"Par\": [5,4,4,4,4,3,4,3,5,5,4,4,3,5,4,4,3,4],\"Hcp\": [9,5,13,11,1,17,15,3,7,6,4,18,12,2,8,10,16,14],\"Bernie\": [7,6,6,4,6,5,4,8,0,null,6,6,7,null,null,5,7,9],\"Marc\": [7,6,6,4,6,5,4,8,0,null,6,6,7,null,null,5,7,9]}"
)

now = datetime.now()
date_time = now.strftime("%d.%m.%Y %H:%M:%S")
scorecard_path = f"json/golf_df/golf_df_{date_time}.json"
day_path = f"json/golf_df/golf_df.json"
today = date.today()
date_key = today.strftime("%d.%m.%Y")
ort = "Hallo"

create_default_golf_json(day_path, date_key, ort, ["Marc", "Bernie", "Buffy", "Jens"])

query_vision_model(image_id, scorecard_path, gpt_model , prompt)

copy_scorecard_to_golf_df(scorecard_path, day_path)

calc_dayhcps_for_players_before_date(date_key)
apply_dayhcps_from_json(day_path, "json/DayHcp.json")

# Step 4: Calculate round for a certain date
# date_key = "2.09.2025"   # <- gewünschtes Datum
update_round_for_date(day_path, date_key)

# Add money
calculate_money_for_players(day_path, date_key)

# date_key = "22.09.2025"  # Schlüssel wie in deiner JSON
show_scorecard(day_path, date_key, save_path="scorecard.png", show=True)

