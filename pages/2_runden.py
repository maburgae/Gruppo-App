import os
import streamlit as st
from PIL import Image
from datetime import datetime
import json

def render(st):
    # Streamlit app starts here
    st.title("All time rankings:")

    # Directory selection
    directory1 = "rankings/"
    directory2 = "scorecards/"
    image_files = []

    # Load round metadata (Ort) from JSON
    json_path = "json/allrounds.json"
    round_metadata = {}
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for date_key, round_obj in data.items():
                ort = round_obj.get("Ort", "")
                round_metadata[date_key] = ort

    if os.path.exists(directory1):  # Check if the directory exists
        # Load image files
        for file in os.listdir(directory1):  # Get all files in the directory
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):  # Filter image files
                image_files.append(file)
        images = sorted(image_files, key=lambda d: datetime.strptime(os.path.splitext(d)[0], "%d.%m.%Y"), reverse=True)

        if len(images) == 0:
            st.write("No images found in the directory.")
        else:
            # Display each image with its name
            for image_file in images:
                # Extract file name without extension
                file_name = os.path.splitext(image_file)[0]
                # Get Ort from JSON metadata
                ort = round_metadata.get(file_name, "")
                if ort:
                    display_name = f"{file_name} ({ort})"
                else:
                    display_name = file_name
                st.write(f"**{display_name}**")  # Display file name
                # Open and display the image
                image_path = os.path.join(directory1, image_file)
                image = Image.open(image_path)
                st.image(image, width='stretch')

                # Extract file name for scorecards
                image_path2 = os.path.join(directory2, image_file)
                if os.path.exists(image_path2):
                    image2 = Image.open(image_path2)
                    st.image(image2, width='stretch')
                else:
                    print(f"Image not found: {image_path2}")
    else:
        st.error("The provided directory does not exist. Please check the path.")

if __name__ == "__main__":
    render(st)
