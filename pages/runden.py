import os
import streamlit as st
from PIL import Image
from datetime import datetime

# Function to load images from directory
directory = "ranking"
image_files = []
    

# Streamlit app starts here
st.title("All time rankings:")

# Directory selection
directory1 = "rankings/"
directory2 = "scorecards/"

if os.path.exists(directory1):  # Check if the directory exists
    # Load image files
    for file in os.listdir(directory1):  # Get all files in the directory
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):  # Filter image files
            image_files.append(file)
            #images = sorted(image_files)  # Return sorted list of images
            images = sorted(image_files, key=lambda d: datetime.strptime(os.path.splitext(d)[0], "%d.%m.%Y"), reverse=True)
            #images = load_images_from_directory(directory)

    if len(images) == 0:
        st.write("No images found in the directory.")
    else:
        # Display each image with its name
        for image_file in images:
            # Extract file name without extension
            file_name = os.path.splitext(image_file)[0]
            st.write(f"**{file_name}**")  # Display file name
            # Open and display the image
            image_path = os.path.join(directory1, image_file)
            image = Image.open(image_path)
            st.image(image, width='stretch')
            
            # Extract file name for scorecards
            file_name = os.path.splitext(image_file)[0]
            # st.write(f"**{file_name}**")  # Display file name
            # Open and display the image
            image_path = os.path.join(directory2, image_file)
            
            
            if os.path.exists(image_path):
                image = Image.open(image_path)
                st.image(image, width='stretch')
                # ggf. weiterverarbeiten, z.B. st.image(image)
            else:
                print(f"Image not found: {image_path}")
             
            
else:
    st.error("The provided directory does not exist. Please check the path.")
