# app.py (Polished & Fully Functional)

import streamlit as st
import os
from google.cloud import aiplatform
import requests
import io
from PIL import Image as PILImage

# --- UTILS ---
from utils.vision_api import detect_objects
from utils.imagen_api import create_mask, generate_new_image

# --- CONFIG ---
PROJECT_ID = "ai-style-curator"
LOCATION = "us-central1"
PRIMARY_COLOR = "#BF092F"
SECONDARY_COLOR = "#3B9797"
TEXT_COLOR = "#0D7C98"
LIGHT_BG = "#f5f5f5"
SIDEBAR_BG = "#054C02"
PLACEHOLDER_BG = "#e7e7e7"

# --- AUTHENTICATION ---
try:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = (
        r"C:\Users\srika\Downloads\iship_project\iship_project\credentials\service_key.json"
    )
    if 'aiplatform_init' not in st.session_state:
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        st.session_state['aiplatform_init'] = True
except Exception as e:
    st.error(f"Authentication Error: {e}")
    st.stop()

# --- HELPER ---
def process_style_input(style_option, text_prompt, uploaded_style_file, style_link):
    if style_option == "Describe it (Text Prompt)":
        return text_prompt
    elif style_option == "Upload a Style Image":
        if uploaded_style_file:
            if not text_prompt:
                st.warning("Please describe the style based on the uploaded image.")
                return ""
            st.success("Style image uploaded successfully.")
            return text_prompt
        return ""
    elif style_option == "Use an Image Link (URL)" and style_link:
        try:
            r = requests.get(style_link, timeout=5)
            r.raise_for_status()
            PILImage.open(io.BytesIO(r.content))
            if not text_prompt:
                st.warning("Please describe the style based on the image link.")
                return ""
            st.success("Fetched style image successfully!")
            return text_prompt
        except Exception:
            st.error("Invalid URL or inaccessible image.")
            return ""
    return ""

# --- STREAMLIT CONFIG ---
st.set_page_config(
    page_title="Inspacio AI Interior Designer 🎨",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GOOGLE FONT ---
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap" rel="stylesheet">',
    unsafe_allow_html=True
)

