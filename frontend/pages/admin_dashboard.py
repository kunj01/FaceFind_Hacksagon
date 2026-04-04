"""
FaceFind — Admin Dashboard (Streamlit)

Features:
  - Admin login
  - Upload Google Drive folder link → process all images
  - Scene understanding chart
  - Event management (view/delete)
  - Platform analytics
"""

import streamlit as st
import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import (
    verify_user, get_all_events, get_scene_counts,
    get_photos_by_scene, delete_event_photos,
    get_photo_stats, insert_photo, get_connection
)
from services.drive_utils import download_drive_folder
from services.scene_engine import scene_engine, SCENE_CATEGORIES, SCENE_EMOJIS
from services.face_engine import face_engine


# ── Page config ──────────────────────────────────────────────────────────────

def render_admin_dashboard():
    """Main entry point called from app.py."""

    # ── Auth gate ──────────────────────────────────────────────────────────
    if not st.session_state.get("admin_logged_in"):
        _render_login()
        return

    # ── Logged in ─────────────────────────────────────────────────────────
    st.sidebar.success(f"👤 {st.session_state.get('admin_name', 'Admin')}")
    if st.sidebar.button("🚪 Logout", key="admin_logout"):
        for key in ["admin_logged_in", "admin_name", "admin_id"]:
            st.session_state.pop(key, None)
        st.rerun()

    # Top-level admin tabs
    tabs = st.tabs([
        "📤 Upload Photos",
        "📊 Analytics",
        "🗂️ Event Manager",
        "🔍 Browse Scenes"
    ])

    with tabs[0]:
        _render_upload_tab()
    with tabs[1]:
        _render_analytics_tab()
    with tabs[2]:
        _render_event_manager_tab()
    with tabs[3]:
        _render_browse_tab()


# ── Login ─────────────────────────────────────────────────────────────────────

def _render_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center; padding: 2rem 0 1rem;'>
            <h1 style='font-size:3rem;'>🔐</h1>
            <h2 style='color:#6C63FF;'>Admin Login</h2>
            <p style='color:#888;'>FaceFind Control Panel</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("admin_login_form"):
            email = st.text_input("📧 Admin Email", placeholder="admin@facefind.ai")
            password = st.text_input("🔑 Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Login →", use_container_width=True)

        if submitted:
            user = verify_user(email, password)
            if user and user["role"] == "admin":
                st.session_state["admin_logged_in"] = True
                st.session_state["admin_name"] = user["name"]
                st.session_state["admin_id"] = user["id"]
                st.success("✅ Login successful!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Invalid credentials or insufficient permissions.")

        st.markdown("""
        <p style='text-align:center; color:#666; font-size:0.85rem; margin-top:1rem;'>
        Default: admin@facefind.ai / admin123
        </p>
        """, unsafe_allow_html=True)


# ── Upload Tab ────────────────────────────────────────────────────────────────

