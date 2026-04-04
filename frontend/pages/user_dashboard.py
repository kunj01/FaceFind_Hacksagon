"""
FaceFind — User Dashboard (Streamlit)

Features:
  - Register / Login
  - Upload selfie → face search
  - Scene-filtered search
  - Results grid with download
  - Save all matches to personal library
  - Browse scene folders
"""

import streamlit as st
import os
import sys
import time
import tempfile
from pathlib import Path
import pandas as pd
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import (
    create_user, verify_user,
    get_scene_counts, get_photos_by_scene, get_photos_by_ids,
    get_all_events, insert_face_match, get_user_matched_photos, log_search
)
from services.face_engine import face_engine
from services.scene_engine import SCENE_EMOJIS, SCENE_CATEGORIES


# ── Entry Point ───────────────────────────────────────────────────────────────

def render_user_dashboard():
    if not st.session_state.get("user_logged_in"):
        _render_auth()
        return

    # Logged-in header with modern design
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        st.sidebar.markdown(f"**👤 {st.session_state.get('user_name', 'User')}**")
    with col2:
        if st.sidebar.button("🚪", key="user_logout", help="Logout", use_container_width=True):
            for key in ["user_logged_in", "user_name", "user_id", "user_email"]:
                st.session_state.pop(key, None)
            st.rerun()

    st.sidebar.markdown("---")

    tabs = st.tabs([
        "🔍 Find My Photos",
        "📚 My Library",
        "🗂️ Browse by Scene"
    ])
    with tabs[0]:
        _render_search_tab()
    with tabs[1]:
        _render_library_tab()
    with tabs[2]:
        _render_browse_tab()


# ── Auth ──────────────────────────────────────────────────────────────────────

def _render_auth():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center; padding: 2rem 0 1.5rem; animation: fadeInUp 0.6s ease-out;'>
            <h1 style='font-size:4rem; margin-bottom: 0.5rem;'>🤳</h1>
            <h1 style='background: linear-gradient(135deg, #0EA5E9, #8B5CF6); 
                -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                font-weight: 800; font-size: 2.5rem; margin: 0;'>
                Welcome to FaceFind
            </h1>
            <p style='color:#4B5563; font-size: 1.05rem; margin: 0.5rem 0 0; font-weight: 500;'>
                Find yourself in event photos instantly using AI
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Wrap auth in a clean card with animation
        with st.container(border=True):
            tab_login, tab_register = st.tabs(["🔑 Login", "✨ Register"])

            with tab_login:
                with st.form("user_login_form", border=False):
                    st.markdown("<div style='padding: 0.5rem 0;'></div>", unsafe_allow_html=True)
                    email = st.text_input(
                        "Email Address",
                        placeholder="you@example.com",
                        key="login_email"
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="••••••••",
                        key="login_password"
                    )
                    st.markdown("<div style='padding: 0.5rem 0;'></div>", unsafe_allow_html=True)
                    col_space, col_btn = st.columns([0.15, 0.85])
                    with col_btn:
                        submitted = st.form_submit_button(
                            "Sign In",
                            use_container_width=True,
                            type="primary"
                        )

                    if submitted:
                        if not email.strip():
                            st.error("Please enter your email.")
                        elif not password.strip():
                            st.error("Please enter your password.")
                        else:
                            user = verify_user(email, password)
                            if user and user["role"] == "user":
                                _set_session(user)
                                st.success("✅ Login successful!")
                                time.sleep(0.5)
                                st.rerun()
                            elif user and user["role"] == "admin":
                                st.warning("⚠️ This is an admin account. Use the Admin Dashboard to login.")
                            else:
                                st.error("❌ Invalid email or password.")

            with tab_register:
                with st.form("register_form", border=False):
                    st.markdown("<div style='padding: 0.5rem 0;'></div>", unsafe_allow_html=True)
                    name = st.text_input(
                        "Full Name",
                        placeholder="Ada Lovelace",
                        key="reg_name"
                    )
                    email_r = st.text_input(
                        "Email Address",
                        placeholder="you@example.com",
                        key="reg_email"
                    )
                    password_r = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Min 6 characters",
                        key="reg_pass"
                    )
                    confirm = st.text_input(
                        "Confirm Password",
                        type="password",
                        placeholder="Repeat password",
                        key="reg_confirm"
                    )
                    st.markdown("<div style='padding: 0.5rem 0;'></div>", unsafe_allow_html=True)
                    col_space, col_btn = st.columns([0.15, 0.85])
                    with col_btn:
                        submitted_r = st.form_submit_button(
                            "Create Account",
                            use_container_width=True,
                            type="primary"
                        )

                    if submitted_r:
                        if not name.strip():
                            st.error("Please enter your full name.")
                        elif not email_r.strip():
                            st.error("Please enter your email.")
                        elif len(password_r) < 6:
                            st.error("Password must be at least 6 characters.")
                        elif password_r != confirm:
                            st.error("Passwords do not match.")
                        else:
                            user = create_user(email_r.strip(), name.strip(), password_r, role="user")
                            if user:
                                _set_session(user)
                                st.success("🎉 Account created! Welcome to FaceFind.")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ An account with this email already exists.")



