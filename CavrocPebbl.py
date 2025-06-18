# Full Streamlit App Using Stopex Pydantic Model

import streamlit as st
from models import Stopex, ProjectModel, SettingModel, FLACVersion
from enums import FLACVersion
from PIL import Image
from pathlib import Path

# -- PAGE SETUP (MUST BE FIRST)
st.set_page_config(layout="wide")

# -- CUSTOM STYLES
st.markdown("""
    <style>
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #3C3C3B;
    }
    [data-testid="stSidebar"] .css-1v0mbdj {
        background-color: #3C3C3B;
    }
    /* Main area */
    .main .block-container {
        background-color: #F2F1EF;
        padding-top: 4rem;
    }
    /* Header bar and separators */
    .css-1avcm0n, .stMarkdown h1, .stMarkdown h2 {
        color: #3C3C3B;
        border-bottom: 2px solid #707070;
    }
    </style>
""", unsafe_allow_html=True)

# -- CAVROC LOGO (resize and render at top of sidebar)
logo_path = Path(__file__).parent / "CavrocPebbl.jpg"
try:
    logo = Image.open(logo_path)
    st.sidebar.image(logo, width=120)
except FileNotFoundError:
    st.sidebar.warning("Logo not found: CavrocPebbl.jpg")

# -- TITLE
st.title("StopeX Input Generator")

# -- SIDEBAR NAVIGATION
sections = [
    "Project",
    "Settings",
    "Generate .f3dat"
]
page = st.sidebar.radio("Navigation", sections)

# -- INITIALIZE STOPEX MODEL
if "stopex" not in st.session_state:
    st.session_state.stopex = Stopex(
        project=ProjectModel(project_name="My Project"),
        settings=SettingModel(file_format="stl", FLAC_version=FLACVersion.v7_0),
        backfills=[], domains=[], faults=[], stress=None, stress_details=[], solving_parameter=None
    )

stopex = st.session_state.stopex

# -- PROJECT PAGE
if page == "Project":
    st.header("Project Setup")
    stopex.project.project_name = st.text_input("Project Name", value=stopex.project.project_name)
    st.write("Optional: Company, User, etc. could go here")

# -- SETTINGS PAGE
elif page == "Settings":
    st.header("Global Settings")
    col1, col2 = st.columns(2)
    with col1:
        stopex.settings.FLAC_version = st.selectbox(
            "FLAC3D Version",
            options=list(FLACVersion),
            format_func=lambda v: v.label,
            index=1 if stopex.settings.FLAC_version == FLACVersion.v7_0 else 0
        )
        stopex.settings.file_format = st.selectbox("Geometry File Format", ["stl", "dxf"], index=0)
    with col2:
        stopex.settings.import_mesh = st.checkbox("Import Mesh", value=stopex.settings.import_mesh)
        stopex.settings.GEM4D_output = st.checkbox("Output for GEM4D", value=stopex.settings.GEM4D_output)
        stopex.settings.paraview = st.checkbox("Output for ParaView", value=stopex.settings.paraview)

# -- GENERATE PAGE
elif page == "Generate .f3dat":
    st.header("Generate .f3dat File")
    st.write("This would serialize your `stopex` model to an .f3dat-compatible format.")

    if st.button("Preview Model JSON"):
        st.json(stopex.model_dump())

    st.download_button(
        "Download JSON Config",
        data=stopex.model_dump_json(indent=2),
        file_name="stopex_config.json",
        mime="application/json"
    )
