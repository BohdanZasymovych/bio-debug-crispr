"""
Agent 3: The Regulator (Safety Officer)
========================================
Role: The FDA Safety Officer - Final authority on therapy safety
Responsibility: Validates CRISPR designs and has authority to REJECT unsafe therapies
"""

import json
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv
from tools import regulator_tools
from utils.utils import get_api_key
from prompts.regulator_prompt import REGULATOR_PROMPT

# Initialize environment
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")


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


def run_regulator_agent(therapy_design: dict, api_key: str) -> dict:
    """
    Main entry point for the Regulator agent.
    Analyzes therapy safety and returns AI-reasoned decision.
    
    Args:
        therapy_design: CRISPR therapy design from Engineer agent
        api_key: Anthropic API key
        
    Returns:
        Dict with decision (APPROVE/REJECT), reasoning, and safety report
    """
    print("=" * 70)
    print("🛡️  REGULATOR AGENT - SAFETY VALIDATION")
    print("=" * 70)
    
    print("\n📊 Computing safety metrics...")
    safety_data = analyze_safety(therapy_design)
    
    # Prepare analysis report for LLM
    analysis_report = json.dumps({
        "therapy_design": therapy_design,
        "safety_analysis": safety_data
    }, indent=2)
    
    print(f"\n🤖 Consulting AI for decision...")
    
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
    
    print("\n🛡️  FINAL DECISION:\n")
    report = response.content[0].text
    print(report)
    
    # Parse the LLM response
    try:
        decision_data = json.loads(report)
    except json.JSONDecodeError:
        # If LLM didn't return valid JSON, fall back to safety metrics
        decision_data = {
            "decision": safety_data['safety_metrics']['recommendation'],
            "safety_score": safety_data['safety_metrics']['score'],
            "risk_level": safety_data['safety_metrics']['risk_level'],
            "reasoning": safety_data['safety_metrics'].get('reason', ''),
            "llm_analysis": report
        }
    
    return {
        "therapy_design": therapy_design,
        "safety_analysis": safety_data,
        "decision": decision_data
    }


def main():
    """Entry point for CLI script."""
    
    # Example therapy design (from Engineer agent)
    example_therapy = {
        "target_gene": "HBB",
        "mutation_location": "chr11:5246696",
        "guide_rna": {
            "spacer_sequence": "GTGCACCTGACTCCTGAGGA",
            "pam_sequence": "AGG",
            "gc_content": 55
        },
        "cas_variant": "High-Fidelity Cas9",
        "repair_template": "GTGCACCTGACTCCTGAGGAGAAGTCTGCC",
        "efficiency_score": 78
    }
    
    result = run_regulator_agent(example_therapy, get_api_key())
    
    print("\n" + "=" * 70)
    print("VALIDATION RESULT:")
    print("=" * 70)
    print(json.dumps(result['decision'], indent=2))


if __name__ == "__main__":
    main()