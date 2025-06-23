import tempfile
from typing import Tuple

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from stl import mesh

__all__ = [
    'ACCURACY_OPTIONS',
    'select_zone_sizes',
    'handle_geometry_section',
]

# Options and parameters
ACCURACY_OPTIONS = ["Low", "Intermediate", "High"]
_NUM_ZONES = 6

def select_zone_sizes(
    label: str,
    current_min: float,
    current_init: float,
    farfield: float,
    key_prefix: str,
) -> Tuple[float, float]:
    """
    Render two selectboxes for minimum and initial zone sizes based on octree multipliers.
    Returns the selected (min_zonesize, init_zonesize).
    """
    multipliers = [farfield / (2 ** i) for i in range(_NUM_ZONES)]
    try:
        min_idx = multipliers.index(current_min)
    except (ValueError, TypeError):
        min_idx = _NUM_ZONES // 2
    try:
        init_idx = multipliers.index(current_init)
    except (ValueError, TypeError):
        init_idx = _NUM_ZONES // 2
    min_zone = st.selectbox(
        f"{label} Minimum Zone Size", multipliers, index=min_idx,
        key=f"{key_prefix}_zone_min"
    )
    init_zone = st.selectbox(
        f"{label} Initial Zone Size", multipliers, index=init_idx,
        key=f"{key_prefix}_zone_init"
    )
    return min_zone, init_zone

def handle_geometry_section(
    label: str,
    key: str,
    detail: object,
    farfield: float,
    color: str,
) -> None:
    """
    Unified handler for a geometry section: file upload, filename input,
    zone-size selection, accuracy, densification, and STL preview.
    Modifies the given detail object in place.
    """
    uploaded = st.file_uploader(
        f"{label} Geometry File", type=["stl", "dxf"], key=f"{key}_file"
    )
    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".stl", mode="wb") as tmp:
            tmp.write(uploaded.getbuffer())
            st.session_state[f"{key}_path"] = tmp.name
        st.session_state[f"{key}_shadow"] = uploaded
    shadow = st.session_state.get(f"{key}_shadow")
    if shadow:
        detail.file = shadow.name
    # Filename text input override
    detail.file = st.text_input(
        f"{label} Geometry Filename", value=detail.file or "",
        key=f"{key}_path_input"
    )
    # Zone size controls
    detail.min_zonesize, detail.init_zonesize = select_zone_sizes(
        label, detail.min_zonesize or 0.0,
        detail.init_zonesize or 0.0,
        farfield, key
    )
    # Accuracy and densification
    detail.geometry_accuracy = st.selectbox(
        "Geometry Accuracy", ACCURACY_OPTIONS,
        index=ACCURACY_OPTIONS.index(detail.geometry_accuracy or "Intermediate"),
        key=f"{key}_accuracy"
    )
    detail.zone_dens_dist = st.number_input(
        "Densification Distance (m)",
        value=detail.zone_dens_dist or 0.0,
        step=0.5,
        key=f"{key}_densify"
    )
    # STL preview if available
    path = st.session_state.get(f"{key}_path")
    if detail.file and detail.file.endswith(".stl") and path:
        try:
            stl_mesh = mesh.Mesh.from_file(path)
            vertices = np.reshape(stl_mesh.vectors, (-1, 3))
            x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
            idx = range(0, len(vertices), 3)
            i, j, k = list(idx), [x + 1 for x in idx], [x + 2 for x in idx]
            fig = go.Figure(data=[
                go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k,
                           opacity=0.8, color=color)
            ])
            fig.update_layout(
                title=f"{label} Geometry Preview", margin=dict(l=0, r=0, t=30, b=0),
                scene=dict(aspectmode='data')
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to preview STL: {e}")