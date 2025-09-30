
from openai import OpenAI
import json
from datetime import date, datetime
from functions import upload_image_for_vision, query_vision_model, copy_scorecard_to_golf_df

def main(image_path: str | None = None) -> str:
    """Verarbeitet Upload-Referenz (File-ID). Platzhalter-Logik."""
    if not image_path:
        return "Keine File-ID übergeben."
    
    #######################################################
    # Disabled to run without AI query
    image_id = upload_image_for_vision(image_path)
    #######################################################
    
    # Set model type
    gpt_model = "gpt-5-mini"  # Vision-capable model

    # Preprocess image
    # out_path = Path(image_path).with_stem(Path(image_path).stem + "_proc").with_suffix(".png")
    #preprocess(image_path, image_path)
    #image_path = out_path

    # image_id = "file-8mmR171eCLG3PjorUVjMgD"

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
    scorecard_path = f"json/golf_df/ai_result_{date_time}.json"
    day_path = f"json/golf_df/golf_df.json"
    today = date.today()
    date_key = today.strftime("%d.%m.%Y")

    #######################################
    ## code to run without ai query
    #scorecard_path = f"json/golf_df/ai_result_29.09.2025 23_19_18.json"
    success = query_vision_model(image_id, scorecard_path, gpt_model , prompt)
    #success = True
    copy_scorecard_to_golf_df(scorecard_path, day_path)
    #######################################
    
    return success
