# app.py
from __future__ import annotations

import streamlit as st

from core.state import init_session_state, reset_session_state
from core.contracts import diagnostician_to_ui, therapist_to_ui
from core.events import get_events  # events are stored in session_state

from ui.styles import load_css
from ui.components.header import render_header
from ui.components.zone_a import render_zone_a
from ui.components.zone_b import render_zone_b
from ui.components.zone_c import render_zone_c

from demo.mock_pipeline import run_mock_pipeline


def main() -> None:
    st.set_page_config(
        page_title="CRISPR-OS: Agentic Gene Editor",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Init state + CSS
    init_session_state()
    load_css("ui/styles.css")

    # Header
    if render_header():
        reset_session_state()
        st.rerun()

    # Split top: Zone A / Zone B
    colA, colB = st.columns(2)

    with colA:
        dna_norm, run_clicked = render_zone_a(
            annotations=st.session_state.annotations,
            ui_locked=st.session_state.ui_locked,
        )

    # Placeholder variables (computed after run)
    diagnosis_summary = st.session_state.get("diagnosis_summary", None)
    therapy_ui = st.session_state.get("therapy_ui", None)
    safety_ui = st.session_state.get("safety_ui", None)

    with colB:
        render_zone_b(
            diagnosis_summary=diagnosis_summary,
            therapy_ui=therapy_ui,
            safety_ui=safety_ui,
        )

    # Run pipeline on click
    if run_clicked:
        # lock UI while running (simple)
        st.session_state.ui_locked = True
        st.session_state.status = "running"
        st.session_state.result_json = None

        # Clear prior derived UI fields
        st.session_state.annotations = []
        st.session_state.diagnosis_summary = None
        st.session_state.therapy_ui = None
        st.session_state.safety_ui = None

        # Run mock orchestrator (emits events)
        outputs = run_mock_pipeline(dna_norm)

        agent1 = outputs.get("agent1_diagnostician", {})
        agent2 = outputs.get("agent2_therapist", {})
        agent3 = outputs.get("agent3_safety", {})

        # Convert to UI-friendly shapes
        annotations, diag_summary = diagnostician_to_ui(agent1)
        therapy = therapist_to_ui(agent2)

        st.session_state.annotations = annotations
        st.session_state.diagnosis_summary = diag_summary
        st.session_state.therapy_ui = therapy
        st.session_state.safety_ui = agent3  # placeholder until we formalize Agent 3

        # Keep the full "final result" bundle for download/judges
        st.session_state.result_json = {
            "agent1_diagnostician": agent1,
            "agent2_therapist": agent2,
            "agent3_safety": agent3,
        }

        st.session_state.status = "done"
        st.session_state.ui_locked = False
        st.rerun()

    # Bottom: Zone C logs
    render_zone_c(
        events=get_events(),
        final_result=st.session_state.result_json,
    )


if __name__ == "__main__":
    main()
