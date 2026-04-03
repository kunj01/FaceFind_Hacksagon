"""
FaceFind — User Dashboard (Streamlit)
Professional Photo Gallery Retrieval System

Features:
  - Event title display
  - Name + Phone number input (simple form)
  - Live camera capture (prominent)
  - Privacy & consent checkboxes
  - "Get My Photos" button
  - Results gallery with download
  - Social media links
"""

import streamlit as st
import os
import sys
import time
import tempfile
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import (
    get_all_events, get_photos_by_ids,
    insert_face_match, log_search
)
from services.face_engine import face_engine
from services.scene_engine_light import SCENE_EMOJIS


# ─────────────────────────────────────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def render_user_dashboard():
    """Main user dashboard - professional photo retrieval interface"""
    
    # ⚡ HEADER - Event showcase
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0; font-size: 2.5rem;'>📸 Your Event Photos</h1>
        <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0;'>Find yourself in our collection instantly</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ─ Main search form ─
    st.markdown("## Get Your Photos")
    
    col_form = st.container()
    with col_form:
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input(
                "Full Name *",
                placeholder="Enter your full name",
                key="user_fullname"
            )
        with col2:
            phone_number = st.text_input(
                "Mobile Number *",
                placeholder="10-digit phone number",
                key="user_phone"
            )
    
    # ─ Camera Capture (PROMINENT) ─
    st.markdown("### 📷 Capture Your Selfie")
    
    col_cam, col_upload = st.columns([2, 1])
    with col_cam:
        camera_img = st.camera_input(
            "Click the camera icon to capture your selfie",
            key="selfie_capture"
        )
    with col_upload:
        st.markdown("<br>", unsafe_allow_html=True)
        uploaded_selfie = st.file_uploader(
            "Or upload a photo",
            type=["jpg", "jpeg", "png", "webp"],
            key="selfie_upload"
        )
    
    selfie_image = None
    if camera_img:
        selfie_image = camera_img
    elif uploaded_selfie:
        selfie_image = uploaded_selfie
    
    # ─ Privacy & Consent ─
    st.markdown("---")
    col_check1, col_check2 = st.columns([3, 1])
    
    with col_check1:
        agree_privacy = st.checkbox(
            "I agree to the Privacy Policy and give my Consent",
            value=False,
            key="privacy_check"
        )
    
    with col_check2:
        receive_promo = st.checkbox(
            "Send me updates",
            value=False,
            key="promo_check"
        )
    
    # ─ Main Action Button ─
    col_btn = st.container()
    with col_btn:
        button_col1, button_col2 = st.columns([2, 1])
        with button_col1:
            search_clicked = st.button(
                "🔍 GET MY PHOTOS",
                use_container_width=True,
                type="primary",
                key="search_button"
            )
    
    # ─ Execute Search ─
    if search_clicked:
        if not full_name.strip():
            st.error("❌ Please enter your name")
            return
        if not phone_number.strip():
            st.error("❌ Please enter your phone number")
            return
        if not agree_privacy:
            st.error("❌ Please accept the privacy policy")
            return
        if selfie_image is None:
            st.error("❌ Please capture or upload a selfie")
            return
        
        # Process the search
        _process_photo_search(full_name, phone_number, selfie_image)
    
    # ─ Footer with Social Links ─
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <p style='color: #666; margin-bottom: 1rem;'>Follow Us</p>
        <div style='display: flex; justify-content: center; gap: 1rem;'>
            <a href='#' style='font-size: 2rem; text-decoration: none;'>📘</a>
            <a href='#' style='font-size: 2rem; text-decoration: none;'>📷</a>
            <a href='#' style='font-size: 2rem; text-decoration: none;'>🎥</a>
            <a href='#' style='font-size: 2rem; text-decoration: none;'>💬</a>
            <a href='#' style='font-size: 2rem; text-decoration: none;'>🌐</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _process_photo_search(name: str, phone: str, selfie_image):
    """Process the photo search"""
    
    st.markdown("---")
    st.markdown("## 🔍 Searching for your photos...")
    
    # Show progress
    progress_bar = st.progress(0)
    status = st.empty()
    
    try:
        # Extract face embeddings from user's selfie
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(selfie_image.getvalue())
            tmp_path = tmp.name
        
        status.info("⏳ Analyzing your photo...")
        progress_bar.progress(25)
        
        # Extract face vector
        face_count = 0
        try:
            face_data = face_engine.extract_face_embeddings(tmp_path)
            if face_data and len(face_data) > 0:
                face_count = len(face_data)
                user_embedding = face_data[0]  # Use first face
            else:
                st.error("❌ Could not detect a face in your photo. Please try again with a clear selfie.")
                os.unlink(tmp_path)
                return
        except Exception as e:
            st.error(f"❌ Face detection error: {str(e)}")
            os.unlink(tmp_path)
            return
        
        status.info("⏳ Searching photo database...")
        progress_bar.progress(50)
        
        # Search FAISS index
        try:
            matched_ids = face_engine.search(user_embedding, top_k=100)
            if not matched_ids:
                progress_bar.progress(100)
                status.empty()
                st.warning("😔 No matches found. You might not be in these photos!")
                os.unlink(tmp_path)
                return
        except Exception as e:
            st.error(f"❌ Search error: {str(e)}")
            os.unlink(tmp_path)
            return
        
        status.info("⏳ Loading your photos...")
        progress_bar.progress(75)
        
        # Fetch matched photos
        matched_photos = get_photos_by_ids(matched_ids)
        
        progress_bar.progress(100)
        status.empty()
        
        if not matched_photos:
            st.warning("😔 No photos found for you.")
            os.unlink(tmp_path)
            return
        
        # ─ Display Results ─
        st.success(f"🎉 Found **{len(matched_photos)}** photos of you!")
        
        st.markdown("### 📸 Your Photos")
        
        # Display in grid
        COLS = 4
        for row_start in range(0, len(matched_photos), COLS):
            row_photos = matched_photos[row_start:row_start + COLS]
            grid = st.columns(len(row_photos))
            
            for idx, photo in enumerate(row_photos):
                with grid[idx]:
                    try:
                        img = Image.open(photo["local_path"])
                        st.image(img, caption=photo["filename"][:20], use_column_width=True)
                        
                        # Download button
                        with open(photo["local_path"], "rb") as f:
                            st.download_button(
                                label="⬇️ Download",
                                data=f.read(),
                                file_name=photo["filename"],
                                mime="image/jpeg",
                                key=f"download_{photo['id']}"
                            )
                    except Exception:
                        st.info(f"📷 {photo['filename']}")
        
        # Log the search
        try:
            log_search("anonymous", len(matched_photos), "selfie_search")
        except:
            pass
        
        # Cleanup
        os.unlink(tmp_path)
        
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        progress_bar.empty()
        status.empty()

