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


from pipeline import run_full_pipeline
from utils.utils import get_api_key
from utils.streamlit_logger import enable_streamlit_logging
import html


def _update_live_logs():
    """Update the live log placeholder with current logs."""
    if hasattr(st.session_state, 'live_log_placeholder') and st.session_state.live_log_placeholder is not None:
        logs = st.session_state.get("agent_logs", [])
        if logs:
            lines = [f'<p style="margin: 2px 0; color: #e5e7eb;">{html.escape(log)}</p>' for log in logs[-50:]]
            # Use img onerror hack to trigger scroll since script tags might be stripped/delayed
            html_content = f'''
                <div class="log-box-live" id="live-logs">{"".join(lines)}</div>
                <img src="x" style="display:none" onerror="var el=document.getElementById('live-logs'); if(el) el.scrollTop=el.scrollHeight;">
            '''
            st.session_state.live_log_placeholder.markdown(html_content, unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(
        page_title="BIO-DEBUG: Agentic Gene Editor",
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

    # Enable backend log redirection
    enable_streamlit_logging()

    # Run pipeline on click
    if run_clicked:
        st.session_state.ui_locked = True
        st.session_state.status = "running"
        st.session_state.result_json = None
        st.session_state.agent_logs = []

        # Clear prior derived UI fields
        st.session_state.annotations = []
        st.session_state.diagnosis_summary = None
        st.session_state.therapy_ui = None
        st.session_state.safety_ui = None

        # Save uploaded file to disk for backend pipeline
        uploaded_file = st.session_state.get("uploaded_fasta_file")
        if uploaded_file is not None:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".fasta", mode="wb") as tmp:
                tmp.write(uploaded_file.getvalue())
                patient_dna_path = tmp.name
        else:
            st.error("No FASTA file uploaded.")
            st.session_state.ui_locked = False
            return

        # Render scrollable log container for live updates
        st.markdown('<div class="crispr-panel">', unsafe_allow_html=True)
        st.markdown("### ZONE C: AGENT SWARM LOGS")
        st.info("🔄 Pipeline is running... logs updating in real-time")
        
        # Create auto-scrolling log container with placeholder
        log_placeholder = st.empty()
        st.session_state.live_log_placeholder = log_placeholder
        log_placeholder.markdown('<div class="log-box-live" id="live-logs">(starting...)</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Run backend pipeline
        try:
            api_key = get_api_key()
            st.session_state.agent_logs.append("🔬 Initializing agents...")
            _update_live_logs()
            
            outputs = run_full_pipeline(
                patient_dna_path=patient_dna_path,
                reference_path="data/dna_reference_hbb.fasta",
                annotation_path="data/annotation.gff3",
                clinvar_path="data/clinvar.vcf",
                conservation_path="data/conservation.csv",
                protein_struct_path="data/protein_structure.json",
                api_key=api_key
            )
            
            # Extract results and report from pipeline output
            results_data = outputs.get("results", outputs)
            report_md = outputs.get("report_md", "")
            
            st.session_state.result_json = results_data
            st.session_state.report_md = report_md
            
            # Post-process for UI highlights
            annotations, diag_summary = diagnostician_to_ui(results_data)
            st.session_state.annotations = annotations
            st.session_state.diagnosis_summary = diag_summary

            st.session_state.status = "done"

        except Exception as e:
            import traceback
            error_msg = str(e)
            traceback_msg = traceback.format_exc()
            st.session_state.agent_logs.append(f"❌ Error: {error_msg}")
            st.session_state.agent_logs.append(traceback_msg)
            st.session_state.status = "error"
        finally:
            st.session_state.ui_locked = False
            st.session_state.live_log_placeholder = None
            st.rerun()
    else:
        # Normal state - show Zone C with completed logs
        render_zone_c(
            events=[{"ts": "", "agent": "backend", "text": log} for log in st.session_state.get("agent_logs", [])],
            final_result=st.session_state.result_json,
        )


if __name__ == "__main__":
    main()
