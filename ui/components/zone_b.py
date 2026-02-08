# ui/components/zone_b.py
from __future__ import annotations

import streamlit as st
from typing import Any, Dict, Optional


def _badge(text: str, kind: str = "ok") -> str:
    cls = {"ok": "badge badge-ok", "warn": "badge badge-warn", "bad": "badge badge-bad"}.get(kind, "badge")
    return f'<span class="{cls}">{text}</span>'


def render_zone_b(
    diagnosis_summary: Optional[Dict[str, Any]],
    therapy_ui: Optional[Dict[str, Any]],
    safety_ui: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Zone B renders the solution space.

    diagnosis_summary (from core/contracts.py diagnostician_to_ui):
      {
        "patient_id": "...",
        "global_status": "ACTION_REQUIRED" | "UNKNOWN" | ...
        "critical_positions": [70, ...],
        "findings_count": N
      }

    therapy_ui (from core/contracts.py therapist_to_ui):
      {
        "patient_id": "...",
        "targets": [...],
        "primary": {
          "mutation_index": 70,
          "strategy": "...",
          "pam_used": "...",
          "guide_rna": "...",
          "repair_template": "...",
          "safety_notes": "..."
        }
      }

    safety_ui: optional placeholder for Agent 3 (later)
    """
    st.markdown('<div class="crispr-panel">', unsafe_allow_html=True)
    st.markdown("### ZONE B: THERAPY PLAN")

    if not diagnosis_summary:
        st.info("No diagnosis yet. Run the analysis to generate a therapy plan.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    patient_id = diagnosis_summary.get("patient_id", "P-001")
    status = (diagnosis_summary.get("global_status") or "UNKNOWN").upper()
    critical = diagnosis_summary.get("critical_positions", []) or []
    findings_count = diagnosis_summary.get("findings_count", 0)

    # ---- Component 4: Diagnosis Card
    if status in {"ACTION_REQUIRED", "CRITICAL_DETECTED"} or len(critical) > 0:
        st.error(f"🔴 {status}")
        if critical:
            st.caption(f"Patient: {patient_id} | Critical targets: {', '.join(map(str, critical))} | Findings: {findings_count}")
        else:
            st.caption(f"Patient: {patient_id} | Findings: {findings_count}")
    else:
        st.success(f"🟢 {status}")
        st.caption(f"Patient: {patient_id} | Findings: {findings_count}")

    # ---- Component 5: Manufacturing Kit
    st.markdown("#### Manufacturing Kit")

    primary = (therapy_ui or {}).get("primary") if isinstance(therapy_ui, dict) else None
    if not isinstance(primary, dict):
        st.warning("No therapy payload generated yet.")
        primary = {}

    guide = primary.get("guide_rna", "") or ""
    template = primary.get("repair_template", "") or ""
    strategy = primary.get("strategy", "—")
    pam_used = primary.get("pam_used", "—")
    safety_notes = primary.get("safety_notes", "")

    st.caption(f"Strategy: **{strategy}**")
    st.markdown("**gRNA Sequence (copy/paste):**")
    st.code(guide if guide else "(not generated)", language="text")

    st.markdown("**Repair Template (copy/paste):**")
    st.code(template if template else "(not generated)", language="text")

    if safety_notes:
        st.caption(f"Safety notes: {safety_notes}")

    # ---- Component 6: Safety Badges
    st.markdown("#### Safety Checks")

    badges_html = ""
    badges_html += _badge(f"✅ PAM: {pam_used}", "ok")

    # From Agent 2 notes (shield strategy is embedded in safety_notes usually)
    if "silent mutation" in (safety_notes or "").lower():
        badges_html += _badge("✅ Shield: Silent Mutation", "ok")
    else:
        badges_html += _badge("⚠️ Shield: Not specified", "warn")

    # Agent 3 status placeholder (will refine once you share agent 3 JSON)
    if isinstance(safety_ui, dict):
        approved = safety_ui.get("approved")
        if approved is True:
            badges_html += _badge("✅ Safety: APPROVED", "ok")
        elif approved is False:
            reason = safety_ui.get("reason", "REJECTED")
            badges_html += _badge(f"❌ Safety: REJECTED ({reason})", "bad")
        else:
            badges_html += _badge("⏳ Safety: pending", "warn")
    else:
        badges_html += _badge("⏳ Safety: pending", "warn")

    st.markdown(badges_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
