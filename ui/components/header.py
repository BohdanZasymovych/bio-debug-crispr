# ui/components/header.py
from __future__ import annotations

import streamlit as st


def render_header() -> bool:
    """
    Header row with title and RESET button.
    Returns True if RESET was clicked.
    """
    # Use spacing to push button to the far right
    col_title, col_space, col_btn = st.columns([6, 3, 1], vertical_alignment="center")

    with col_title:
        st.markdown("## 🧬 BIO-DEBUG: Agentic Gene Editor")

    with col_btn:
        reset_clicked = st.button("RESET", type="secondary")

    return reset_clicked
