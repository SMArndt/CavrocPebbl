# Full Streamlit App Using Stopex Pydantic Model

import streamlit as st
from models import Stopex, ProjectModel, SettingModel, FLACVersion, ModelConstructionModel, ModelConstructionDetail
from enums import FLACVersion
from PIL import Image
from pathlib import Path
import plotly.graph_objects as go
from stl import mesh
import tempfile
import numpy as np

# -- PAGE SETUP (MUST BE FIRST)
st.set_page_config(layout="wide")

# -- CUSTOM STYLES
st.markdown("""
    <style>
    /* Sidebar styling only */
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
""", unsafe_allow_html=True)

# -- CAVROC LOGO (resize and render at top of sidebar)
logo_path = Path(__file__).parent / "CavrocPebbl.jpg"
try:
    logo = Image.open(logo_path)
    st.sidebar.image(logo, width=120)
except FileNotFoundError:
    st.sidebar.warning("Logo not found: CavrocPebbl.jpg")

# -- TITLE
st.sidebar.title("Cavroc Pebbl")

# -- SIDEBAR NAVIGATION
sections = [
    "Project",
    "Settings",
    "Model Construction",
    "Generate .f3dat"
]
page = st.sidebar.radio("Navigation", sections)

# -- INITIALIZE STOPEX MODEL
if "stopex" not in st.session_state:
    
    st.session_state.stopex = Stopex(
        project=ProjectModel(project_name="My Project"),
        model_construction=ModelConstructionModel(),
        settings=SettingModel(file_format="stl", FLAC_version=FLACVersion.v7_0),
        backfills=[], domains=[], faults=[], stress=None, stress_details=[], solving_parameter=None
    )

stopex = st.session_state.stopex

# -- PROJECT PAGE
if page == "Project":
    
    stopex.project.project_name = st.text_input("Project Name", value=stopex.project.project_name)
    st.write("Optional: Company, User, etc. could go here")

# -- SETTINGS PAGE
elif page == "Settings":
    
    st.subheader("Global Settings")
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
        stopex.settings.inc_mXrap_result = st.checkbox("Output for mXrap", value=stopex.settings.inc_mXrap_result)
        stopex.settings.GEM4D_output = st.checkbox("Output for GEM4D", value=stopex.settings.GEM4D_output)
        stopex.settings.paraview = st.checkbox("Output for ParaView", value=stopex.settings.paraview)

    with st.expander("Advanced Options"):
        stopex.settings.import_mesh = st.checkbox("Do you want to import model mesh?", value=stopex.settings.import_mesh)
        if stopex.settings.import_mesh:
            mesh_file = st.file_uploader("Select mesh file (for local path capture only)", key="mesh_file_selector")
            if mesh_file:
                stopex.settings.import_mesh_file = mesh_file.name

            mesh_path = st.text_input("Local path to model mesh file", value=stopex.settings.import_mesh_file or "")
            if mesh_path != stopex.settings.import_mesh_file:
                stopex.settings.import_mesh_file = mesh_path

        stopex.settings.import_map3D = st.checkbox("Do you want to import geometries from a Map3D model?", value=stopex.settings.import_map3D)
        if stopex.settings.import_map3D:
            map3d_file = st.file_uploader("Select Map3D file (for local path capture only)", key="map3d_file_selector")
            if map3d_file:
                stopex.settings.import_map3D_file = map3d_file.name

            map3d_path = st.text_input("Local path to Map3D geometry file", value=stopex.settings.import_map3D_file or "")
            if map3d_path != stopex.settings.import_map3D_file:
                stopex.settings.import_map3D_file = map3d_path

    st.markdown("---")
    st.subheader("Global Octree Meshing Parameters")
    stopex.settings.target_zones = st.number_input("Target number of zones in the model (m)", value=stopex.settings.target_zones or 2000000, step=100000)
    stopex.settings.farfieldzonesize = st.number_input("Far Field Zone Size (m)", value=stopex.settings.farfieldzonesize or 48, step=1)
    stopex.settings.model_boundary_offset = st.number_input("Model Boundary Offset (m)", value=stopex.settings.model_boundary_offset or 400, step=10)

    custom_zone = st.checkbox("Use custom zone size multiplier?", value=stopex.settings.zone_size_number is not None, key="custom_zone_toggle")
    if custom_zone:
        stopex.settings.zonesize_dropdown = None
        stopex.settings.zone_size_number = st.number_input(
            "Custom Zone Size Multiplier During Initial Iteration (m)",
            value=stopex.settings.zone_size_number or 6.0,
            step=0.5
        )
    else:
        stopex.settings.zone_size_number = None
        stopex.settings.predefined_zonesize = True
        farfield = stopex.settings.farfieldzonesize or 48
        predefined_multipliers = [farfield / (2 ** i) for i in range(6)]
        try:
            current_value = float(stopex.settings.zonesize_dropdown)
            ratio = farfield / current_value
            default_index = int(round(ratio).bit_length() - 1)
        except (ValueError, TypeError):
            default_index = 3
        dropdown_value = st.selectbox(
            "Choose predefined Zone Size Multiplier",
            predefined_multipliers,
            index=default_index
        )
        stopex.settings.zonesize_dropdown = str(dropdown_value)

