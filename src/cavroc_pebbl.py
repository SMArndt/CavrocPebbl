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

# -- PAGE SETUP (must be first)
st.set_page_config(layout="wide")

# -- CUSTOM SIDEBAR STYLES
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #3C3C3B !important;
        color: #F2F1EF !important;
    }
    [data-testid="stSidebar"] .css-1v0mbdj {
        background-color: #3C3C3B !important;
    }
    .stRadio > div > label {
        font-size: 1.2rem;
    }
    [data-testid="stSidebar"] * {
        color: #F2F1EF !important;
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