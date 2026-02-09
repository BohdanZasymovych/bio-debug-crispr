
from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime


def now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def code_block(text: str, lang: str = "text") -> str:
    """Wrap text in a Markdown code block."""
    text = text or ""
    return f"```{lang}\n{text}\n```"


def extract_variants(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert results.json (keyed by mutation index)
    into a list of per-variant dictionaries.
    
    Expected input structure:
    {
        "123": {
            "diagnostician": {
                "diagnostic": {"index": 123, "risk_level": "Pathogenic", "reasoning": "..."},
                "target_gene": "HBB",
                "ref": "A",
                "alt": "T"
            },
            "engineer": {
                "mutation_index": 123,
                "candidates": [...],
                "analysis": "..."
            },
            "regulator": {
                "ranked_candidates": [...]
            }
        }
    }
    """
    variants = []
    for index, data in results.items():
        if not isinstance(data, dict):
            continue

        # Flatten diagnostician structure for easier access
        diag_raw = data.get("diagnostician", {})
        diag_nested = diag_raw.get("diagnostic", {})
        
        diagnostician = {
            "index": diag_nested.get("index", index),
            "risk_level": diag_nested.get("risk_level", "UNKNOWN"),
            "reasoning": diag_nested.get("reasoning", ""),
            "target_gene": diag_raw.get("target_gene", "N/A"),
            "ref": diag_raw.get("ref", "?"),
            "alt": diag_raw.get("alt", "?"),
        }

        variant = {
            "index": int(index),
            "diagnostician": diagnostician,
            "engineer": data.get("engineer", {}),
            "regulator": data.get("regulator", {}),
        }
        variants.append(variant)

    return variants


def therapy_feasibility(engineer: Dict[str, Any]) -> str:
    """
    Decide whether a CRISPR therapy is constructible.
    
    Engineer structure:
    {
        "mutation_index": 123,
        "candidates": [
            {
                "spacer_sequence": "...",
                "repair_template": {
                    "is_tryptophan": false,
                    "too_short_context": false,
                    "templates": [...]
                }
            },
            ...
        ],
        "analysis": "..."
    }
    """
    candidates = engineer.get("candidates", [])
    
    if not candidates:
        return "NOT CONSTRUCTIBLE"
    
    # Check if any candidate has viable repair templates
    for cand in candidates:
        repair = cand.get("repair_template", {})
        too_short = repair.get("too_short_context", False)
        is_tryptophan = repair.get("is_tryptophan", False)
        templates = repair.get("templates", [])
        
        if not too_short and not is_tryptophan and templates:
            return "CONSTRUCTIBLE"

    return "NOT CONSTRUCTIBLE"


def safety_summary(regulator: Dict[str, Any]) -> str:
    """
    Return short safety summary from regulator output.
    """
    ranked = regulator.get("ranked_candidates", [])
    if not ranked:
        return "UNKNOWN"

    top = ranked[0]
    return f"{top.get('recommendation', 'UNKNOWN')} (risk: {top.get('risk_level', 'UNKNOWN')})"


def build_markdown_report(results: Dict[str, Any]) -> str:
    """
    Build a human-readable clinical report in Markdown
    from the aggregated results.json.
    """
    run_id = now_iso()
    variants = extract_variants(results)

    lines: List[str] = []


    lines.append("# 🧬 BIO-DEBUG — Clinical Report")
    lines.append(f"**Run ID:** `{run_id}`")
    lines.append("")


    lines.append("## Executive Summary")

    pathogenic = 0
    constructible = 0

    for v in variants:
        if v["diagnostician"].get("risk_level") == "Pathogenic":
            pathogenic += 1
        if therapy_feasibility(v["engineer"]) == "CONSTRUCTIBLE":
            constructible += 1

    lines.append(
        f"- **{len(variants)} genetic variants** were analyzed.\n"
        f"- **{pathogenic} variants** are classified as pathogenic.\n"
        f"- **{constructible} variants** have a technically constructible CRISPR therapy.\n"
    )

  
    lines.append("## Variant Details")

    for v in variants:
        idx = v["index"]
        diag = v["diagnostician"]
        eng = v["engineer"]
        reg = v["regulator"]

        lines.append(f"### Variant at position {idx}")

        # Diagnosis section
        lines.append("**Diagnosis**")
        lines.append(
            f"- Gene: `{diag.get('target_gene', 'N/A')}`\n"
            f"- Change: `{diag.get('ref', '?')} → {diag.get('alt', '?')}`\n"
            f"- Risk level: **{diag.get('risk_level', 'UNKNOWN')}**\n"
            f"- Reasoning: {diag.get('reasoning', 'No reasoning provided.')}\n"
        )

        # CRISPR therapy design section
        feasibility = therapy_feasibility(eng)
        lines.append("**CRISPR Therapy Design**")
        lines.append(f"- Overall Status: **{feasibility}**")
        
        candidates = eng.get("candidates", [])
        regulator_ranked = reg.get("ranked_candidates", [])
        
        if candidates:
            lines.append(f"- Total candidates analyzed: {len(candidates)}")
            lines.append("")
            
            # Build a map of regulator decisions by gRNA sequence
            reg_map = {}
            for rc in regulator_ranked:
                grna = rc.get("gRNA", "")
                reg_map[grna] = rc
            
            for i, cand in enumerate(candidates):
                spacer = cand.get("spacer_sequence", "")
                pam = cand.get("pam_sequence", "")
                strand = cand.get("strand", "")
                gc_content = cand.get("gc_content", 0)
                cut_distance = cand.get("cut_distance", 0)
                safety = cand.get("safety", {})
                repair = cand.get("repair_template", {})
                
                # Check regulator decision for this candidate
                reg_info = reg_map.get(spacer, {})
                recommendation = reg_info.get("recommendation", "NOT EVALUATED")
                risk_level = reg_info.get("risk_level", "UNKNOWN")
                safety_score = reg_info.get("safety_score", "N/A")
                efficiency_score = reg_info.get("efficiency_score", "N/A")
                issues = reg_info.get("issues", [])
                
                is_approved = recommendation == "APPROVE"
                status_label = "✅ APPROVED" if is_approved else "❌ REJECTED"
                
                lines.append(f"**Candidate {i+1}: {status_label}**")
                lines.append(f"- PAM: `{pam}` | Strand: {strand} | Cut distance: {cut_distance}bp")
                lines.append(f"- GC content: {gc_content:.1f}%")
                lines.append(f"- Safety score: {safety_score}/100 | Efficiency score: {efficiency_score}")
                lines.append(f"- Risk level: {risk_level}")
                
                # gRNA sequence
                lines.append("- gRNA sequence:")
                lines.append(code_block(spacer))
                
                # Repair template (if available)
                templates = repair.get("templates", [])
                if templates:
                    best_template = templates[0].get("sequence", "")
                    if best_template:
                        lines.append("- Repair template:")
                        lines.append(code_block(best_template))
                
                # Safety details
                lines.append("- Manufacturing safety checks:")
                lines.append(f"  - Has terminator sequence: {'Yes ⚠️' if safety.get('has_terminator') else 'No ✓'}")
                lines.append(f"  - Hairpin count: {safety.get('hairpin_count', 0)}")
                lines.append(f"  - Starts with G: {'Yes ✓' if safety.get('starts_with_g') else 'No'}")
                lines.append(f"  - Last nucleotide: {safety.get('last_nucleotide', '?')}")
                
                # Rejection/approval reasoning
                if not is_approved:
                    rejection_reasons = []
                    if safety.get("has_terminator"):
                        rejection_reasons.append("Contains terminator sequence")
                    if safety.get("hairpin_count", 0) > 3:
                        rejection_reasons.append(f"Too many hairpins ({safety.get('hairpin_count')})")
                    if repair.get("is_tryptophan"):
                        rejection_reasons.append("Tryptophan PAM (unshieldable)")
                    if repair.get("too_short_context"):
                        rejection_reasons.append("Insufficient DNA context for repair template")
                    if issues:
                        rejection_reasons.extend(issues)
                    if not rejection_reasons:
                        rejection_reasons.append("Did not pass safety validation")
                    
                    lines.append(f"- **Rejection reasons:** {'; '.join(rejection_reasons)}")
                else:
                    lines.append("- **Approval reasoning:** Passed all safety checks with acceptable risk profile")
                    if issues:
                        lines.append(f"- **Warnings:** {'; '.join(issues)}")
                
                lines.append("")
        else:
            lines.append("- No gRNA candidates were found for this variant.")
            lines.append("")

        # Safety assessment section
        lines.append("**Safety Assessment Summary**")
        lines.append(f"- {safety_summary(reg)}")
        if regulator_ranked:
            top = regulator_ranked[0]
            lines.append(f"- Top candidate safety score: {top.get('safety_score', 'N/A')}/100")
            top_issues = top.get("issues", [])
            if top_issues:
                lines.append(f"- Flagged issues: {', '.join(top_issues)}")
            else:
                lines.append("- No safety issues flagged")
        lines.append("")

        # Recommended next steps
        lines.append("**Recommended next step**")

        if feasibility != "CONSTRUCTIBLE":
            lines.append(
                "- Provide a longer DNA context or alternative PAM sites to enable HDR repair."
            )
        elif safety_summary(reg).startswith("WARNING"):
            lines.append(
                "- Re-design gRNA to reduce off-target risk before clinical use."
            )
        else:
            lines.append(
                "- Therapy design is ready for further validation and export."
            )

        lines.append("")


    lines.append("## Notes")
    lines.append(
        "This report is generated by an experimental AI system and needs to be reviewed by a human."
    )

    return "\n".join(lines)
