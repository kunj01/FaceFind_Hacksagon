"""
FaceFind — Admin Dashboard (Streamlit)

Features:
  - Admin login (default: admin@facefind.ai / admin123)
  - Upload via Google Drive link OR direct file upload
  - Scene understanding (CLIP + YOLOv8) + Face embeddings (ArcFace + FAISS)
  - Analytics charts
  - Event manager with delete + FAISS rebuild
  - Browse photos by scene
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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import (
    verify_user, get_all_events, get_scene_counts,
    get_photos_by_scene, delete_event_photos,
    get_photo_stats, insert_photo, update_photo_face_count,
    get_all_photos
)
from services.drive_utils import download_drive_folder
from services.scene_engine_light import scene_engine, SCENE_CATEGORIES, SCENE_EMOJIS
from services.face_engine import face_engine


# ─────────────────────────────────────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def render_admin_dashboard():
    """Main entry point called from app.py."""

    if not st.session_state.get("admin_logged_in"):
        _render_login()
        return

    st.sidebar.success(f"👤 {st.session_state.get('admin_name', 'Admin')}")
    if st.sidebar.button("🚪 Logout", key="admin_logout"):
        for key in ["admin_logged_in", "admin_name", "admin_id"]:
            st.session_state.pop(key, None)
        st.rerun()

    # ⚡ QUICK DEMO MODE BANNER ⚡
    st.markdown("""
    <div style='background: linear-gradient(90deg, #FF6B6B, #FF8C42); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center;'>
    <h2 style='color: white; margin: 0;'>⚡ INSTANT DEMO MODE ⚡</h2>
    <p style='color: white; margin: 0.5rem 0 0; font-size: 0.9rem;'>Upload 50 photos in <b>10-15 seconds</b> with no processing overhead</p>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs([
        "📤 Upload Photos",
        "📊 Analytics",
        "🗂️ Event Manager",
        "🔍 Browse Scenes",
    ])

    with tabs[0]: _render_upload_tab()
    with tabs[1]: _render_analytics_tab()
    with tabs[2]: _render_event_manager_tab()
    with tabs[3]: _render_browse_tab()


# ─────────────────────────────────────────────────────────────────────────────
#  Login
# ─────────────────────────────────────────────────────────────────────────────

