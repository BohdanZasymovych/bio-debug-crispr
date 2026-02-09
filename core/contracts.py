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
def diagnostician_to_ui(pipeline_results: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Input: The 'final' dict from run_full_pipeline, keyed by mutation index (str or int).
    Example:
    {
      "123": {
        "diagnostician": {
          "diagnostic": { "index": 123, "risk_level": "Pathogenic", "reasoning": "..." },
          "target_gene": "HBB", ...
        }, ...
      }
    }

    Output:
      annotations: List of dicts for render_zone_a
      diagnosis_summary: Dict for render_zone_b
    """
    annotations: List[Dict[str, Any]] = []
    critical_positions: List[int] = []
    total_findings = 0
    
    # Check if input is valid
    if not isinstance(pipeline_results, dict):
        return [], {}

    for idx_val, mutation_report in pipeline_results.items():
        # mutation_report corresponds to the dict with keys: 'diagnostician', 'engineer', 'regulator'
        if not isinstance(mutation_report, dict):
            continue
            
        diag_report = mutation_report.get("diagnostician", {})
        if not diag_report:
            continue
            
        # Extract diagnostic details
        diag_data = diag_report.get("diagnostic", {})
        pos = diag_data.get("index")
        risk = (diag_data.get("risk_level") or "UNKNOWN").upper()
        reasoning = diag_data.get("reasoning") or ""
        
        # Ensure we have a valid integer position
        if pos is None:
            # Fallback to key if needed, though safer to use internal index
            try:
                pos = int(idx_val)
            except:
                continue
                
        # Classify risk
        ann_type = "benign"
        if "PATHOGENIC" in risk:
            ann_type = "critical" # Red
        elif "BENIGN" in risk:
            ann_type = "safe"     # Green
        elif "NOVEL" in risk:
            ann_type = "warning"  # Yellow

        is_critical = ann_type == "critical"
        
        tooltip = f"Index: {pos}\nRisk: {risk}\nReason: {reasoning}"
        
        annotations.append({
            "index0": to_zero_based(pos),
            "type": ann_type,
            "tooltip": tooltip,
            "verdict": risk,
            "reasoning": reasoning
        })
        
        total_findings += 1
        if is_critical:
            critical_positions.append(pos)

    # Sort annotations by index
    annotations.sort(key=lambda x: x["index0"])

    diagnosis_summary = {
        "global_status": "ACTION_REQUIRED" if critical_positions else "ALL_CLEAR",
        "critical_positions": critical_positions,
        "findings_count": total_findings
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