def _render_upload_tab():
    st.markdown("## 📤 Upload Event Photos")

    src_tab_drive, src_tab_local = st.tabs([
        "☁️ Google Drive Folder",
        "💻 Upload from Computer"
    ])

    # ── Source 1: Google Drive ────────────────────────────────────────────
    with src_tab_drive:
        st.markdown(
            "Paste a **Google Drive folder link** shared as *Anyone with the link can view*."
        )
        with st.form("upload_form_drive"):
            col1, col2 = st.columns([2, 1])
            with col1:
                drive_url = st.text_input(
                    "🔗 Google Drive Folder URL",
                    placeholder="https://drive.google.com/drive/folders/XXXXXX"
                )
            with col2:
                event_name_d = st.text_input(
                    "📅 Event Name",
                    placeholder="Annual Fest 2025"
                )
            col_a, col_b = st.columns(2)
            with col_a:
                run_scene_d = st.checkbox("🎭 Scene Understanding (CLIP + YOLO)", value=True)
            with col_b:
                run_face_d = st.checkbox("👤 Face Embeddings (ArcFace)", value=True)
            process_btn_d = st.form_submit_button("🚀 Process Photos", use_container_width=True)

        if process_btn_d:
            if not drive_url.strip():
                st.error("Please provide a Google Drive URL.")
            elif not event_name_d.strip():
                st.error("Please provide an event name.")
            else:
                _run_processing_pipeline(
                    drive_url.strip(), event_name_d.strip(),
                    run_scene=run_scene_d, run_face=run_face_d
                )

    # ── Source 2: Direct upload ───────────────────────────────────────────
    with src_tab_local:
        st.markdown(
            "Upload photos **directly from your computer** — the most reliable option for demos."
        )
        col1, col2 = st.columns([2, 1])
        with col1:
            uploaded_files = st.file_uploader(
                "📁 Select Photos (JPG / PNG / WEBP)",
                type=["jpg", "jpeg", "png", "webp", "bmp"],
                accept_multiple_files=True,
                key="local_upload_files"
            )
        with col2:
            event_name_l = st.text_input(
                "📅 Event Name",
                placeholder="Annual Fest 2025",
                key="local_event_name"
            )

        col_a2, col_b2 = st.columns(2)
        with col_a2:
            run_scene_l = st.checkbox("🎭 Scene Understanding (CLIP + YOLO)",
                                      value=True, key="local_run_scene")
        with col_b2:
            run_face_l  = st.checkbox("👤 Face Embeddings (ArcFace)",
                                      value=True, key="local_run_face")

        if uploaded_files:
            st.caption(f"✅ {len(uploaded_files)} file(s) selected")

        process_btn_l = st.button("🚀 Process Uploaded Photos",
                                  use_container_width=True, type="primary",
                                  disabled=(not uploaded_files),
                                  key="local_process_btn")

        if process_btn_l and uploaded_files:
            if not event_name_l.strip():
                st.error("Please provide an event name.")
            else:
                _run_local_upload_pipeline(
                    uploaded_files, event_name_l.strip(),
                    run_scene=run_scene_l, run_face=run_face_l
                )


def _run_local_upload_pipeline(uploaded_files, event_name, run_scene, run_face):
    """Save uploaded UploadedFile objects to disk, then run AI pipeline."""
    import os
    from pathlib import Path

    admin_id = st.session_state.get("admin_id", "admin")
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
    dest_dir = Path(UPLOAD_DIR) / event_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    st.markdown("---")
    st.subheader("💾 Saving uploaded photos…")
    save_progress = st.progress(0, text="Saving files…")

    image_paths = []
    for i, uf in enumerate(uploaded_files):
        save_path = dest_dir / uf.name
        with open(save_path, "wb") as f:
            f.write(uf.getbuffer())
        image_paths.append(str(save_path))
        save_progress.progress((i + 1) / len(uploaded_files),
                               text=f"Saved {i+1}/{len(uploaded_files)}: {uf.name}")

    save_progress.progress(1.0, text=f"✅ Saved {len(image_paths)} photos")
    _run_ai_pipeline(image_paths, event_name, run_scene, run_face, admin_id)


def _run_processing_pipeline(drive_url, event_name, run_scene, run_face):
    """Download images from Drive then run the shared AI pipeline."""
    admin_id = st.session_state.get("admin_id", "admin")

    # ── Step 1: Download from Google Drive ───────────────────────────────
    st.markdown("---")
    st.subheader("⬇️ Step 1: Downloading from Google Drive")
    progress_bar = st.progress(0, text="Connecting to Google Drive…")

    try:
        with st.spinner("Downloading images… (this may take a few minutes)"):
            image_paths = download_drive_folder(
                drive_url=drive_url,
                event_name=event_name,
                progress_callback=None,
            )
    except Exception as e:
        progress_bar.empty()
        st.error(f"❌ Download failed: {e}")
        st.warning(
            "💡 **Tip:** If Drive download keeps failing, switch to "
            "the **💻 Upload from Computer** tab — it always works!"
        )
        return

    total = len(image_paths)
    if total == 0:
        st.warning("⚠️ No images found in the Drive folder.")
        return

    st.success(f"✅ Downloaded **{total}** images from Google Drive")
    progress_bar.progress(1.0, text="Download complete!")

    _run_ai_pipeline(image_paths, event_name, run_scene, run_face, admin_id)


