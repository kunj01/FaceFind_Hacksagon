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

    # Logged-in header
    st.sidebar.success(f"👤 {st.session_state.get('user_name', 'User')}")
    if st.sidebar.button("🚪 Logout", key="user_logout"):
        for key in ["user_logged_in", "user_name", "user_id", "user_email"]:
            st.session_state.pop(key, None)
        st.rerun()

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
        <div style='text-align:center; padding: 2rem 0 1rem;'>
            <h1 style='font-size:3rem;'>🤳</h1>
            <h2 style='color:#6C63FF;'>Welcome to FaceFind</h2>
            <p style='color:#888;'>Find yourself in event photos instantly</p>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔑 Login", "✨ Register"])

        with tab_login:
            with st.form("user_login_form"):
                email = st.text_input("📧 Email", placeholder="you@example.com")
                password = st.text_input("🔒 Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Login →", use_container_width=True)

            if submitted:
                user = verify_user(email, password)
                if user and user["role"] == "user":
                    _set_session(user)
                    st.success("✅ Login successful!")
                    time.sleep(0.5)
                    st.rerun()
                elif user and user["role"] == "admin":
                    st.warning("⚠️ This is a user account login. Use the Admin Dashboard for admin access.")
                else:
                    st.error("❌ Invalid email or password.")

        with tab_register:
            with st.form("register_form"):
                name = st.text_input("👤 Full Name", placeholder="Ada Lovelace")
                email_r = st.text_input("📧 Email", placeholder="you@example.com", key="reg_email")
                password_r = st.text_input("🔒 Password", type="password",
                                           placeholder="Min 6 characters", key="reg_pass")
                confirm = st.text_input("🔒 Confirm Password", type="password",
                                        placeholder="Repeat password", key="reg_confirm")
                submitted_r = st.form_submit_button("Create Account →", use_container_width=True)

            if submitted_r:
                if not name.strip():
                    st.error("Please enter your name.")
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
                        st.error("An account with this email already exists.")


def _set_session(user: dict):
    st.session_state["user_logged_in"] = True
    st.session_state["user_name"] = user["name"]
    st.session_state["user_id"] = user["id"]
    st.session_state["user_email"] = user["email"]


# ── Search Tab ────────────────────────────────────────────────────────────────

def _render_search_tab():
    st.markdown("## 🔍 Find My Photos")
    st.markdown("Take a selfie with your camera — FaceFind will locate you across all event photos.")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("### 📸 Capture Your Face")

        selfie_bytes = None

        camera_img = st.camera_input(
            "Click 📷 to take your selfie",
            key="camera_selfie"
        )
        if camera_img:
            selfie_bytes = camera_img.getbuffer()
            st.success("✅ Photo captured!")

    with col_right:
        st.markdown("### 🎭 Scene Filter (Optional)")
        st.caption("Narrow search to specific scene categories")

        scene_counts = get_scene_counts()
        available_scenes = [sc["scene"] for sc in scene_counts]

        selected_scenes = st.multiselect(
            "Select scenes (leave empty to search all)",
            options=available_scenes,
            format_func=lambda s: f"{SCENE_EMOJIS.get(s, '📁')} {s.replace('_', ' ').title()}",
            key="scene_filter_ms"
        )

        st.markdown("### 📅 Event Filter (Optional)")
        events = get_all_events()
        event_options = ["All Events"] + [e["name"] for e in events]
        selected_event_search = st.selectbox(
            "Narrow to a specific event",
            options=event_options,
            key="event_filter_sel"
        )

        sensitivity = st.slider(
            "🎯 Match Sensitivity",
            min_value=0.2, max_value=0.95, value=0.75, step=0.05,
            help="Lower = more results (fewer false negatives). Higher = stricter."
        )

    st.markdown("---")
    search_btn = st.button(
        "🚀 Find My Photos",
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
    st.markdown("## 📚 My Matched Photos")
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

    # Stats row
    col1, col2, col3 = st.columns(3)
    col1.metric("🖼️ Total Matches", len(photos))
    events_in_matches = len(set(p["event_name"] for p in photos))
    col2.metric("📅 Events", events_in_matches)
    scenes_in_matches = len(set(p["scene_label"] for p in photos))
    col3.metric("🎭 Scene Types", scenes_in_matches)

    st.markdown("---")

    # Filter by event
    event_names = list(set(p["event_name"] for p in photos if p["event_name"]))
    if event_names:
        filter_event = st.selectbox("📅 Filter by Event", ["All"] + event_names)
        if filter_event != "All":
            photos = [p for p in photos if p["event_name"] == filter_event]

    _render_photo_grid(photos, show_confidence=True,
                       conf_map={p["id"]: p.get("confidence", 0) for p in photos})


# ── Browse Tab ────────────────────────────────────────────────────────────────

def _render_browse_tab():
    st.markdown("## 🗂️ Browse Photos by Scene")

    events = get_all_events()
    event_names = ["All Events"] + [e["name"] for e in events]
    selected_event = st.selectbox("📅 Select Event", event_names, key="browse_event_user")
    event_filter = None if selected_event == "All Events" else selected_event

    scene_counts = get_scene_counts(event_name=event_filter)
    if not scene_counts:
        st.info("No photos found. Ask your admin to upload event photos.")
        return

    # Scene cards
    SCENE_COLS = 5
    cols = st.columns(SCENE_COLS)
    for i, sc in enumerate(scene_counts):
        emoji = SCENE_EMOJIS.get(sc["scene"], "📁")
        label = sc["scene"].replace("_", " ").title()
        with cols[i % SCENE_COLS]:
            if st.button(
                f"{emoji}\n{label}\n{sc['count']} photos",
                key=f"user_scene_{sc['scene']}_{i}",
                use_container_width=True
            ):
                st.session_state["user_browse_scene"] = sc["scene"]
                st.session_state["user_browse_event"] = event_filter

    selected_scene = st.session_state.get("user_browse_scene")
    if selected_scene:
        ev = st.session_state.get("user_browse_event", event_filter)
        photos = get_photos_by_scene(selected_scene, event_name=ev)
        emoji = SCENE_EMOJIS.get(selected_scene, "📁")
        st.markdown(f"---\n### {emoji} {selected_scene.replace('_', ' ').title()}")
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
