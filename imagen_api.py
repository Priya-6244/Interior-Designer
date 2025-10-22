# utils/imagen_api.py

import streamlit as st
from vertexai.preview.vision_models import Image, ImageGenerationModel
from PIL import Image as PILImage, ImageDraw
import io

def create_mask(image_bytes, vertices):
    try:
        image = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
        width, height = image.size
        
        mask = PILImage.new('L', (width, height), 0)
        draw = ImageDraw.Draw(mask)
        
        pixel_coords = [(v.x * width, v.y * height) for v in vertices]
        draw.polygon(pixel_coords, fill=255)
        
        mask_bytes_io = io.BytesIO()
        mask.save(mask_bytes_io, format='PNG')
        return mask_bytes_io.getvalue()
    except Exception as e:
        st.error(f"An error occurred while creating mask: {e}")
        return None

def generate_new_image(original_image_bytes, mask_bytes, prompt_text):
    try:
        # Using the recommended Imagen model version 
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        source_image = Image(image_bytes=original_image_bytes)
        mask_image = Image(image_bytes=mask_bytes)
        
        st.info(f"Generating image with prompt: '{prompt_text}'... Please wait.")

        images = model.edit_image(
            base_image=source_image,
            mask=mask_image,
            prompt=prompt_text,
            number_of_images=1,
            # ✅ Guidance Scale increased to enforce prompt adherence
            guidance_scale=35, 
        )
        
        img_byte_arr = io.BytesIO()
        images[0]._pil_image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()

    except Exception as e:
        st.error(f"Error during image generation: {e}")
        return None