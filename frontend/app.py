"""
FaceFind — Main Streamlit Application Entry Point

Run with:  streamlit run app.py
"""

import streamlit as st
import sys
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# ── Load environment vars ──────────────────────────────────────────────────────
load_dotenv(".env.example")
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

# ── Custom CSS — Clean & Modern Dark Theme ────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --bg-dark: #0a0a0a;
        --bg-card: #111111;
        --accent-green: #22c55e;
        --accent-dark: #16a34a;
        --text-primary: #ffffff;
        --text-secondary: #d1d5db;
        --gray-dim: #6b7280;
        --border-color: #2d2d2d;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: var(--bg-dark) !important;
        color: var(--text-secondary) !important;
    }

    /* ── Main content area ── */
    .stMainBlockContainer {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }

    /* ── Headings ── */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
    }

    /* ── Hero header style ── */
    .facefind-header {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        padding: 2.5rem !important;
        border-radius: 8px !important;
        margin-bottom: 2rem !important;
        text-align: center !important;
    }

    .facefind-header h1 {
        color: var(--text-primary) !important;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
        margin-bottom: 0.5rem !important;
    }

    .facefind-header p {
        color: var(--text-secondary) !important;
        font-size: 1rem !important;
        margin: 0 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background-color: var(--accent-green) !important;
        color: var(--bg-dark) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    .stButton > button:hover {
        background-color: var(--accent-dark) !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid var(--border-color) !important;
        padding: 0.5rem 0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem !important;
        color: var(--gray-dim) !important;
        border-radius: 0 !important;
    }

    .stTabs [aria-selected="true"] {
        color: var(--accent-green) !important;
        border-bottom: 2px solid var(--accent-green) !important;
    }

    /* ── Form inputs ── */
    .stTextInput input,
    .stSelectbox [data-baseweb="select"],
    .stMultiSelect,
    .stSlider,
    textarea {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 6px !important;
    }

    .stTextInput input::placeholder,
    textarea::placeholder {
        color: var(--gray-dim) !important;
    }

    .stTextInput input:focus,
    .stSelectbox [data-baseweb="select"]:focus,
    textarea:focus {
        border-color: var(--accent-green) !important;
        color: var(--text-primary) !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 1.5rem !important;
    }

    /* ── Images ── */
    [data-testid="stImage"] img {
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: var(--bg-dark) !important;
        border-right: 1px solid var(--border-color) !important;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: var(--text-secondary) !important;
    }

    [data-testid="stSidebar"] [role="radiogroup"] {
        background-color: var(--bg-card) !important;
        border-radius: 6px !important;
        padding: 0.5rem !important;
    }

    /* ── Alerts & Messages ── */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 8px !important;
        border: 1px solid !important;
    }

    .stSuccess {
        background-color: rgba(34, 197, 94, 0.1) !important;
        border-color: var(--accent-green) !important;
    }

    .stError {
        background-color: rgba(239, 68, 68, 0.1) !important;
        border-color: #ef4444 !important;
    }

    .stWarning {
        background-color: rgba(245, 158, 11, 0.1) !important;
        border-color: #f59e0b !important;
    }

    .stInfo {
        background-color: rgba(59, 130, 246, 0.1) !important;
        border-color: #3b82f6 !important;
    }

    /* ── Progress bar ── */
    [data-testid="stProgress"] > div > div > div > div {
        background-color: var(--accent-green) !important;
    }

    /* ── Hide menu ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {
        width: 8px !important;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-card) !important;
    }

    ::-webkit-scrollbar-thumb {
        background: var(--accent-green) !important;
        border-radius: 4px !important;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-dark) !important;
    }

    /* ── Responsive ── */
    @media (max-width: 768px) {
        .facefind-header {
            padding: 1.5rem !important;
        }

        .facefind-header h1 {
            font-size: 1.75rem !important;
        }

        .stButton > button {
            padding: 0.5rem 1rem !important;
            font-size: 0.9rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1.5rem 0 1rem;'>
        <h2 style='color: #ffffff; margin: 0; font-size: 1.5rem; font-weight: 800;'>FaceFind</h2>
        <p style='color: #d1d5db; font-size: 0.85rem; margin: 0.3rem 0 0;'>AI Identity System</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    dashboard = st.radio(
        "Navigate",
        options=["🧑‍💻 User Dashboard", "🛠️ Admin Dashboard"],
        index=0,
        key="nav_radio"
    )

    st.markdown("---")
    st.markdown("""
    <div style='padding: 1rem 0; text-align: center;'>
        <p style='color: #22c55e; font-size: 0.75rem; margin: 0 0 0.8rem; font-weight: 700;'>System Overview</p>
        <p style='color: #d1d5db; font-size: 0.75rem; margin: 0; line-height: 1.6;'>
            Upload photos → AI processes → Users find matches
        </p>
    </div>
    """, unsafe_allow_html=True)


# ── Hero Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class='facefind-header'>
    <h1>Face Recognition System</h1>
    <p>Simple and secure identity detection</p>
</div>
""", unsafe_allow_html=True)

# ── Route to Dashboard ─────────────────────────────────────────────────────────
if "Admin" in dashboard:
    from pages.admin_dashboard import render_admin_dashboard
    render_admin_dashboard()
else:
    from pages.user_dashboard import render_user_dashboard
    render_user_dashboard()
