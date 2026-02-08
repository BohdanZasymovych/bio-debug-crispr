# ui/styles.py
from __future__ import annotations

from pathlib import Path
import streamlit as st


def load_css(css_path: str | Path) -> None:
    """
    Inject CSS from a file into Streamlit.
    """
    p = Path(css_path)
    if not p.exists():
        st.warning(f"CSS file not found: {p}")
        return

    css = p.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