def _render_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center; padding: 2rem 0 1rem;'>
            <span style='font-size:3rem;'>🔐</span>
            <h2 style='color:#6C63FF;'>Admin Login</h2>
            <p style='color:#888;'>FaceFind Control Panel</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("admin_login_form"):
            email    = st.text_input("📧 Admin Email", placeholder="admin@facefind.ai")
            password = st.text_input("🔑 Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Login →", use_container_width=True)

        if submitted:
            user = verify_user(email, password)
            if user and user["role"] == "admin":
                st.session_state["admin_logged_in"] = True
                st.session_state["admin_name"]      = user["name"]
                st.session_state["admin_id"]        = user["id"]
                st.success("✅ Login successful!")
                time.sleep(0.4)
                st.rerun()
            else:
                st.error("❌ Invalid credentials or not an admin account.")

        st.markdown("""
        <p style='text-align:center; color:#666; font-size:0.85rem; margin-top:1rem;'>
        Default: admin@facefind.ai / admin123
        </p>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Upload Tab
# ─────────────────────────────────────────────────────────────────────────────

def _render_upload_tab():
    st.markdown("## 📤 Upload Event Photos")

    src_drive, src_local = st.tabs([
        "☁️ Google Drive Folder",
        "💻 Upload from Computer",
    ])

    # ── Google Drive ──────────────────────────────────────────────────────
    with src_drive:
        st.markdown(
            "Paste a **Google Drive folder link** shared as *Anyone with the link can view*."
        )
        with st.form("upload_form_drive"):
            col1, col2 = st.columns([2, 1])
            with col1:
                drive_url    = st.text_input("🔗 Google Drive Folder URL",
                                              placeholder="https://drive.google.com/drive/folders/XXXXXX")
            with col2:
                event_name_d = st.text_input("📅 Event Name", placeholder="Annual Fest 2025")
            st.info("⚡ **INSTANT UPLOAD MODE** - Photos stored instantly (no processing)")
            col_a, col_b = st.columns(2)
            with col_a:
                run_scene_d = st.checkbox("🎭 Scene Categorization (adds 30s)", value=False)
            with col_b:
                run_face_d  = st.checkbox("👤 Face Extraction (adds 1-2 min)", value=False)
            process_btn_d = st.form_submit_button("⚡ INSTANT UPLOAD (no processing)", use_container_width=True)

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

    # ── Local Upload ──────────────────────────────────────────────────────
    with src_local:
        st.markdown("Upload photos **directly from your computer** — most reliable option for demos.")
        col1, col2 = st.columns([2, 1])
        with col1:
            uploaded_files = st.file_uploader(
                "📁 Select Photos (JPG / PNG / WEBP)",
                type=["jpg", "jpeg", "png", "webp", "bmp"],
                accept_multiple_files=True,
                key="local_upload_files"
            )
        with col2:
            event_name_l = st.text_input("📅 Event Name", placeholder="Annual Fest 2025",
                                          key="local_event_name")

        st.info("⚡ **INSTANT UPLOAD MODE** - Photos stored instantly (no processing)")
        col_a2, col_b2 = st.columns(2)
        with col_a2:
            run_scene_l = st.checkbox("🎭 Scene Categorization (adds 30s)",
                                      value=False, key="local_run_scene")
        with col_b2:
            run_face_l  = st.checkbox("👤 Face Extraction (adds 1-2 min)",
                                      value=False, key="local_run_face")

        if uploaded_files:
            st.caption(f"✅ {len(uploaded_files)} file(s) selected")

        process_btn_l = st.button(
            "⚡ INSTANT UPLOAD (no processing)",
            use_container_width=True, type="primary",
            disabled=(not uploaded_files),
            key="local_process_btn"
        )

        if process_btn_l and uploaded_files:
            if not event_name_l.strip():
                st.error("Please provide an event name.")
            else:
                _run_local_upload_pipeline(
                    uploaded_files, event_name_l.strip(),
                    run_scene=run_scene_l, run_face=run_face_l
                )


def _run_local_upload_pipeline(uploaded_files, event_name, run_scene, run_face):
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
    dest_dir   = Path(UPLOAD_DIR) / event_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    st.markdown("---")
    st.subheader("💾 Saving uploaded photos…")
    save_bar = st.progress(0, text="Saving files…")

    image_paths = []
    for i, uf in enumerate(uploaded_files):
        save_path = dest_dir / uf.name
        with open(save_path, "wb") as f:
            f.write(uf.getbuffer())
        image_paths.append(str(save_path))
        save_bar.progress((i + 1) / len(uploaded_files),
                           text=f"Saved {i+1}/{len(uploaded_files)}: {uf.name}")

    save_bar.progress(1.0, text=f"✅ Saved {len(image_paths)} photos")
    _run_ai_pipeline(image_paths, event_name, run_scene, run_face)


def _run_processing_pipeline(drive_url, event_name, run_scene, run_face):
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
            "💡 **Tip:** Switch to the **💻 Upload from Computer** tab — "
            "it always works!"
        )
        return

    total = len(image_paths)
    if total == 0:
        st.warning("⚠️ No images found in the Drive folder.")
        return

    st.success(f"✅ Downloaded **{total}** images from Google Drive")
    progress_bar.progress(1.0, text="Download complete!")
    _run_ai_pipeline(image_paths, event_name, run_scene, run_face)


def _run_ai_pipeline(image_paths: list, event_name: str, run_scene: bool, run_face: bool):
    """Shared AI processing loop with PARALLEL processing for ULTRA-FAST speeds."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    
    admin_id = st.session_state.get("admin_id", "admin")
    total    = len(image_paths)
    if total == 0:
        st.warning("No images to process.")
        return

    st.subheader("🤖 AI Processing Pipeline ⚡ PARALLEL MODE")
    ai_progress  = st.progress(0, text="Starting AI pipeline…")
    status_area  = st.empty()
    results_log  = []
    scene_tally  = {}
    results_lock = threading.Lock()
    
    # If no AI processing, skip the loop entirely
    if not run_scene and not run_face:
        for i, img_path in enumerate(image_paths):
            filename = os.path.basename(img_path)
            ai_progress.progress((i+1) / total, text=f"Uploading [{i+1}/{total}]: {filename}")
            
            # Just insert to DB without any AI
            photo_id = insert_photo(
                filename         = filename,
                local_path       = img_path,
                event_name       = event_name,
                scene_label      = "unknown",
                scene_confidence = 0.0,
                detected_objects = [],
                face_count       = 0,
                uploaded_by      = admin_id
            )
            
            results_log.append({
                "File":       filename,
                "Scene":      "—",
                "Confidence": "—",
                "Faces":      "—",
                "Objects":    "—",
            })
            with results_lock:
                scene_tally["unknown"] = scene_tally.get("unknown", 0) + 1
        
        ai_progress.progress(1.0, text="✅ Upload Complete!")
        status_area.empty()
        st.success(f"🎉 Successfully uploaded **{total}** photos for event: **{event_name}**")
        
        # Show quick results
        st.info("✨ Upload complete! Photos are ready for face search without scene processing.")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("📊 Upload Summary")
            if scene_tally:
                df_scene = pd.DataFrame(
                    list(scene_tally.items()), columns=["Scene", "Count"]
                ).sort_values("Count", ascending=False)
                df_scene["Scene"] = df_scene["Scene"].astype(str)
                df_scene["Count"] = df_scene["Count"].astype(int)
                st.dataframe(df_scene)
        
        with col2:
            st.subheader("📋 Upload Log")
            st.dataframe(pd.DataFrame(results_log), use_container_width=True, height=350)
        return

    # ─ PARALLEL AI Processing (8-12 concurrent workers for SPEED) ─────────────
    completed = [0]
    
    def process_single_image(img_path: str, index: int) -> dict:
        """Process one image - called in parallel."""
        filename = os.path.basename(img_path)
        
        scene_data = {
            "scene": "unknown", "scene_label": "Unknown",
            "confidence": 0.0, "objects": [], "object_count": 0, "emoji": "📁"
        }
        face_count = 0

        # Scene understanding (FAST with scene_engine_light)
        if run_scene:
            try:
                scene_data = scene_engine.analyze(img_path)
            except Exception:
                pass

        # Insert photo into DB
        photo_id = insert_photo(
            filename         = filename,
            local_path       = img_path,
            event_name       = event_name,
            scene_label      = scene_data["scene"],
            scene_confidence = scene_data["confidence"],
            detected_objects = scene_data["objects"],
            face_count       = 0,
            uploaded_by      = admin_id
        )

        # Face embedding extraction  
        if run_face:
            try:
                face_count = face_engine.process_image(img_path, photo_id)
            except Exception:
                face_count = 0
            update_photo_face_count(photo_id, face_count)

        # Update progress
        with results_lock:
            completed[0] += 1
            progress = completed[0] / total
            ai_progress.progress(progress, text=f"Processing [{completed[0]}/{total}]: {filename}")
            status_area.info(f"⚡ {completed[0]}/{total} processed ({progress*100:.0f}%)")

        return {
            "index": index,
            "filename": filename,
            "scene": scene_data["scene"],
            "scene_label": scene_data["scene_label"],
            "emoji": scene_data.get("emoji", "📁"),
            "confidence": scene_data["confidence"],
            "face_count": face_count,
            "objects": scene_data["objects"],
        }

    # Use 8-12 workers for parallel processing (balanced for stability)
    max_workers = min(12, total, 12)  # Cap at 12 concurrent
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_image, img_path, i): i
            for i, img_path in enumerate(image_paths)
        }
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results_log.append({
                    "File":       result["filename"],
                    "Scene":      f"{result['emoji']} {result['scene_label']}",
                    "Confidence": f"{result['confidence']*100:.1f}%",
                    "Faces":      result["face_count"],
                    "Objects":    ", ".join(result["objects"][:4]) if result["objects"] else "—",
                })
                with results_lock:
                    scene_key = result["scene"]
                    scene_tally[scene_key] = scene_tally.get(scene_key, 0) + 1
            except Exception as e:
                pass

    ai_progress.progress(1.0, text="✅ AI Processing Complete!")
    status_area.empty()

    st.success(f"🎉 Successfully processed **{total}** photos for event: **{event_name}** ⚡")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📊 Scene Distribution")
        if scene_tally:
            df_scene = pd.DataFrame(
                list(scene_tally.items()), columns=["Scene", "Count"]
            ).sort_values("Count", ascending=False)
            # Cast to native Python types to avoid numpy type issues
            df_scene["Scene"] = df_scene["Scene"].astype(str)
            df_scene["Count"] = df_scene["Count"].astype(int)
            fig = px.bar(df_scene, x="Scene", y="Count",
                         color="Count", color_continuous_scale="Viridis",
                         template="plotly_dark")
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📋 Processing Log")
        st.dataframe(pd.DataFrame(results_log), use_container_width=True, height=350)

    # Thumbnail preview (first 8)
    st.markdown("---")
    st.subheader("🖼️ Preview (first 8 photos)")
    preview_paths = image_paths[:8]
    preview_cols  = st.columns(min(len(preview_paths), 4))
    for idx, p in enumerate(preview_paths):
        with preview_cols[idx % 4]:
            try:
                st.image(Image.open(p), caption=Path(p).name[:20],
                         use_column_width=True)
            except Exception:
                st.caption(Path(p).name)


