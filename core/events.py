# core/events.py
from __future__ import annotations

from datetime import datetime
import streamlit as st
from typing import Any, Dict, Optional

def now_ts() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")

def add_event(agent: str, text: str, etype: str = "message", level: str = "info",
              payload: Optional[Dict[str, Any]] = None) -> None:
    if "events" not in st.session_state:
        st.session_state.events = []
    st.session_state.events.append({
        "ts": now_ts(),
        "agent": agent,
        "type": etype,
        "level": level,
        "text": text,
        "payload": payload or {},
    })

def get_events() -> list[dict]:
    return st.session_state.get("events", [])