elif page == "Model Construction":
    
    tabs = st.tabs(["Stoping", "Topography", "Development", "Area of Interest", "Historical Mining"])

    with tabs[0]:
        
        st.subheader("Stoping")
        stoping = ModelConstructionDetail()
        uploaded_file = st.file_uploader("Select Stoping Geometry File (for local path capture only)", type=["stl", "dxf"], key="stoping_file")
        if uploaded_file is not None:
            st.session_state.stoping_file_shadow = uploaded_file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".stl", mode="wb") as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                st.session_state.stoping_file_path = tmp_file.name

        stoping_file = st.session_state.get("stoping_file_shadow")
        if stoping_file:
            stoping.file = stoping_file.name

        stoping_path = st.text_input("Stoping Geometry Filename", value=stoping.file or "")
        if stoping_path != stoping.file:
            stoping.file = stoping_path
        farfield = stopex.settings.farfieldzonesize or 48
        predefined_multipliers = [farfield / (2 ** i) for i in range(6)]
        try:
            min_val = stoping.min_zonesize or farfield / 8
            init_val = stoping.init_zonesize or farfield / 8
            min_index = predefined_multipliers.index(min_val)
            init_index = predefined_multipliers.index(init_val)
        except (ValueError, TypeError):
            min_index = init_index = 3

        stoping.min_zonesize = st.selectbox("Minimum Zone Size", predefined_multipliers, index=min_index, key="stoping_zone_min")
        stoping.init_zonesize = st.selectbox("Initial Zone Size", predefined_multipliers, index=init_index, key="stoping_zone_init")
        stoping.geometry_accuracy = st.selectbox("Geometry Accuracy", ["Low", "Intermediate", "High"], index=1, key="stoping_accuracy")
        stoping.zone_dens_dist = st.number_input("Densification Distance (m)", value=stoping.zone_dens_dist or 0.0, step=0.5, key="stoping_densify")

        stopex.model_construction.stoping_enabled = True
        stopex.model_construction.model_construction_detail = ["stoping"]
                

        # -- STL Preview for Stoping
        if stoping_file and stoping_file.name.endswith(".stl"):
            tmp_file_path = st.session_state.get("stoping_file_path")

            try:
                stl_mesh = mesh.Mesh.from_file(tmp_file_path)
                vertices = np.reshape(stl_mesh.vectors, (-1, 3))
                x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
                i = np.arange(0, len(vertices), 3)
                j = i + 1
                k = i + 2

                fig = go.Figure(data=[go.Mesh3d(
                    x=x, y=y, z=z,
                    i=i, j=j, k=k,
                    opacity=0.8,
                    color='lightblue'
                )])
                fig.update_layout(
                    title="Stoping Geometry Preview",
                    margin=dict(l=0, r=0, t=30, b=0),
                    scene=dict(aspectmode='data')
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to preview STL: {e}")
    with tabs[1]:
        st.subheader("Topography")
        stopex.model_construction.topo_enabled = st.checkbox("Include Topography", value=stopex.model_construction.topo_enabled, key="topo_enabled")
        if stopex.model_construction.topo_enabled:
            uploaded_topo = st.file_uploader("Topography Geometry File", type=["stl", "dxf"], key="topo_file")
            if uploaded_topo is not None:
                st.session_state.topo_file_shadow = uploaded_topo
                with tempfile.NamedTemporaryFile(delete=False, suffix=".stl", mode="wb") as tmp_file:
                    tmp_file.write(uploaded_topo.getbuffer())
                    st.session_state.topo_file_path = tmp_file.name

            topo_file = st.session_state.get("topo_file_shadow")
            topo_path = topo_file.name if topo_file else ""
            topo_path = st.text_input("Topography Geometry Filename", value=topo_path)

            farfield = stopex.settings.farfieldzonesize or 48
            predefined_multipliers = [farfield / (2 ** i) for i in range(6)]
            zone_min = st.selectbox("Minimum Zone Size", predefined_multipliers, index=3, key="topo_zone_min")
            accuracy = st.selectbox("Geometry Accuracy", ["Low", "Intermediate", "High"], index=1, key="topo_accuracy")
            densify = st.number_input("Densification Distance (m)", value=0.0, step=0.5, key="topo_densify")

            # -- STL Preview for Topography
            if topo_file and topo_file.name.endswith(".stl"):
                tmp_file_path = st.session_state.get("topo_file_path")
                try:
                    stl_mesh = mesh.Mesh.from_file(tmp_file_path)
                    vertices = np.reshape(stl_mesh.vectors, (-1, 3))
                    x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
                    i = np.arange(0, len(vertices), 3)
                    j = i + 1
                    k = i + 2

                    fig = go.Figure(data=[go.Mesh3d(
                        x=x, y=y, z=z,
                        i=i, j=j, k=k,
                        opacity=0.8,
                        color='lightgreen'
                    )])
                    fig.update_layout(
                        title="Topography Geometry Preview",
                        margin=dict(l=0, r=0, t=30, b=0),
                        scene=dict(aspectmode='data')
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to preview STL: {e}")
            stopex.topography.geometry = st.file_uploader("Topography Geometry File", type=["stl", "dxf"], key="topo_file")
            stopex.topography.zone_size_min = st.number_input("Minimum Zone Size", value=stopex.topography.zone_size_min or 6, step=1, key="topo_zone_min")
            stopex.topography.geometry_accuracy = st.selectbox("Geometry Accuracy", ["Low", "Intermediate", "High"], index=1, key="topo_accuracy")
            stopex.topography.densify_distance = st.number_input("Densification Distance (m)", value=stopex.topography.densify_distance or 0.0, step=0.5, key="topo_densify")

    with tabs[2]:
        st.subheader("Development")
        stopex.development.enabled = st.checkbox("Include Development", value=stopex.development.enabled, key="dev_enabled")
        if stopex.development.enabled:
            stopex.development.geometry = st.file_uploader("Development Geometry File", type=["stl", "dxf"], key="dev_file")
            stopex.development.zone_size_min = st.number_input("Minimum Zone Size", value=stopex.development.zone_size_min or 6, step=1, key="dev_zone_min")
            stopex.development.geometry_accuracy = st.selectbox("Geometry Accuracy", ["Low", "Intermediate", "High"], index=1, key="dev_accuracy")
            stopex.development.densify_distance = st.number_input("Densification Distance (m)", value=stopex.development.densify_distance or 0.0, step=0.5, key="dev_densify")

    with tabs[3]:
        st.subheader("Area of Interest")
        stopex.aoi.enabled = st.checkbox("Include AOI", value=stopex.aoi.enabled, key="aoi_enabled")
        if stopex.aoi.enabled:
            stopex.aoi.geometry = st.file_uploader("AOI Geometry File", type=["stl", "dxf"], key="aoi_file")
            stopex.aoi.zone_size_min = st.number_input("Minimum Zone Size", value=stopex.aoi.zone_size_min or 6, step=1, key="aoi_zone_min")
            stopex.aoi.geometry_accuracy = st.selectbox("Geometry Accuracy", ["Low", "Intermediate", "High"], index=1, key="aoi_accuracy")
            stopex.aoi.densify_distance = st.number_input("Densification Distance (m)", value=stopex.aoi.densify_distance or 0.0, step=0.5, key="aoi_densify")

    with tabs[4]:
        st.subheader("Historical Mining")
        stopex.historical.enabled = st.checkbox("Include Historical Mining", value=stopex.historical.enabled, key="hist_enabled")
        if stopex.historical.enabled:
            stopex.historical.geometry = st.file_uploader("Historical Mining Geometry File", type=["stl", "dxf"], key="hist_file")
            stopex.historical.zone_size_min = st.number_input("Minimum Zone Size", value=stopex.historical.zone_size_min or 6, step=1, key="hist_zone_min")
            stopex.historical.geometry_accuracy = st.selectbox("Geometry Accuracy", ["Low", "Intermediate", "High"], index=1, key="hist_accuracy")
            stopex.historical.densify_distance = st.number_input("Densification Distance (m)", value=stopex.historical.densify_distance or 0.0, step=0.5, key="hist_densify")

elif page == "Generate .f3dat":
    
    st.write("This would serialize your `stopex` model to an .f3dat-compatible format.")

    if st.button("Preview Model JSON"):
        st.json(stopex.model_dump(exclude_unset=True))

    st.markdown("---")
    st.subheader("Live JSON Preview")
    st.json(stopex.model_dump(exclude_unset=True))

    st.download_button(
        "Download JSON Config",
        data=stopex.model_dump_json(indent=2),
        file_name="stopex_config.json",
        mime="application/json"
    )