def _run_ai_pipeline(image_paths: list, event_name: str,
                     run_scene: bool, run_face: bool, admin_id: str):
    """Shared AI processing loop used by both Drive and local upload paths."""
    total = len(image_paths)
    if total == 0:
        st.warning("No images to process.")
        return

    st.subheader("🤖 AI Processing Pipeline")
    ai_progress = st.progress(0, text="Initializing AI engines…")
    status_area = st.empty()
    
    # Pre-load engines for better UX
    if run_scene:
        status_area.info("🧠 Loading Scene Engine (CLIP + YOLOv8)…")
        scene_engine._load_models()
    if run_face:
        status_area.info("👤 Loading Face Engine (face_recognition)…")
        face_engine._load()
    
    results_log = []
    scene_tally = {}

    for i, img_path in enumerate(image_paths):
        filename = os.path.basename(img_path)
        ai_progress.progress(i / total, text=f"Processing [{i+1}/{total}]: {filename}")
        status_area.info(f"🔄 Analyzing: `{filename}`")

        scene_data = {
            "scene": "unknown", "scene_label": "Unknown",
            "confidence": 0.0, "objects": [], "object_count": 0, "emoji": "📁"
        }
        face_count = 0

        # Scene understanding
        if run_scene:
            try:
                scene_data = scene_engine.analyze(img_path)
            except Exception as e:
                scene_data["scene"] = "error"

        # Store photo metadata in DuckDB
        photo_id = insert_photo(
            filename=filename,
            local_path=img_path,
            event_name=event_name,
            scene_label=scene_data["scene"],
            scene_confidence=scene_data["confidence"],
            detected_objects=scene_data["objects"],
            face_count=0,
            uploaded_by=admin_id
        )

        # Face embedding extraction
        if run_face:
            try:
                added = face_engine.process_image(img_path, photo_id)
                face_count = added
            except Exception as e:
                face_count = 0

        # Update photo face count in DB
        try:
            conn = get_connection()
            conn.execute("UPDATE photos SET face_count = ? WHERE id = ?", [face_count, photo_id])
            conn.close()
        except Exception:
            pass

        scene_key = scene_data["scene"]
        scene_tally[scene_key] = scene_tally.get(scene_key, 0) + 1

        results_log.append({
            "File": filename,
            "Scene": f"{scene_data.get('emoji', '📁')} {scene_data['scene_label']}",
            "Confidence": f"{scene_data['confidence']*100:.1f}%",
            "Faces": face_count,
            "Objects": ", ".join(scene_data["objects"][:4]) if scene_data["objects"] else "—"
        })

    ai_progress.progress(1.0, text="✅ AI Processing Complete!")
    status_area.empty()

    # ── Results ───────────────────────────────────────────────────────────
    st.success(f"🎉 Successfully processed **{total}** photos for event: **{event_name}**")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📊 Scene Distribution")
        if scene_tally:
            df_scene = pd.DataFrame(
                list(scene_tally.items()), columns=["Scene", "Count"]
            ).sort_values("Count", ascending=False)
            fig = px.bar(
                df_scene, x="Scene", y="Count",
                color="Count",
                color_continuous_scale="Viridis",
                template="plotly_dark"
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📋 Processing Log")
        st.dataframe(
            pd.DataFrame(results_log),
            use_container_width=True,
            height=350
        )


# ── Analytics Tab ─────────────────────────────────────────────────────────────

def _render_analytics_tab():
    st.markdown("## 📊 Platform Analytics")
    stats = get_photo_stats()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🖼️ Total Photos", stats["total_photos"])
    col2.metric("👥 Registered Users", stats["total_users"])
    col3.metric("🔍 Total Searches", stats["total_searches"])
    col4.metric("✅ Face Matches", stats["total_matches"])

    st.markdown("---")

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📁 Scene Distribution (All Events)")
        scene_counts = get_scene_counts()
        if scene_counts:
            df = pd.DataFrame(scene_counts)
            df["emoji"] = df["scene"].map(SCENE_EMOJIS).fillna("📁")
            df["label"] = df["emoji"] + " " + df["scene"].str.replace("_", " ").str.title()
            fig = px.pie(
                df, values="count", names="label",
                template="plotly_dark",
                color_discrete_sequence=px.colors.sequential.Plasma_r
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No photo data yet. Upload an event to see analytics.")

    with col_r:
        st.subheader("📅 Events Overview")
        events = get_all_events()
        if events:
            df_ev = pd.DataFrame(events)
            df_ev.columns = ["Event Name", "Photos", "Created At"]
            st.dataframe(df_ev, use_container_width=True)
        else:
            st.info("No events uploaded yet.")


# ── Event Manager Tab ─────────────────────────────────────────────────────────

def _render_event_manager_tab():
    st.markdown("## 🗂️ Event Manager")
    events = get_all_events()

    if not events:
        st.info("No events found. Upload photos first.")
        return

    for event in events:
        with st.expander(
            f"📅 **{event['name']}** — {event['photo_count']} photos | Created: {event['created_at'][:10]}",
            expanded=False
        ):
            col1, col2 = st.columns([3, 1])
            with col1:
                scenes = get_scene_counts(event_name=event["name"])
                if scenes:
                    df_s = pd.DataFrame(scenes)
                    df_s["emoji"] = df_s["scene"].map(SCENE_EMOJIS).fillna("📁")
                    df_s["Scene"] = df_s["emoji"] + " " + df_s["scene"].str.replace("_", " ").str.title()
                    st.dataframe(df_s[["Scene", "count"]].rename(columns={"count": "Photos"}),
                                 use_container_width=True)
            with col2:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button(f"🗑️ Delete Event", key=f"del_{event['name']}"):
                    st.session_state[f"confirm_delete_{event['name']}"] = True

            if st.session_state.get(f"confirm_delete_{event['name']}"):
                st.warning(f"⚠️ Are you sure you want to delete **{event['name']}** and all its photos?")
                c1, c2 = st.columns(2)
                if c1.button("✅ Yes, Delete", key=f"yes_{event['name']}"):
                    delete_event_photos(event["name"])
                    st.session_state.pop(f"confirm_delete_{event['name']}", None)
                    st.success(f"Deleted event: {event['name']}")
                    st.rerun()
                if c2.button("❌ Cancel", key=f"no_{event['name']}"):
                    st.session_state.pop(f"confirm_delete_{event['name']}", None)
                    st.rerun()


# ── Browse Scenes Tab ─────────────────────────────────────────────────────────

def _render_browse_tab():
    st.markdown("## 🔍 Browse Photos by Scene")

    events = get_all_events()
    event_names = ["All Events"] + [e["name"] for e in events]
    selected_event = st.selectbox("📅 Select Event", event_names)
    event_filter = None if selected_event == "All Events" else selected_event

    scene_counts = get_scene_counts(event_name=event_filter)
    if not scene_counts:
        st.info("No photos found. Upload an event first.")
        return

    # Scene cards row
    st.markdown("### 📁 Scene Folders")
    cols = st.columns(5)
    for i, sc in enumerate(scene_counts):
        emoji = SCENE_EMOJIS.get(sc["scene"], "📁")
        label = sc["scene"].replace("_", " ").title()
        with cols[i % 5]:
            if st.button(
                f"{emoji}\n**{label}**\n{sc['count']} photos",
                key=f"scene_btn_{sc['scene']}_{i}",
                use_container_width=True
            ):
                st.session_state["browse_scene"] = sc["scene"]

    # Photo grid for selected scene
    selected_scene = st.session_state.get("browse_scene")
    if selected_scene:
        st.markdown(f"---\n### {SCENE_EMOJIS.get(selected_scene, '📁')} {selected_scene.replace('_', ' ').title()} Photos")
        photos = get_photos_by_scene(selected_scene, event_name=event_filter)
        if not photos:
            st.info("No photos in this scene.")
        else:
            COLS = 4
            for row_start in range(0, len(photos), COLS):
                row_photos = photos[row_start:row_start + COLS]
                cols = st.columns(len(row_photos))
                for j, photo in enumerate(row_photos):
                    with cols[j]:
                        try:
                            img = Image.open(photo["local_path"])
                            st.image(img, caption=photo["filename"][:20], use_container_width=True)
                            if photo["detected_objects"]:
                                st.caption("🏷️ " + " · ".join(photo["detected_objects"][:4]))
                        except Exception:
                            st.info(f"📷 {photo['filename']}")
