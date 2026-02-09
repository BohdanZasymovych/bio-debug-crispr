# ui/components/zone_c.py
from __future__ import annotations

import json
import html
import streamlit as st
from typing import Any, Dict, List, Optional


def _emoji(agent: str) -> str:
    agent = (agent or "").lower()
    if agent == "diagnostician":
        return "🕵️"
    if agent == "therapist":
        return "💊"
    if agent == "safety":
        return "🛡️"
    if agent == "orchestrator":
        return "🧠"
    return "•"


def render_zone_c(
    events: List[Dict[str, Any]],
    final_result: Optional[Dict[str, Any]] = None,
) -> None:
    st.markdown('<div class="crispr-panel">', unsafe_allow_html=True)
    st.markdown("### ZONE C: AGENT SWARM LOGS")

    with st.expander("Agent Reasoning Logs", expanded=True):
        view_raw = st.checkbox("View Raw JSON", value=False)

        # Pretty log feed
        if not events:
            st.markdown('<div class="log-box">(no logs yet)</div>', unsafe_allow_html=True)
        else:
            lines = []
            for e in events:
                if not isinstance(e, dict):
                    continue
                ts = html.escape(str(e.get("ts", "")))
                agent = html.escape(str(e.get("agent", "unknown")))
                text = html.escape(str(e.get("text", "")))
                prefix = _emoji(agent)
                lines.append(
                    f'<p class="log-line"><span class="log-ts">[{ts}]</span>{prefix} <b>[{agent}]</b>: {text}</p>'
                )
            st.markdown(f'<div class="log-box">{"".join(lines)}</div>', unsafe_allow_html=True)

        # Raw JSON proof
        if view_raw:
            st.markdown("#### Raw events JSON")
            st.code(json.dumps(events, indent=2), language="json")

            if final_result is not None:
                st.markdown("#### Final result JSON")
                st.code(json.dumps(final_result, indent=2), language="json")

    st.markdown("</div>", unsafe_allow_html=True)