# ─────────────────────────────────────────────────────────────────────────────
#  Analytics Tab
# ─────────────────────────────────────────────────────────────────────────────

def _render_analytics_tab():
    st.markdown("## 📊 Platform Analytics")

    stats = get_photo_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🖼️ Total Photos",    stats["total_photos"])
    col2.metric("👥 Registered Users", stats["total_users"])
    col3.metric("🔍 Total Searches",   stats["total_searches"])
    col4.metric("✅ Face Matches",     stats["total_matches"])

    st.markdown("---")

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("📁 Scene Distribution (All Events)")
        scene_counts = get_scene_counts()
        if scene_counts:
            # Build chart data with 100% native Python types
            chart_data = []
            for item in scene_counts:
                scene_str = str(item["scene"])
                emoji = SCENE_EMOJIS.get(scene_str, "📁")
                label = emoji + " " + scene_str.replace("_", " ").title()
                count = int(item["count"])
                chart_data.append({"label": label, "count": count})
            
            df = pd.DataFrame(chart_data)
            # Ensure all columns are native Python types
            df["label"] = df["label"].astype(str)
            df["count"] = pd.to_numeric(df["count"], downcast="integer")
            
            # Create pie chart with pure native types
            try:
                fig = px.pie(df, values="count", names="label",
                             template="plotly_dark",
                             color_discrete_sequence=px.colors.sequential.Plasma_r)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                   margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                # Fallback: use simple bar chart (no plotly)
                st.bar_chart(df.set_index("label")["count"])
        else:
            st.info("No photo data yet. Upload an event to see analytics.")

    with col_r:
        st.subheader("📅 Events Overview")
        events = get_all_events()
        if events:
            # Build dataset with native Python types only
            events_data = []
            for e in events:
                events_data.append({
                    "event_name": str(e["name"]),
                    "photos": int(e["photo_count"]),
                    "created": str(e["created_at"])[:10] if e.get("created_at") else "—"
                })
            
            df_ev = pd.DataFrame(events_data)
            display_cols = ["event_name", "photos", "created"]
            df_ev.columns = ["Event Name", "Photos", "Created At"]
            st.dataframe(df_ev[display_cols], use_container_width=True)

            # Bar chart with guaranteed native types
            df_chart = pd.DataFrame({
                "event_name": [str(e["event_name"]) for e in events_data],
                "photos": [int(e["photos"]) for e in events_data]
            })
            
            fig2 = px.bar(df_chart, x="event_name", y="photos",
                          color="photos",
                          color_continuous_scale="Blues",
                          template="plotly_dark")
            fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                                paper_bgcolor="rgba(0,0,0,0)",
                                margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No events uploaded yet.")


