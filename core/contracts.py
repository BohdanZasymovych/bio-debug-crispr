# core/contracts.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# If your mutation indices come from VCF/GFF-like sources, it's usually 1-based.
# If your agents return 0-based indices already, set this to 0.
INDEX_BASE = 1  # 1 or 0


def to_zero_based(pos: int) -> int:
    """
    Convert agent position to Python string index.
    If INDEX_BASE=1, position 1 becomes index 0.
    If INDEX_BASE=0, position stays the same.
    """
    return pos - 1 if INDEX_BASE == 1 else pos


def _safe_get(d: Dict[str, Any], path: List[str], default=None):
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


# =========================
# Agent 1 (Diagnostician)
# =========================
def diagnostician_to_ui(agent_json: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Input (example):
    {
      "diagnosis_report": {
        "patient_id": "P-001",
        "global_status": "ACTION_REQUIRED",
        "findings": [
          {"index": 70, "verdict": "CRITICAL", "reasoning": "..."},
          {"index": 200, "verdict": "BENIGN", "reasoning": "..."}
        ]
      }
    }

    Output:
      annotations: [
        { "index0": 69, "type": "critical", "tooltip": "...", "verdict": "...", "reasoning": "..." },
        ...
      ]
      diagnosis_summary: {
        "patient_id": "...",
        "global_status": "...",
        "critical_positions": [70, ...],
        "findings_count": N
      }
    """
    report = agent_json.get("diagnosis_report", {}) if isinstance(agent_json, dict) else {}
    patient_id = report.get("patient_id", "P-001")
    global_status = (report.get("global_status", "UNKNOWN") or "UNKNOWN").upper()
    findings = report.get("findings", [])

    annotations: List[Dict[str, Any]] = []
    critical_positions: List[int] = []

    if isinstance(findings, list):
        for f in findings:
            if not isinstance(f, dict):
                continue
            pos = f.get("index")
            verdict = (f.get("verdict") or "").upper()
            reasoning = f.get("reasoning") or ""

            if not isinstance(pos, int):
                continue

            ann_type = "critical" if verdict == "CRITICAL" else "benign"
            if verdict == "CRITICAL":
                critical_positions.append(pos)

            tooltip = f"Index {pos} | {verdict}"
            annotations.append({
                "pos": pos,                 # original position from agent
                "index0": to_zero_based(pos),# python index for rendering
                "type": ann_type,            # "critical" | "benign"
                "verdict": verdict,
                "reasoning": reasoning,
                "tooltip": tooltip,
            })

    diagnosis_summary = {
        "patient_id": patient_id,
        "global_status": global_status,
        "critical_positions": sorted(set(critical_positions)),
        "findings_count": len(findings) if isinstance(findings, list) else 0,
    }

    return annotations, diagnosis_summary


# =========================
# Agent 2 (Therapist)
# =========================
def therapist_to_ui(agent_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input (example):
    {
      "therapy_plan": {
        "patient_id": "P-001",
        "targets": [
          {
            "mutation_index": 70,
            "strategy": "HDR ...",
            "components": {
              "pam_used": "TGG at index 74",
              "guide_rna": "....",
              "repair_template": "...."
            },
            "safety_notes": "..."
          }
        ]
      }
    }

    Output (UI-friendly):
    {
      "patient_id": "...",
      "targets": [ { ... } ],
      "primary": { ... } | None
    }
    """
    plan = agent_json.get("therapy_plan", {}) if isinstance(agent_json, dict) else {}
    patient_id = plan.get("patient_id", "P-001")
    targets = plan.get("targets", [])

    ui_targets: List[Dict[str, Any]] = []
    if isinstance(targets, list):
        for t in targets:
            if not isinstance(t, dict):
                continue
            comps = t.get("components", {}) if isinstance(t.get("components"), dict) else {}
            ui_targets.append({
                "mutation_index": t.get("mutation_index"),
                "strategy": t.get("strategy") or "—",
                "pam_used": comps.get("pam_used") or "—",
                "guide_rna": comps.get("guide_rna") or "",
                "repair_template": comps.get("repair_template") or "",
                "safety_notes": t.get("safety_notes") or "",
            })

    primary = ui_targets[0] if ui_targets else None
    return {
        "patient_id": patient_id,
        "targets": ui_targets,
        "primary": primary,
    }
