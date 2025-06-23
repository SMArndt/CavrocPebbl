import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from stl import mesh

from models import ModelConstructionDetail
from ui.helpers import handle_geometry_section


def render_model_construction_page(stopex):
    """Render the Model Construction page with Stoping, Topo, Dev, AOI, Hist, and Summary."""
    tabs = st.tabs([
        "Stoping", "Topography", "Development",
        "Area of Interest", "Historical Mining", "Summary"
    ])
    farfield = stopex.settings.farfieldzonesize or 48
    stopex.model_construction.model_construction_detail.clear()

    # -- Stoping
    with tabs[0]:
        st.subheader("Stoping")
        stoping_detail = ModelConstructionDetail()
        handle_geometry_section("Stoping", "stoping", stoping_detail, farfield, "lightblue")
        stopex.model_construction.stoping_enabled = True
        stopex.model_construction.model_construction_detail.append("stoping")

    # -- Topography
    with tabs[1]:
        st.subheader("Topography")
        topo_detail = ModelConstructionDetail()
        stopex.model_construction.topo_enabled = st.checkbox(
            "Include Topography", value=stopex.model_construction.topo_enabled,
            key="topo_enabled"
        )
        if stopex.model_construction.topo_enabled:
            handle_geometry_section(
                "Topography", "topo", topo_detail, farfield, "lightgreen"
            )
            stopex.model_construction.model_construction_detail.append("topography")

    # -- Development
    with tabs[2]:
        st.subheader("Development")
        dev_detail = ModelConstructionDetail()
        stopex.model_construction.dev_enabled = st.checkbox(
            "Include Development", value=stopex.model_construction.dev_enabled,
            key="dev_enabled"
        )
        if stopex.model_construction.dev_enabled:
            handle_geometry_section(
                "Development", "dev", dev_detail, farfield, "lightyellow"
            )
            stopex.model_construction.model_construction_detail.append("development")

    # -- Area of Interest
    with tabs[3]:
        st.subheader("Area of Interest")
        aoi_detail = ModelConstructionDetail()
        stopex.model_construction.aoi_enabled = st.checkbox(
            "Include AOI", value=stopex.model_construction.aoi_enabled,
            key="aoi_enabled"
        )
        if stopex.model_construction.aoi_enabled:
            handle_geometry_section(
                "Area of Interest", "aoi", aoi_detail, farfield, "lightcoral"
            )
            stopex.model_construction.model_construction_detail.append("area_of_interest")

    # -- Historical Mining
    with tabs[4]:
        st.subheader("Historical Mining")
        hist_detail = ModelConstructionDetail()
        stopex.model_construction.hist_enabled = st.checkbox(
            "Include Historical Mining",
            value=stopex.model_construction.hist_enabled,
            key="hist_enabled"
        )
        if stopex.model_construction.hist_enabled:
            handle_geometry_section(
                "Historical Mining", "hist", hist_detail, farfield, "lightgray"
            )
            stopex.model_construction.model_construction_detail.append("historical")

    # -- Summary
    with tabs[5]:
        st.subheader("Summary")
        check, cross = "✅", "❌"
        summary_rows = []
        # Stoping always
        summary_rows.append({
            "Geometry": "Stoping",
            "Enabled": check,
            "Min Zone": stoping_detail.min_zonesize,
            "Init Zone": stoping_detail.init_zonesize,
            "Accuracy": stoping_detail.geometry_accuracy or "",
            "Densify": stoping_detail.zone_dens_dist,
            "File": stoping_detail.file or "",
        })
        # Optional geometries
        optional = [
            ("Topography", stopex.model_construction.topo_enabled, topo_detail),
            ("Development", stopex.model_construction.dev_enabled, dev_detail),
            ("AOI", stopex.model_construction.aoi_enabled, aoi_detail),
            ("Historical", stopex.model_construction.hist_enabled, hist_detail),
        ]
        for label, enabled, obj in optional:
            summary_rows.append({
                "Geometry": label,
                "Enabled": check if enabled else cross,
                "Min Zone": obj.min_zonesize,
                "Init Zone": obj.init_zonesize,
                "Accuracy": obj.geometry_accuracy or "",
                "Densify": obj.zone_dens_dist,
                "File": obj.file or "",
            })
        df = pd.DataFrame(summary_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        # 3D preview of combined meshes
        all_meshes = []
        colors = {
            "stoping": "lightblue", "topo": "lightgreen",
            "dev": "lightyellow", "aoi": "lightcoral",
            "hist": "lightgray",
        }
        file_keys = [
            ("stoping_path", "stoping"),
            ("topo_path", "topo"),
            ("dev_path", "dev"),
            ("aoi_path", "aoi"),
            ("hist_path", "hist"),
        ]
        vis = {}
        for i, (_, lbl) in enumerate(file_keys):
            vis[lbl] = st.checkbox(lbl.upper(), value=True, key=f"vis_{lbl}",
                                    help=f"Show {lbl}" ,
                                    )
        for key, lbl in file_keys:
            path = st.session_state.get(key)
            if path and vis.get(lbl):
                try:
                    mesh_obj = mesh.Mesh.from_file(path)
                    verts = np.reshape(mesh_obj.vectors, (-1, 3))
                    x, y, z = verts[:, 0], verts[:, 1], verts[:, 2]
                    idx = range(0, len(verts), 3)
                    all_meshes.append(
                        go.Mesh3d(
                            x=x, y=y, z=z,
                            i=list(idx), j=[i+1 for i in idx], k=[i+2 for i in idx],
                            opacity=0.5, color=colors[lbl]
                        )
                    )
                except Exception:
                    st.warning(f"Could not load {lbl}")
        if all_meshes:
            fig = go.Figure(data=all_meshes)
            fig.update_layout(
                title="Preview", margin=dict(l=0, r=0, t=30, b=0),
                scene=dict(aspectmode='data')
            )
            st.plotly_chart(fig, use_container_width=True)