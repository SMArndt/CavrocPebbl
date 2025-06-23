import streamlit as st

from enums import FLACVersion


def render_settings_page(stopex):
    """Render the global settings page."""
    st.subheader("Global Settings")
    col1, col2 = st.columns(2)
    with col1:
        stopex.settings.FLAC_version = st.selectbox(
            "FLAC3D Version",
            options=list(FLACVersion),
            format_func=lambda v: v.label,
            index=1 if stopex.settings.FLAC_version == FLACVersion.v7_0 else 0,
        )
        stopex.settings.file_format = st.selectbox(
            "Geometry File Format", ["stl", "dxf"], index=0
        )
    with col2:
        stopex.settings.inc_mXrap_result = st.checkbox(
            "Output for mXrap", value=stopex.settings.inc_mXrap_result
        )
        stopex.settings.GEM4D_output = st.checkbox(
            "Output for GEM4D", value=stopex.settings.GEM4D_output
        )
        stopex.settings.paraview = st.checkbox(
            "Output for ParaView", value=stopex.settings.paraview
        )

    with st.expander("Advanced Options"):
        stopex.settings.import_mesh = st.checkbox(
            "Do you want to import model mesh?",
            value=stopex.settings.import_mesh,
        )
        if stopex.settings.import_mesh:
            mesh_file = st.file_uploader(
                "Select mesh file (for local path capture only)",
                key="mesh_file_selector",
            )
            if mesh_file:
                stopex.settings.import_mesh_file = mesh_file.name

            mesh_path = st.text_input(
                "Local path to model mesh file",
                value=stopex.settings.import_mesh_file or "",
            )
            if mesh_path != stopex.settings.import_mesh_file:
                stopex.settings.import_mesh_file = mesh_path

        stopex.settings.import_map3D = st.checkbox(
            "Do you want to import geometries from a Map3D model?",
            value=stopex.settings.import_map3D,
        )
        if stopex.settings.import_map3D:
            map3d_file = st.file_uploader(
                "Select Map3D file (for local path capture only)",
                key="map3d_file_selector",
            )
            if map3d_file:
                stopex.settings.import_map3D_file = map3d_file.name

            map3d_path = st.text_input(
                "Local path to Map3D geometry file",
                value=stopex.settings.import_map3D_file or "",
            )
            if map3d_path != stopex.settings.import_map3D_file:
                stopex.settings.import_map3D_file = map3d_path

    st.markdown("---")
    st.subheader("Global Octree Meshing Parameters")
    stopex.settings.target_zones = st.number_input(
        "Target number of zones in the model (m)",
        value=stopex.settings.target_zones or 2000000,
        step=100000,
    )
    stopex.settings.farfieldzonesize = st.number_input(
        "Far Field Zone Size (m)",
        value=stopex.settings.farfieldzonesize or 48,
        step=1,
    )
    stopex.settings.model_boundary_offset = st.number_input(
        "Model Boundary Offset (m)",
        value=stopex.settings.model_boundary_offset or 400,
        step=10,
    )

    custom = st.checkbox(
        "Use custom zone size multiplier?",
        value=stopex.settings.zone_size_number is not None,
        key="custom_zone_toggle",
    )
    if custom:
        stopex.settings.zonesize_dropdown = None
        stopex.settings.zone_size_number = st.number_input(
            "Custom Zone Size Multiplier During Initial Iteration (m)",
            value=stopex.settings.zone_size_number or 6.0,
            step=0.5,
        )
    else:
        stopex.settings.zone_size_number = None
        stopex.settings.predefined_zonesize = True
        farfield = stopex.settings.farfieldzonesize or 48
        predefined = [farfield / (2 ** i) for i in range(6)]
        try:
            current = float(stopex.settings.zonesize_dropdown)
            ratio = farfield / current
            default_idx = int(round(ratio).bit_length() - 1)
        except (ValueError, TypeError):
            default_idx = 3
        dropdown_value = st.selectbox(
            "Choose predefined Zone Size Multiplier",
            predefined,
            index=default_idx,
        )
        stopex.settings.zonesize_dropdown = str(dropdown_value)