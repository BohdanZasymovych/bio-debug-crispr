# ui/components/zone_a.py
from __future__ import annotations

import html
import streamlit as st
from typing import Any, Dict, List, Tuple

from core.dna import load_uploaded_fasta, normalize_dna, is_valid_dna, dna_length_hint


def _render_dna_html(seq: str, annotations: List[Dict[str, Any]]) -> str:
    """
    Renders DNA as HTML spans with color-coded highlights.
    annotations expected (from core/contracts.py diagnostician_to_ui):
      [{ "index0": int, "type": "critical"|"benign", "tooltip": str, ... }, ...]
    """
    ann_map = {a.get("index0"): a for a in annotations if isinstance(a, dict) and isinstance(a.get("index0"), int)}

    chunks = []
    for i, ch in enumerate(seq):
        safe_ch = html.escape(ch)
        if i in ann_map:
            a = ann_map[i]
            # Map semantic type to CSS class
            t = a.get("type", "benign")
            if t == "critical":
                cls = "dna-critical"
            elif t == "warning":
                cls = "dna-warning"
            elif t == "safe":
                cls = "dna-safe"
            else:
                cls = "dna-benign"

            tooltip = html.escape(a.get("tooltip") or "")
            chunks.append(f'<span class="{cls}" title="{tooltip}">{safe_ch}</span>')
        else:
            chunks.append(f'<span class="dna-base">{safe_ch}</span>')

    return f'<div class="dna-box">{"".join(chunks) if chunks else "(no sequence)"}</div>'


def render_zone_a(
    annotations: List[Dict[str, Any]],
    ui_locked: bool,
) -> Tuple[str, bool]:
    """
    Zone A: input + visualizer + primary trigger.
    Returns: (dna_norm, run_clicked)
    """
    st.markdown('<div class="crispr-panel">', unsafe_allow_html=True)
    st.markdown("### ZONE A: PATIENT GENOME")

    # --- Sequence loader


    uploaded = st.file_uploader("Upload FASTA", type=["fasta", "fa", "txt"], disabled=ui_locked)
    dna_raw = st.session_state.get("dna_raw", "")
    if uploaded is not None and not ui_locked:
        # Only parse and update if new file uploaded
        if (
            "uploaded_fasta_file" not in st.session_state
            or st.session_state.uploaded_fasta_file != uploaded
        ):
            content = uploaded.read()
            parsed = load_uploaded_fasta(content)
            st.session_state.dna_raw = parsed
            st.session_state.uploaded_fasta_file = uploaded
            dna_raw = parsed
        else:
            dna_raw = st.session_state.get("dna_raw", "")
    else:
        dna_raw = st.session_state.get("dna_raw", "")

    dna_norm = normalize_dna(dna_raw)
    st.session_state.dna_norm = dna_norm

    # --- Validation + hints
    level, msg = dna_length_hint(dna_norm)
    st.caption(msg)

    valid = is_valid_dna(dna_norm) if dna_raw.strip() else False
    if dna_raw.strip() and not valid:
        st.error("Only A, C, G, T, N are allowed (spaces/newlines OK).")

    # --- Visualizer
    st.markdown("#### Visualizer")
    dna_html = _render_dna_html(dna_norm, annotations) if dna_norm else '<div class="dna-box">(no sequence)</div>'
    st.markdown(dna_html, unsafe_allow_html=True)

    # --- Primary Trigger
    run_disabled = (not valid) or ui_locked
    run_clicked = st.button("Analyze & Design Cure  >", type="primary", disabled=run_disabled)

    st.markdown("</div>", unsafe_allow_html=True)
    return dna_norm, run_clicked
