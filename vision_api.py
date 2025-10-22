# utils/vision_api.py

from google.cloud import vision
import streamlit as st

def detect_objects(image_content):
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_content)
        
        # Correctly calling object_localization
        response = client.object_localization(image=image)
        
        objects = response.localized_object_annotations
        
        if response.error.message:
            st.error(f"Vision API Error: {response.error.message}")
            return []
            
        return objects
    except Exception as e:
        st.error(f"An error occurred in detect_objects: {e}")
        return []