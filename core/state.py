
from __future__ import annotations

import streamlit as st


def init_session_state() -> None:
    """
    Initialize all session_state keys used by the app.
    Keeps state management in one place (professional & predictable).
    """
    defaults = {
        "dna_raw": "",
        "dna_norm": "",
        "status": "idle",          # idle | running | done | error
        "events": [],              # list[dict]
        "result_json": None,       # dict | None
        "annotations": [],         # list[dict] for DNA visualizer
        "ui_locked": False,        # prevents editing while running
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_session_state() -> None:
    """
    Reset state for a clean demo run.
    """
    st.session_state.dna_raw = ""
    st.session_state.dna_norm = ""
    st.session_state.status = "idle"
    st.session_state.events = []
    st.session_state.result_json = None
    st.session_state.annotations = []
    st.session_state.ui_locked = False