def _set_session(user: dict):
    st.session_state["user_logged_in"] = True
    st.session_state["user_name"] = user["name"]
    st.session_state["user_id"] = user["id"]
    st.session_state["user_email"] = user["email"]


# ── Search Tab ────────────────────────────────────────────────────────────────

def _render_search_tab():
    st.markdown("""
    <div style='text-align:center; padding-bottom: 1.5rem; animation: slideInDown 0.5s ease-out;'>
        <h2 style='font-size: 2rem; font-weight: 800; color: #111827; margin: 0;'>🔍 Find My Photos</h2>
        <p style='color: #4B5563; font-size: 0.95rem; margin-top: 0.5rem; font-weight: 500;'>
            Upload a photo and AI will find you across all event galleries
        </p>
    </div>
    
    <style>
        /* Camera input styling */
        [data-testid="stCameraInputWebcamStyledBox"] {
            width: 100% !important;
            height: 500px !important;
            min-height: 500px !important;
            border-radius: 12px !important;
            border: 2px solid #0EA5E9 !important;
        }
        
        [data-testid="stCameraInputWebcamStyledBox"] canvas,
        [data-testid="stCameraInputWebcamStyledBox"] video {
            width: 100% !important;
            height: 500px !important;
            object-fit: cover !important;
            border-radius: 12px !important;
        }
        
        /* Camera container */
        [data-testid="stCameraInput"] {
            width: 100% !important;
        }
        
        /* Make file uploader look clean */
        .stFileUploader section {
            padding: 0 !important;
            min-height: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize variables
    selfie_bytes = None
    uploaded_file = None
    selected_scenes = []
    selected_event_search = "All Events"
    sensitivity = 0.75

    # Main search container
    with st.container(border=True):
        col_left, col_right = st.columns([1.6, 1], gap="large")

        # LEFT COLUMN: Photo Input
        with col_left:
            st.markdown("#### 📸 Get Your Face")
            st.caption("Capture a selfie or browse your gallery")
            
            # Camera feed
            camera_img = st.camera_input(
                "Capture Selfie",
                key="camera_selfie",
                label_visibility="collapsed"
            )
            if camera_img:
                selfie_bytes = camera_img.getbuffer()
            
            # Browse file uploader
            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "📁 Or Browse from Gallery",
                type=["jpg", "jpeg", "png"],
                key="selfie_upload",
                label_visibility="collapsed"
            )
            
            if uploaded_file:
                selfie_bytes = uploaded_file.getbuffer()

            if selfie_bytes:
                st.markdown("""
                <div style='
                    background: rgba(16, 185, 129, 0.1);
                    border: 1px solid rgba(16, 185, 129, 0.3);
                    border-radius: 12px;
                    padding: 0.75rem;
                    text-align: center;
                    color: #059669;
                    font-weight: 600;
                    font-size: 0.9rem;
                    margin-top: 1rem;
                    animation: slideInDown 0.3s ease-out;
                '>
                    ✅ Photo ready for search
                </div>
                """, unsafe_allow_html=True)

        # RIGHT COLUMN: Filters
        with col_right:
            st.markdown("#### 🎯 Filter Results")
            st.caption("Optional filters to refine your search")

            scene_counts = get_scene_counts()
            available_scenes = [sc["scene"] for sc in scene_counts]

            if available_scenes:
                selected_scenes = st.multiselect(
                    "Scenes",
                    options=available_scenes,
                    format_func=lambda s: f"{SCENE_EMOJIS.get(s, '📁')} {s.replace('_', ' ').title()}",
                    key="scene_filter_ms",
                    placeholder="Leave empty to search all"
                )
            else:
                selected_scenes = []
                st.info("No photos uploaded yet. Ask admin to upload event photos first.")

            events = get_all_events()
            event_options = ["All Events"] + [e["name"] for e in events]
            selected_event_search = st.selectbox(
                "Event",
                options=event_options,
                key="event_filter_sel"
            )

            col_sens_label, col_sens_value = st.columns([0.6, 0.4])
            with col_sens_label:
                st.markdown("#### 🎚️ Sensitivity")
            with col_sens_value:
                st.markdown("<span style='color: #0EA5E9; font-weight: 700;' id='sens-val'>75%</span>", unsafe_allow_html=True)

            sensitivity = st.slider(
                "Match Sensitivity (higher = stricter matching)",
                min_value=0.2, max_value=0.95, value=0.75, step=0.05,
                key="sensitivity_slider",
                label_visibility="collapsed"
            )

    # Search button - positioned prominently
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    col_empty, col_search = st.columns([0.15, 0.85])
    with col_search:
        search_btn = st.button(
            "🚀 Start Searching",
            use_container_width=True,
            type="primary",
            disabled=(selfie_bytes is None)
        )

    if search_btn and selfie_bytes:
        _run_face_search(
            selfie_bytes=selfie_bytes,
            selected_scenes=selected_scenes,
            selected_event=None if selected_event_search == "All Events" else selected_event_search,
            sensitivity=sensitivity
        )


def _run_face_search(selfie_bytes, selected_scenes, selected_event, sensitivity):
    user_id = st.session_state["user_id"]

    # Save selfie bytes to temp file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(bytes(selfie_bytes))
        selfie_path = tmp.name

    try:
        with st.spinner("🔍 Scanning face embeddings…"):
            # Get scene-filtered photo IDs if needed
            allowed_ids = None
            if selected_scenes or selected_event:
                allowed_ids = set()
                scenes_to_search = selected_scenes if selected_scenes else list(SCENE_CATEGORIES.keys())
                for sc in scenes_to_search:
                    photos = get_photos_by_scene(sc, event_name=selected_event)
                    for p in photos:
                        allowed_ids.add(p["id"])

            # Temporarily override distance threshold per sensitivity
            # High sensitivity (0.9) means strict (0.33 threshold).
            # Low sensitivity (0.4) means loose (0.51 threshold).
            import services.face_engine as fe_mod
            original_threshold = fe_mod.DISTANCE_THRESHOLD
            fe_mod.DISTANCE_THRESHOLD = round(0.65 - (sensitivity * 0.35), 3)

            match_results = face_engine.search(
                selfie_path=selfie_path,
                top_k=100,
                allowed_photo_ids=allowed_ids
            )

            # Apply hard threshold: Only show 60% or above
            match_results = [m for m in match_results if m.get("confidence", 0) >= 0.6]

            fe_mod.DISTANCE_THRESHOLD = original_threshold

        if not match_results:
            st.warning("😕 No matching photos found. Try a different selfie or lower sensitivity.")
            log_search(user_id, 0, ",".join(selected_scenes) if selected_scenes else None)
            return

        # Fetch full photo metadata
        matched_ids = [m["photo_id"] for m in match_results]
        photos = get_photos_by_ids(matched_ids)

        # Save matches to DB
        conf_map = {m["photo_id"]: m["confidence"] for m in match_results}
        for photo in photos:
            insert_face_match(user_id, photo["id"], conf_map.get(photo["id"], 0.0))

        log_search(user_id, len(photos), ",".join(selected_scenes) if selected_scenes else None)

        # Display results
        st.markdown(f"---\n### ✅ Found **{len(photos)}** Photos of You!")
        _render_photo_grid(photos, show_confidence=True, conf_map=conf_map)

    finally:
        try:
            os.unlink(selfie_path)
        except Exception:
            pass


# ── Library Tab ───────────────────────────────────────────────────────────────

def _render_library_tab():
    st.markdown("""
    <div style='text-align:center; padding-bottom: 1.5rem; animation: slideInDown 0.5s ease-out;'>
        <h2 style='font-size: 2rem; font-weight: 800; color: #111827; margin: 0;'>📚 My Matched Photos</h2>
        <p style='color: #4B5563; font-size: 0.95rem; margin-top: 0.5rem; font-weight: 500;'>
            Your favorite photos from all events
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    user_id = st.session_state["user_id"]
    photos = get_user_matched_photos(user_id)

    if not photos:
        st.info("No matched photos yet. Go to **Find My Photos** tab and take a selfie!")
        return

    # Apply hard threshold: Only show 60% or above in Library
    photos = [p for p in photos if p.get("confidence", 0) >= 0.6]

    if not photos:
        st.info("No matches with 60% or higher confidence yet.")
        return

    # Stats row with smooth animations
    col1, col2, col3 = st.columns(3, gap="small")
    with col1:
        st.metric("🖼️ Total Matches", len(photos))
    with col2:
        events_in_matches = len(set(p["event_name"] for p in photos))
        st.metric("📅 Events", events_in_matches)
    with col3:
        scenes_in_matches = len(set(p["scene_label"] for p in photos))
        st.metric("🎭 Scene Types", scenes_in_matches)

    st.markdown("<div style='padding: 1rem 0;'></div>", unsafe_allow_html=True)

    # Filter by event
    event_names = list(set(p["event_name"] for p in photos if p["event_name"]))
    if event_names:
        filter_event = st.selectbox(
            "Filter by Event",
            ["All"] + event_names,
            key="library_event_filter"
        )
        if filter_event != "All":
            photos = [p for p in photos if p["event_name"] == filter_event]

    _render_photo_grid(photos, show_confidence=True,
                       conf_map={p["id"]: p.get("confidence", 0) for p in photos})


# ── Browse Tab ────────────────────────────────────────────────────────────────

def _render_browse_tab():
    st.markdown("""
    <div style='text-align:center; padding-bottom: 1.5rem; animation: slideInDown 0.5s ease-out;'>
        <h2 style='font-size: 2rem; font-weight: 800; color: #111827; margin: 0;'>🗂️ Browse Photos by Scene</h2>
        <p style='color: #4B5563; font-size: 0.95rem; margin-top: 0.5rem; font-weight: 500;'>
            Explore event photography organized by AI detection
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        events = get_all_events()
        event_names = ["All Events"] + [e["name"] for e in events]
        selected_event = st.selectbox(
            "Select Event to Browse",
            event_names,
            key="browse_event_user"
        )
        event_filter = None if selected_event == "All Events" else selected_event

        scene_counts = get_scene_counts(event_name=event_filter)
        if not scene_counts:
            st.info("No photos found. Ask your admin to upload event photos.")
            return

        # Scene cards with smooth animations
        st.markdown("<div style='padding: 1rem 0;'></div>", unsafe_allow_html=True)
        SCENE_COLS = 5
        cols = st.columns(SCENE_COLS, gap="small")
        for i, sc in enumerate(scene_counts):
            emoji = SCENE_EMOJIS.get(sc["scene"], "📁")
            label = sc["scene"].replace("_", " ").title()
            with cols[i % SCENE_COLS]:
                if st.button(
                    f"{emoji}\n{label}\n{sc['count']} 📷",
                    key=f"user_scene_{sc['scene']}_{i}",
                    use_container_width=True
                ):
                    st.session_state["user_browse_scene"] = sc["scene"]
                    st.session_state["user_browse_event"] = event_filter

    selected_scene = st.session_state.get("user_browse_scene")
    if selected_scene:
        st.markdown("<div style='padding: 1rem 0;'></div>", unsafe_allow_html=True)
        ev = st.session_state.get("user_browse_event", event_filter)
        photos = get_photos_by_scene(selected_scene, event_name=ev)
        emoji = SCENE_EMOJIS.get(selected_scene, "📁")
        st.markdown(f"#### {emoji} {selected_scene.replace('_', ' ').title()}")
        st.caption(f"{len(photos)} photos")
        if photos:
            _render_photo_grid(photos)
        else:
            st.info("No photos in this scene.")


# ── Photo Grid ────────────────────────────────────────────────────────────────

def _render_photo_grid(photos: list, show_confidence: bool = False,
                       conf_map: dict = None, cols: int = 4):
    """Render a responsive photo grid with optional confidence badge and download."""
    if conf_map is None:
        conf_map = {}

    # Apply hard threshold: 60%+ if confidence is requested (Search/Library)
    if show_confidence:
        photos = [p for p in photos if conf_map.get(p["id"], p.get("confidence", 0)) >= 0.6]

    if not photos:
        if show_confidence:
             st.info("No photos found with a high enough match (min 60%).")
        return

    for row_start in range(0, len(photos), cols):
        row = photos[row_start:row_start + cols]
        grid_cols = st.columns(len(row))
        for j, photo in enumerate(row):
            with grid_cols[j]:
                try:
                    img = Image.open(photo["local_path"])

                    # Confidence badge
                    conf = conf_map.get(photo["id"], photo.get("confidence"))
                    caption_parts = []
                    if show_confidence and conf is not None:
                        pct = int(conf * 100)
                        badge = "🟢" if pct >= 70 else "🟡" if pct >= 40 else "🔴"
                        caption_parts.append(f"{badge} {pct}% match")

                    scene_emoji = SCENE_EMOJIS.get(photo.get("scene_label", ""), "📁")
                    scene_label = photo.get("scene_label", "").replace("_", " ").title()
                    if scene_label:
                        caption_parts.append(f"{scene_emoji} {scene_label}")
                    if photo.get("event_name"):
                        caption_parts.append(f"📅 {photo['event_name']}")

                    caption_text = " · ".join(caption_parts) if caption_parts else photo["filename"]

                    st.image(img, caption=caption_text, use_container_width=True)

                    # Download button (reads photo bytes)
                    with open(photo["local_path"], "rb") as f:
                        img_bytes = f.read()
                    st.download_button(
                        label="⬇️ Download",
                        data=img_bytes,
                        file_name=photo["filename"],
                        mime="image/jpeg",
                        key=f"dl_{photo['id']}_{row_start}_{j}",
                        use_container_width=True
                    )

                    # Detected objects
                    if photo.get("detected_objects"):
                        st.caption("🏷️ " + " · ".join(photo["detected_objects"][:3]))

                except Exception:
                    st.info(f"📷 {photo.get('filename', 'Photo')}")
