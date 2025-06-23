import streamlit as st


def render_project_page(stopex):
    """Render the Project configuration page."""
    stopex.project.project_name = st.text_input(
        "Project Name", value=stopex.project.project_name
    )
    st.write("Optional: Company, User, etc. could go here")