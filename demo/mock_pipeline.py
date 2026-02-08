# demo/mock_pipeline.py
from __future__ import annotations

import time
from typing import Any, Dict, Tuple

from core.events import add_event


def run_mock_pipeline(patient_dna: str) -> Dict[str, Any]:
    """
    Mock orchestrator:
    - emits logs like agents are working
    - returns JSON outputs in the SAME shapes as Agent 1 + Agent 2 specs
    """
    add_event("orchestrator", "Pipeline started", etype="state")

    # -------- Agent 1: Diagnostician (mock)
    add_event("diagnostician", "Step 1: Alignment — comparing patient DNA to reference (mock).", etype="message")
    time.sleep(0.2)

    # For demo: "detect" two mutations if sequence long enough
    # indices are BIO-style (1-based) in the spec
    mut_a = 70
    mut_b = 200 if len(patient_dna) >= 200 else max(10, len(patient_dna) // 2)

    add_event("diagnostician", f"Mutations found at indices: {mut_a}, {mut_b} (mock).", etype="tool_result")
    time.sleep(0.2)

    add_event("diagnostician", "Step 2: Tribunal — weighing ClinVar vs Conservation vs Structure (mock).")
    time.sleep(0.2)

    diagnostician_json = {
        "diagnosis_report": {
            "patient_id": "P-001",
            "global_status": "ACTION_REQUIRED",
            "findings": [
                {
                    "index": mut_a,
                    "verdict": "CRITICAL",
                    "reasoning": "ClinVar explicitly classifies this as Sickle Cell Anemia (mock)."
                },
                {
                    "index": mut_b,
                    "verdict": "BENIGN",
                    "reasoning": "Novel variant with low conservation and safe structural context (mock)."
                }
            ]
        }
    }

    add_event("diagnostician", "Verdict issued: CRITICAL targets exist → ACTION_REQUIRED.", etype="decision", level="warn",
              payload={"critical_indices": [mut_a]})
    time.sleep(0.2)

    # -------- Agent 2: Therapist (mock)
    add_event("therapist", "Receiving diagnosis. Designing HDR plan (mock).")
    time.sleep(0.2)

    add_event("therapist", "Locating PAM sites near mutation (mock scan).")
    time.sleep(0.2)

    therapy_json = {
        "therapy_plan": {
            "patient_id": "P-001",
            "targets": [
                {
                    "mutation_index": mut_a,
                    "strategy": "HDR (Homology Directed Repair)",
                    "components": {
                        "pam_used": "TGG at index 74",
                        "guide_rna": "GTGCATCTGACTCCTGAGGA",
                        "repair_template": "ACATTT...AGGAGA...CTGGGC"
                    },
                    "safety_notes": "Repair template includes a silent mutation (G->C) at index 75 to disrupt the PAM site and prevent re-cutting."
                }
            ]
        }
    }

    add_event("therapist", "Therapy payload drafted (gRNA + repair template).", etype="decision", level="info")
    time.sleep(0.2)

    # -------- Agent 3: Safety (placeholder until we have your real JSON contract)
    add_event("safety", "Running off-target scan (mock).", etype="message")
    time.sleep(0.2)

    safety_json = {
        "approved": None,
        "reason": "PENDING (mock placeholder)",
        "off_target_hits": None
    }
    add_event("safety", "Safety check pending (mock placeholder).", etype="decision", level="warn")

    add_event("orchestrator", "Pipeline finished (mock)", etype="state")

    return {
        "agent1_diagnostician": diagnostician_json,
        "agent2_therapist": therapy_json,
        "agent3_safety": safety_json,
    }