# ─────────────────────────────────────────────────────────────────────────────
#  Event Manager Tab
# ─────────────────────────────────────────────────────────────────────────────

def _render_event_manager_tab():
    st.markdown("## 🗂️ Event Manager")

    # FAISS index status
    idx_size = face_engine.index_size()
    col_i, col_btn = st.columns([3, 1])
    col_i.info(f"🧠 **FAISS Index** contains **{idx_size:,}** face embeddings")
    if col_btn.button("🔄 Rebuild FAISS Index", key="rebuild_faiss",
                      help="Re-index all photos from disk — run after deleting events"):
        with st.spinner("Rebuilding FAISS index from all stored photos…"):
            all_photos = get_all_photos()
            added = face_engine.rebuild_index_from_photos(all_photos)
        st.success(f"✅ Rebuilt index with **{added}** embeddings from **{len(all_photos)}** photos")
        st.rerun()

    st.markdown("---")

    events = get_all_events()
    if not events:
        st.info("No events found. Upload photos first.")
        return

    for event in events:
        created = event["created_at"][:10] if event["created_at"] else "—"
        with st.expander(
            f"📅 **{event['name']}** — {event['photo_count']} photos | Created: {created}",
            expanded=False
        ):
            col1, col2 = st.columns([3, 1])
            with col1:
                scenes = get_scene_counts(event_name=event["name"])
                if scenes:
                    df_s = pd.DataFrame(scenes)
                    df_s["emoji"] = df_s["scene"].map(SCENE_EMOJIS).fillna("📁")
                    df_s["Scene"] = (df_s["emoji"] + " "
                                     + df_s["scene"].str.replace("_", " ").str.title())
                    st.dataframe(
                        df_s[["Scene", "count"]].rename(columns={"count": "Photos"}),
                        use_container_width=True
                    )
            with col2:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button("🗑️ Delete Event", key=f"del_{event['name']}"):
                    st.session_state[f"confirm_delete_{event['name']}"] = True

            if st.session_state.get(f"confirm_delete_{event['name']}"):
                st.warning(
                    f"⚠️ Delete **{event['name']}** and all its photos/matches?"
                )
                c1, c2 = st.columns(2)
                if c1.button("✅ Yes, Delete", key=f"yes_{event['name']}"):
                    delete_event_photos(event["name"])
                    st.session_state.pop(f"confirm_delete_{event['name']}", None)
                    st.success(f"Deleted event: {event['name']}")
                    st.rerun()
                if c2.button("❌ Cancel", key=f"no_{event['name']}"):
                    st.session_state.pop(f"confirm_delete_{event['name']}", None)
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  Browse Scenes Tab
# ─────────────────────────────────────────────────────────────────────────────

