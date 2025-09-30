import os
import streamlit as st
from PIL import Image

# Function to load images from directory
def load_images_from_directory(directory):
    image_files = []
    for file in os.listdir(directory):  # Get all files in the directory
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):  # Filter image files
            image_files.append(file)
    return sorted(image_files)  # Return sorted list of images

# Streamlit app starts here
st.title("All time rankings:")

# Directory selection
directory = "rankings/"

if os.path.exists(directory):  # Check if the directory exists
    # Load image files
    images = load_images_from_directory(directory)

    if len(images) == 0:
        st.write("No images found in the directory.")
    else:
        # Display each image with its name
        for image_file in images:
            # Extract file name without extension
            file_name = os.path.splitext(image_file)[0]
            st.write(f"**{file_name}**")  # Display file name
            # Open and display the image
            image_path = os.path.join(directory, image_file)
            image = Image.open(image_path)
            st.image(image, width='stretch')
else:
    st.error("The provided directory does not exist. Please check the path.")
