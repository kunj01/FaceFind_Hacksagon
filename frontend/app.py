"""
FaceFind — Main Streamlit Application Entry Point

Run with:  streamlit run app.py
"""

import streamlit as st
import sys
import os
from pathlib import Path



from dotenv import load_dotenv

# ── Load environment vars ──────────────────────────────────────────────────────
load_dotenv(".env.example")  # falls back gracefully if .env not present
load_dotenv(".env")

# ── Ensure project root is on path ────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FaceFind — AI Photo Discovery",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Initialize DB on startup ──────────────────────────────────────────────────
from database.db import init_db

@st.cache_resource
def _initialize_db():
    init_db()

_initialize_db()

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide default Streamlit menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Sidebar branding */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F0C29, #302B63, #24243E);
    }

    /* Header gradient */
    .facefind-header {
        background: linear-gradient(135deg, #6C63FF 0%, #3B82F6 50%, #8B5CF6 100%);
        padding: 2rem 2rem 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .facefind-header h1 {
        color: white;
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .facefind-header p {
        color: rgba(255,255,255,0.85);
        font-size: 1.1rem;
        margin: 0.5rem 0 0;
    }

    /* Card styling */
    .stMetric {
        background: rgba(108,99,255,0.1);
        border: 1px solid rgba(108,99,255,0.3);
        border-radius: 12px;
        padding: 1rem;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 600;
    }

    /* Buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6C63FF, #8B5CF6);
        border: none;
        border-radius: 10px;
        font-weight: 700;
        font-size: 1rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 15px rgba(108, 99, 255, 0.4);
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(108, 99, 255, 0.6);
    }

    /* Image grid */
    [data-testid="stImage"] {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Download button */
    .stDownloadButton > button {
        border-radius: 8px;
        font-size: 0.85rem;
        padding: 0.35rem 0.75rem;
        background: rgba(16,185,129,0.15);
        border-color: rgba(16,185,129,0.5);
        color: #10B981;
        transition: all 0.2s;
    }
    .stDownloadButton > button:hover {
        background: #10B981;
        color: white;
    }

    /* Expander */
    [data-testid="stExpander"] {
        border: 1px solid rgba(108,99,255,0.2);
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1.5rem 0 0.5rem;'>
        <span style='font-size:3rem;'>🔍</span>
        <h2 style='color:#6C63FF; margin:0; font-size:1.6rem; font-weight:800;'>FaceFind</h2>
        <p style='color:#888; font-size:0.8rem; margin:0.2rem 0 0;'>AI Photo Discovery Platform</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    dashboard = st.radio(
        "🧭 Navigate to",
        options=["🧑‍💻 User Dashboard", "🛠️ Admin Dashboard"],
        key="nav_radio"
    )

    st.markdown("---")
    st.markdown("""
    <div style='color:#555; font-size:0.78rem; text-align:center; padding-top:0.5rem;'>
        <b style='color:#6C63FF;'>How It Works</b><br><br>
        1️⃣ Admin uploads Google Drive link<br>
        2️⃣ AI classifies scenes & extracts faces<br>
        3️⃣ User uploads selfie → finds their photos<br><br>
        <b>Powered by</b><br>
        🤖 CLIP + YOLOv8 | ArcFace + FAISS<br>
        🗄️ DuckDB | 🎈 Streamlit
    </div>
    """, unsafe_allow_html=True)

# ── Hero Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class='facefind-header'>
    <h1>🔍 FaceFind</h1>
    <p>AI-Powered Smart Photo Discovery · Scene Understanding · Face Recognition</p>
</div>
""", unsafe_allow_html=True)

# ── Route to Dashboard ─────────────────────────────────────────────────────────
if "Admin" in dashboard:
    from pages.admin_dashboard import render_admin_dashboard
    render_admin_dashboard()
else:
    from pages.user_dashboard import render_user_dashboard
    render_user_dashboard()