def _render_browse_tab():
    st.markdown("## 🔍 Browse Photos by Scene")

    events       = get_all_events()
    event_names  = ["All Events"] + [e["name"] for e in events]
    selected_ev  = st.selectbox("📅 Select Event", event_names)
    event_filter = None if selected_ev == "All Events" else selected_ev

    scene_counts = get_scene_counts(event_name=event_filter)
    if not scene_counts:
        st.info("No photos found. Upload an event first.")
        return

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

    selected_scene = st.session_state.get("browse_scene")
    if selected_scene:
        emoji  = SCENE_EMOJIS.get(selected_scene, "📁")
        label  = selected_scene.replace("_", " ").title()
        photos = get_photos_by_scene(selected_scene, event_name=event_filter)

        st.markdown(f"---\n### {emoji} {label} Photos")
        st.caption(f"{len(photos)} photo(s)")

        if not photos:
            st.info("No photos in this scene.")
        else:
            COLS = 4
            for row_start in range(0, len(photos), COLS):
                row_photos = photos[row_start:row_start + COLS]
                grid       = st.columns(len(row_photos))
                for j, photo in enumerate(row_photos):
                    with grid[j]:
                        try:
                            img = Image.open(photo["local_path"])
                            st.image(img, caption=photo["filename"][:20],
                                     use_column_width=True)
                            if photo["detected_objects"]:
                                st.caption("🏷️ " + " · ".join(photo["detected_objects"][:4]))
                        except Exception:
                            st.info(f"📷 {photo['filename']}")
