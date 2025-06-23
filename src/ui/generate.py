import streamlit as st


def render_generate_page(stopex):
    """Render the Generate .f3dat page for JSON preview and download."""
    st.write(
        "This would serialize your `stopex` model to an .f3dat-compatible format."
    )
    if st.button("Preview Model JSON"):
        st.json(stopex.model_dump(exclude_unset=True))

    st.markdown("---")
    st.subheader("Live JSON Preview")
    st.json(stopex.model_dump(exclude_unset=True))

    st.download_button(
        "Download JSON Config",
        data=stopex.model_dump_json(indent=2),
        file_name="stopex_config.json",
        mime="application/json",
    )