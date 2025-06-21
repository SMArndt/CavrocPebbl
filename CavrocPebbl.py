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
        topography = ModelConstructionDetail()
        stopex.model_construction.topo_enabled = st.checkbox("Include Topography", value=stopex.model_construction.topo_enabled, key="topo_enabled")
        if stopex.model_construction.topo_enabled:
            uploaded_topo = st.file_uploader("Topography Geometry File", type=["stl", "dxf"], key="topo_file")
            if uploaded_topo is not None:
                st.session_state.topo_file_shadow = uploaded_topo
                with tempfile.NamedTemporaryFile(delete=False, suffix=".stl", mode="wb") as tmp_file:
                    tmp_file.write(uploaded_topo.getbuffer())
                    st.session_state.topo_file_path = tmp_file.name

            topo_file = st.session_state.get("topo_file_shadow")
            if topo_file:
                topography.file = topo_file.name

            topo_path = st.text_input("Topography Geometry Filename", value=topography.file or "")
            if topo_path != topography.file:
                topography.file = topo_path

            farfield = stopex.settings.farfieldzonesize or 48
            predefined_multipliers = [farfield / (2 ** i) for i in range(6)]
            try:
                zone_min_val = topography.min_zonesize or farfield / 8
                zone_min_index = predefined_multipliers.index(zone_min_val)
            except (ValueError, TypeError):
                zone_min_index = 3
            topography.min_zonesize = st.selectbox("Minimum Zone Size", predefined_multipliers, index=zone_min_index, key="topo_zone_min")
            topography.geometry_accuracy = st.selectbox("Geometry Accuracy", ["Low", "Intermediate", "High"], index=1, key="topo_accuracy")
            topography.zone_dens_dist = st.number_input("Densification Distance (m)", value=topography.zone_dens_dist or 0.0, step=0.5, key="topo_densify")

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
            stopex.model_construction.model_construction_detail.append("topography")

        

    with tabs[2]:
        st.subheader("Development")
        development = ModelConstructionDetail()
        stopex.model_construction.dev_enabled = st.checkbox("Include Development", value=stopex.model_construction.dev_enabled, key="dev_enabled")
        if stopex.model_construction.dev_enabled:
            uploaded_dev = st.file_uploader("Development Geometry File", type=["stl", "dxf"], key="dev_file")
            if uploaded_dev is not None:
                st.session_state.dev_file_shadow = uploaded_dev
                with tempfile.NamedTemporaryFile(delete=False, suffix=".stl", mode="wb") as tmp_file:
                    tmp_file.write(uploaded_dev.getbuffer())
                    st.session_state.dev_file_path = tmp_file.name

            dev_file = st.session_state.get("dev_file_shadow")
            if dev_file:
                development.file = dev_file.name

            dev_path = st.text_input("Development Geometry Filename", value=development.file or "")
            if dev_path != development.file:
                development.file = dev_path
            farfield = stopex.settings.farfieldzonesize or 48
            predefined_multipliers = [farfield / (2 ** i) for i in range(6)]
            try:
                dev_zone_val = development.min_zonesize or farfield / 8
                dev_zone_index = predefined_multipliers.index(dev_zone_val)
                dev_init_val = development.init_zonesize or farfield / 8
                dev_init_index = predefined_multipliers.index(dev_init_val)
            except (ValueError, TypeError):
                dev_zone_index = 3
                dev_init_index = 3
            development.min_zonesize = st.selectbox("Minimum Zone Size", predefined_multipliers, index=dev_zone_index, key="dev_zone_min")
            development.init_zonesize = st.selectbox("Initial Zone Size", predefined_multipliers, index=dev_init_index, key="dev_zone_init")
            development.geometry_accuracy = st.selectbox("Geometry Accuracy", ["Low", "Intermediate", "High"], index=1, key="dev_accuracy")
            development.zone_dens_dist = st.number_input("Densification Distance (m)", value=development.zone_dens_dist or 0.0, step=0.5, key="dev_densify")

            stopex.model_construction.model_construction_detail.append("development")

            # -- STL Preview for Development
            if dev_file and dev_file.name.endswith(".stl"):
                tmp_file_path = st.session_state.get("dev_file_path")
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
                        color='lightyellow'
                    )])
                    fig.update_layout(
                        title="Development Geometry Preview",
                        margin=dict(l=0, r=0, t=30, b=0),
                        scene=dict(aspectmode='data')
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to preview STL: {e}")

    with tabs[3]:
        st.subheader("Area of Interest")
        aoi = ModelConstructionDetail()
        stopex.model_construction.aoi_enabled = st.checkbox("Include AOI", value=stopex.model_construction.aoi_enabled, key="aoi_enabled")
        if stopex.model_construction.aoi_enabled:
            uploaded_aoi = st.file_uploader("AOI Geometry File", type=["stl", "dxf"], key="aoi_file")
            if uploaded_aoi is not None:
                st.session_state.aoi_file_shadow = uploaded_aoi
                with tempfile.NamedTemporaryFile(delete=False, suffix=".stl", mode="wb") as tmp_file:
                    tmp_file.write(uploaded_aoi.getbuffer())
                    st.session_state.aoi_file_path = tmp_file.name

            aoi_file = st.session_state.get("aoi_file_shadow")
            if aoi_file:
                aoi.file = aoi_file.name

            aoi_path = st.text_input("AOI Geometry Filename", value=aoi.file or "")
            if aoi_path != aoi.file:
                aoi.file = aoi_path

            farfield = stopex.settings.farfieldzonesize or 48
            predefined_multipliers = [farfield / (2 ** i) for i in range(6)]
            try:
                aoi_zone_val = aoi.min_zonesize or farfield / 8
                aoi_zone_index = predefined_multipliers.index(aoi_zone_val)
                aoi_init_val = aoi.init_zonesize or farfield / 8
                aoi_init_index = predefined_multipliers.index(aoi_init_val)
            except (ValueError, TypeError):
                aoi_zone_index = 3
                aoi_init_index = 3
            aoi.min_zonesize = st.selectbox("Minimum Zone Size", predefined_multipliers, index=aoi_zone_index, key="aoi_zone_min")
            aoi.init_zonesize = st.selectbox("Initial Zone Size", predefined_multipliers, index=aoi_init_index, key="aoi_zone_init")
            aoi.geometry_accuracy = st.selectbox("Geometry Accuracy", ["Low", "Intermediate", "High"], index=1, key="aoi_accuracy")
            aoi.zone_dens_dist = st.number_input("Densification Distance (m)", value=aoi.zone_dens_dist or 0.0, step=0.5, key="aoi_densify")

            # -- STL Preview for AOI
            if aoi_file and aoi_file.name.endswith(".stl"):
                tmp_file_path = st.session_state.get("aoi_file_path")
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
                        color='lightcoral'
                    )])
                    fig.update_layout(
                        title="AOI Geometry Preview",
                        margin=dict(l=0, r=0, t=30, b=0),
                        scene=dict(aspectmode='data')
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to preview STL: {e}")

            stopex.model_construction.model_construction_detail.append("aoi")

    with tabs[4]:
        st.subheader("Historical Mining")
        hist = ModelConstructionDetail()
        stopex.model_construction.hist_enabled = st.checkbox("Include Historical Mining", value=stopex.model_construction.hist_enabled, key="hist_enabled")
        if stopex.model_construction.hist_enabled:
            uploaded_hist = st.file_uploader("Historical Mining Geometry File", type=["stl", "dxf"], key="hist_file")
            if uploaded_hist is not None:
                st.session_state.hist_file_shadow = uploaded_hist
                with tempfile.NamedTemporaryFile(delete=False, suffix=".stl", mode="wb") as tmp_file:
                    tmp_file.write(uploaded_hist.getbuffer())
                    st.session_state.hist_file_path = tmp_file.name

            hist_file = st.session_state.get("hist_file_shadow")
            if hist_file:
                hist.file = hist_file.name

            hist_path = st.text_input("Historical Mining Geometry Filename", value=hist.file or "", key="hist_filename")
            if hist_path != hist.file:
                hist.file = hist_path

            farfield = stopex.settings.farfieldzonesize or 48
            predefined_multipliers = [farfield / (2 ** i) for i in range(6)]
            try:
                hist_zone_val = hist.min_zonesize or farfield / 8
                hist_zone_index = predefined_multipliers.index(hist_zone_val)
                hist_init_val = hist.init_zonesize or farfield / 8
                hist_init_index = predefined_multipliers.index(hist_init_val)
            except (ValueError, TypeError):
                hist_zone_index = 3
                hist_init_index = 3
            hist.min_zonesize = st.selectbox("Minimum Zone Size", predefined_multipliers, index=hist_zone_index, key="hist_zone_min_select")
            hist.init_zonesize = st.selectbox("Initial Zone Size", predefined_multipliers, index=hist_init_index, key="hist_zone_init")
            hist.geometry_accuracy = st.selectbox("Geometry Accuracy", ["Low", "Intermediate", "High"], index=1, key="hist_accuracy_select")
            hist.zone_dens_dist = st.number_input("Densification Distance (m)", value=hist.zone_dens_dist or 0.0, step=0.5, key="hist_densify")

            if hist_file and hist_file.name.endswith(".stl"):
                tmp_file_path = st.session_state.get("hist_file_path")
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
                        color='lightgray'
                    )])
                    fig.update_layout(
                        title="Historical Mining Geometry Preview",
                        margin=dict(l=0, r=0, t=30, b=0),
                        scene=dict(aspectmode='data')
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to preview STL: {e}")

            stopex.model_construction.model_construction_detail.append("historical")
            

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
