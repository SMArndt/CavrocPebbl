"""Streamlit application entrypoint for Cavroc Pebbl."""
import streamlit as st
from pathlib import Path
from PIL import Image

from models import (
    Stopex, ProjectModel, SettingModel,
    FLACVersion, ModelConstructionModel
)
from ui.project import render_project_page
from ui.settings import render_settings_page
from ui.model_construction import render_model_construction_page
from ui.generate import render_generate_page

from logging_config import get_logger

logger = get_logger(__name__)
logger.info("Initializing CavrocPebbl UI module")

# Auto-switch to light theme if system prefers light; default to dark otherwise
st.markdown(
    """
    <style>
    @media (prefers-color-scheme: light) {
      :root {
        --background-color: #F2F1EF;
        --secondary-background-color: #F2F1EF;
        --text-color: #000000;
      }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -- CAVROC LOGO
logo_path = Path(__file__).parent.parent / "static" / "CavrocPebbl.jpg"
try:
    logo = Image.open(logo_path)
    st.sidebar.image(logo, width=120)
except FileNotFoundError:
    st.sidebar.warning("Logo not found: CavrocPebbl.jpg")

# -- SIDEBAR TITLE & NAVIGATION
st.sidebar.title("Cavroc Pebbl")
sections = ["Project", "Settings", "Model Construction", "Generate .f3dat"]
page = st.sidebar.radio("Navigation", sections)

# -- INITIALIZE STOPEX MODEL
if "stopex" not in st.session_state:
    st.session_state.stopex = Stopex(
        project=ProjectModel(project_name="My Project"),
        settings=SettingModel(
            file_format="stl", FLAC_version=FLACVersion.v7_0
        ),
        model_construction=ModelConstructionModel(),
        backfills=[], domains=[], faults=[],
        stress=None, stress_details=[], solving_parameter=None,
    )
stopex = st.session_state.stopex

# -- PAGE DISPATCH
if page == "Project":
    render_project_page(stopex)
elif page == "Settings":
    render_settings_page(stopex)
elif page == "Model Construction":
    render_model_construction_page(stopex)
else:
    render_generate_page(stopex)