# --- STYLES ---
st.markdown(f"""
<style>
.stApp {{ background-color:{LIGHT_BG}; color:{TEXT_COLOR}; font-family:'Poppins', sans-serif; }}
p, label, .stMarkdown, .stText, .stTextInput, .stTextArea, .stFileUploader label {{ color:{TEXT_COLOR} !important; }}
section[data-testid="stSidebar"] {{ background-color:{SIDEBAR_BG} !important; color:#f2f2f2 !important; padding:1rem 1.2rem; }}
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] p {{ color:#f2f2f2 !important; }}
.st-emotion-cache-p5m9b9 h2 {{ color:{PRIMARY_COLOR} !important; font-weight:700; font-size:1.5rem; }}
.header-logo {{ display:flex; align-items:center; justify-content:center; font-weight:800; font-size:2.4rem; color:{TEXT_COLOR}; gap:0.6rem; margin:1rem 0 0.5rem 0; }}
.header-logo i {{ color:{PRIMARY_COLOR}; font-size:2.8rem; }}
h2, h3 {{ color:{TEXT_COLOR} !important; font-weight:700 !important; border-bottom:2px solid {SECONDARY_COLOR}33; padding-bottom:0.4rem; margin-top:1.8rem; margin-bottom:1rem; }}
.main .block-container:first-of-type > div:first-child {{ padding: 2rem; background-color: white; border-radius:1rem; box-shadow:0 10px 30px rgba(0,0,0,0.08); }}
div.stButton > button:first-child {{ background-color:{PRIMARY_COLOR}; color:white; font-weight:700; border-radius:9999px; padding:0.7rem 1.8rem; transition:all 0.3s; box-shadow:0 4px 10px rgba(0,0,0,0.15); }}
div.stButton > button:first-child:hover {{ background-color:{SECONDARY_COLOR}; box-shadow:0 0 15px {SECONDARY_COLOR}55; transform:scale(1.03); }}
.placeholder-box {{ height:400px; display:flex; align-items:center; justify-content:center; color:#333 !important; background-color:{PLACEHOLDER_BG}; border:2px dashed #cccccc; border-radius:10px; font-size:1.1em; }}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<div class='header-logo'><i class='fas fa-magic'></i> Inspacio AI Designer</div>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#555; margin-bottom:2rem;'>Instantly restyle furniture or rooms using AI.</p>", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("📤 Upload Your Photo")
    uploaded_room_file = st.file_uploader("Choose a room image...", type=["jpg","jpeg","png"])
    
    if uploaded_room_file and uploaded_room_file.name != st.session_state.get('room_file_name'):
        st.session_state['detected_objects'] = None
        st.session_state['room_file_name'] = uploaded_room_file.name
        st.rerun()
    
    if uploaded_room_file:
        st.subheader("🖼️ Original Room")
        st.image(uploaded_room_file, use_container_width=True)
    st.markdown("---")
    st.caption("Powered by Google Cloud Vision & Imagen Models.")

if not uploaded_room_file:
    st.info("⬆️ Please upload a room image to begin.")
    st.stop()

# --- DETECTION ---
image_bytes = uploaded_room_file.getvalue()
detected_objects = []

if 'detected_objects' not in st.session_state or st.session_state['detected_objects'] is None:
    with st.spinner("🔍 Detecting objects..."):
        try:
            detected_objects = detect_objects(image_bytes)
            st.session_state['detected_objects'] = detected_objects
        except Exception as e:
            st.error(f"Object detection failed: {e}")
            st.stop()
else:
    detected_objects = st.session_state['detected_objects']

display_names = ["Wall (Restyle Whole Room)"] if not detected_objects else sorted(list(set([obj.name for obj in detected_objects])))
if "Wall" in display_names: display_names.remove("Wall")
display_names.insert(0, "Wall (Restyle Whole Room)")

# --- MAIN CONTENT ---
left, right = st.columns([1.1,1.4], gap="large")

with left:
    st.markdown("## ⚙️ Design Controls")
    
    st.subheader("2️⃣ Select Item to Restyle")
    selected_object_name = st.selectbox("Select object:", display_names, label_visibility="collapsed", key="selected_item_key")
    
    st.subheader("3️⃣ Define New Style")
    style_option = st.radio("Style Input Method:", 
                            ("Describe it (Text Prompt)", "Upload a Style Image", "Use an Image Link (URL)"),
                            horizontal=True, key="style_method_key")
    
    text_prompt = ""
    uploaded_style_file = None
    style_link = ""
    
    if style_option == "Describe it (Text Prompt)":
        text_prompt = st.text_input("Style description:", placeholder="e.g., 'modern walnut texture'", key="text_prompt_direct")
    elif style_option == "Upload a Style Image":
        uploaded_style_file = st.file_uploader("Upload a style image...", type=["jpg","jpeg","png"], key="uploaded_style_file")
        if uploaded_style_file: st.image(uploaded_style_file, caption="Style Reference", width=120)
        text_prompt = st.text_input("Describe the style briefly:", placeholder="e.g., 'velvet with gold trim'", key="text_prompt_upload")
    elif style_option == "Use an Image Link (URL)":
        style_link = st.text_input("Enter image URL:", placeholder="https://example.com/style.jpg", key="style_link")
        text_prompt = st.text_input("Describe the style:", placeholder="e.g., 'white minimalist aesthetic'", key="text_prompt_url")
    
    st.markdown("## 🚀 Generate")
    st.markdown("---")
    generate_button = st.button("✨ Generate New Design!", use_container_width=True, type="primary")

with right:
    st.markdown("## ✨ Design Concepts")
    result_placeholder = st.empty()
    
    if not generate_button:
        result_placeholder.markdown("<div class='placeholder-box'>Upload and configure your design to see results here.</div>", unsafe_allow_html=True)
    
    if generate_button:
        final_prompt = process_style_input(style_option, text_prompt, uploaded_style_file, style_link)
        if not final_prompt.strip():
            result_placeholder.error("Please enter a valid style description in step 3.")
            st.stop()
        
        if selected_object_name == "Wall (Restyle Whole Room)":
            vertices = []
            actual_object_name = "room/wall"
        else:
            selected_data = next((obj for obj in detected_objects if obj.name == selected_object_name), None)
            if not selected_data:
                result_placeholder.error(f"Could not find object data for '{selected_object_name}'.")
                st.stop()
            vertices = selected_data.bounding_poly.normalized_vertices
            actual_object_name = selected_object_name
        
        with st.status(f"Running AI Pipeline for **{actual_object_name}**...", expanded=True) as status_box:
            status_box.update(label=f"🎨 Stage 1: Creating mask for {actual_object_name}...")
            try:
                mask_content = create_mask(image_bytes, vertices)
                if not mask_content: raise ValueError("Mask content is empty.")
                status_box.update(label="✅ Stage 1: Mask created successfully!", state="running")
            except Exception as e:
                status_box.update(label="❌ Stage 1: Mask creation failed!", state="error", expanded=True)
                st.error(f"Mask creation failed: {e}")
                st.stop()
            
            prompt_text = (
                f"Replace the {actual_object_name} with a photorealistic {actual_object_name} styled as '{final_prompt}'. "
                f"ONLY MODIFY COLOR AND TEXTURE. KEEP ORIGINAL GEOMETRY, LIGHTING, AND BACKGROUND."
            )
            
            status_box.update(label="🤖 Stage 2: Generating new design...", state="running")
            try:
                new_image = generate_new_image(image_bytes, mask_content, prompt_text)
                if not new_image: raise ValueError("Image generation returned no image.")
                status_box.update(label="🎉 AI Design Complete!", state="complete")
            except Exception as e:
                status_box.update(label="❌ Stage 2: Image generation failed!", state="error", expanded=True)
                st.error(f"Image generation failed: {e}")
                st.stop()
        
        result_placeholder.empty()
        with result_placeholder.container():
            st.markdown("### Primary Result")
            st.markdown(f"<p style='font-size:small; color:#777;'>Targeted Style: <i>{final_prompt}</i></p>", unsafe_allow_html=True)
            st.image(new_image, caption=f"Redesigned {actual_object_name}", use_container_width=True)
            st.success("Design successfully generated!")
            
            st.markdown("---")
            st.markdown("### 💡 Other Style Suggestions")
            sugg_col1, sugg_col2 = st.columns(2)
            with sugg_col1:
                rec_prompt_1 = f"Replace the {actual_object_name} with a photorealistic {actual_object_name} that has a 'sleek marble texture'. Preserve original shape."
                with st.expander("Try: Sleek Marble Texture"):
                    with st.spinner("Generating suggestion 1..."):
                        rec_image_1 = generate_new_image(image_bytes, mask_content, rec_prompt_1)
                    if rec_image_1: st.image(rec_image_1, caption="Style: Sleek Marble", use_container_width=True)
                    else: st.warning("Suggestion failed.")
            with sugg_col2:
                rec_prompt_2 = f"Replace the {actual_object_name} with a photorealistic {actual_object_name} that has a 'vintage burnt orange velvet'. Preserve original shape."
                with st.expander("Try: Vintage Burnt Orange Velvet"):
                    with st.spinner("Generating suggestion 2..."):
                        rec_image_2 = generate_new_image(image_bytes, mask_content, rec_prompt_2)
                    if rec_image_2: st.image(rec_image_2, caption="Style: Burnt Orange Velvet", use_container_width=True)
                    else: st.warning("Suggestion failed.")
