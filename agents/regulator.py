"""
Agent 3: The Regulator (Safety Officer)
========================================
Role: The FDA Safety Officer - Final authority on therapy safety
Responsibility: Validates CRISPR designs and has authority to REJECT unsafe therapies
"""

import json
from anthropic import Anthropic
from tools import regulator_tools
from prompts.regulator_prompt import REGULATOR_PROMPT


def analyze_safety(therapy_design: dict) -> dict:
    """
    Runs comprehensive safety analysis on a CRISPR therapy design.
    Returns all safety metrics and findings for the LLM to reason over.
    
    Args:
        therapy_design: Dict containing guide_rna, target_gene, cas_variant, etc.
        
    Returns:
        Dict with off-target analysis, essentiality checks, and safety scores
    """
    # Extract key parameters
    grna_sequence = therapy_design.get('guide_rna', {}).get('spacer_sequence', '')
    target_gene = therapy_design.get('target_gene', 'Unknown')
    
    if not grna_sequence:
        return {
            "error": "No guide RNA sequence provided",
            "off_targets": [],
            "safety_score": 0,
            "decision": "REJECT"
        }
    
    print(f"🔍 Running genome-wide BLAST for gRNA: {grna_sequence}")
    
    # Run BLAST search
    off_targets = regulator_tools.blast_genome_search(grna_sequence)
    
    # Analyze each off-target for gene essentiality
    analyzed_off_targets = []
    critical_findings = []
    
    for ot in off_targets:
        gene_info = regulator_tools.check_gene_essentiality(ot['gene_name'])
        
        analyzed_ot = {
            **ot,
            "gene_essentiality": gene_info
        }
        analyzed_off_targets.append(analyzed_ot)
        
        # Flag critical findings
        if ot['region_type'] == 'EXON' and ot['gene_name'] != target_gene:
            critical_findings.append(
                f"EXON hit in {ot['gene_name']} ({ot['mismatch_count']} mismatches)"
            )
        
        if ot['is_essential'] and ot['mismatch_count'] <= 2:
            critical_findings.append(
                f"ESSENTIAL GENE hit: {ot['gene_name']} with {ot['mismatch_count']} mismatches"
            )
    
    # Calculate overall safety score
    safety_metrics = regulator_tools.calculate_off_target_score(off_targets, target_gene)
    
    print(f"✅ Analysis complete. Found {len(off_targets)} off-target sites")
    print(f"   Safety Score: {safety_metrics['score']}/100")
    print(f"   Risk Level: {safety_metrics['risk_level']}")
    
    return {
        "off_targets_found": len(off_targets),
        "off_targets": analyzed_off_targets,
        "critical_findings": critical_findings,
        "safety_metrics": safety_metrics,
        "target_gene": target_gene
    }


def analyze_all_candidates(engineer_report: dict) -> list:
    """
    For each gRNA candidate in the engineer's report, run all safety and efficiency checks.
    Returns a list of dicts with all metrics for LLM ranking.
    """
    target_gene = engineer_report.get('target_gene', 'Unknown')
    candidates = engineer_report.get('candidates', [])
    genome_sequence = engineer_report.get('genome_sequence', '')  # Optionally pass genome if needed
    ranked_data = []
    for cand in candidates:
        grna_seq = cand.get('spacer_sequence', '')
        pam_seq = cand.get('pam_sequence', '')
        repair_template = cand.get('repair_template', '')
        efficiency_score = cand.get('efficiency_score', 0)
        pam_index = cand.get('pam_index', None)
        mutation_index = cand.get('mutation_index', None)

        # Safety checks
        off_targets = regulator_tools.blast_genome_search(grna_seq, genome_sequence) if genome_sequence else []
        pam_shield = regulator_tools.verify_pam_shield(repair_template, pam_index, mutation_index)
        struct_risk = regulator_tools.analyze_structure_risk(grna_seq)
        safety_metrics = regulator_tools.calculate_safety_score(
            off_targets, pam_shield, struct_risk, target_gene
        )
        ranked_data.append({
            "gRNA": grna_seq,
            "pam": pam_seq,
            "safety_score": safety_metrics['score'],
            "efficiency_score": efficiency_score,
            "risk_level": safety_metrics['risk_level'],
            "recommendation": safety_metrics['recommendation'],
            "issues": safety_metrics['issues'],
            "reasoning": "",  # LLM will fill this in
            "raw": cand  # Optionally keep all original candidate data
        })
    return ranked_data


def run_regulator_agent(engineer_report: dict, api_key: str) -> dict:
    print("\n📊 Computing safety metrics for all candidates...")
    ranked_data = analyze_all_candidates(engineer_report)

    # Prepare analysis report for LLM
    analysis_report = json.dumps({
        "target_gene": engineer_report.get('target_gene', 'Unknown'),
        "ranked_candidates": ranked_data
    }, indent=2)

    print(f"\n🤖 Consulting AI for ranking and decision...")

    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        temperature=0,
        messages=[{
            "role": "user",
            "content": REGULATOR_PROMPT.format(
                analysis_report=analysis_report
            )
        }]
    )

    report = response.content[0].text

    try:
        ranked_result = json.loads(report)
        
        print("\n🛡️  REGULATOR VALIDATION:")
        print("-" * 40)
        
        candidates = ranked_result.get("ranked_candidates", [])
        if candidates:
            # Report on the top ranked candidate
            top = candidates[0]
            score = top.get("safety_score", 0)
            risk = top.get("risk_level", "UNKNOWN")
            rec = top.get("recommendation", "UNKNOWN")
            
            status_moji = "✅" if rec == "APPROVE" else "❌"
            
            print(f"{status_moji}  DECISION: {rec} (Top Candidate)")
            print(f"📊  SAFETY SCORE: {score}/100")
            print(f"⚠️  RISK LEVEL: {risk}")
            
            issues = top.get("issues", [])
            if issues:
                 print(f"🚩  ISSUES: {', '.join(issues)}")
            else:
                 print(f"✨  Clean safety profile.")
        else:
            print("❌  No candidates to validate.")
            
        print("-" * 40)

    except json.JSONDecodeError:
        print("❌ Error: Could not parse regulator response.")
        print(report)
        ranked_result = {"error": "LLM output not valid JSON", "llm_output": report}
    except json.JSONDecodeError:
        ranked_result = {"error": "LLM output not valid JSON", "llm_output": report}

    return ranked_result
