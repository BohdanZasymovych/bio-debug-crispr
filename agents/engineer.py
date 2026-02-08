import json
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

from tools import engineer_tools
from utils.utils import get_api_key, read_fasta
from prompts.engineer_prompt import ENGINEER_PROMPT


# Initialize environment
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")


def analyze_candidates(mutation_index: int, target_base: str, fasta_file_path: str) -> list[dict]:
    """
    Finds all gRNA candidates and computes their metrics including repair templates.
    Returns a fully-analyzed report for the LLM to reason over.
    """
    fasta_data = read_fasta(fasta_file_path)
    dna_sequence = fasta_data["sequence"]
    
    candidates = engineer_tools.find_pam_sites(dna_sequence, mutation_index)
    
    analyzed = []
    for candidate in candidates:
        spacer = candidate["spacer_sequence"]
        pam_index = candidate["pam_start_index"]
        
        gc_content = engineer_tools.calculate_gc_content(spacer)
        safety = engineer_tools.check_manufacturing(spacer)
        patch = engineer_tools.apply_manufacturing_patch(spacer)
        
        repair_options = engineer_tools.generate_repair_template_options(
            dna_sequence, mutation_index, pam_index, target_base
        )
        
        analyzed.append({
            "spacer_sequence": spacer,
            "strand": candidate["strand"],
            "pam_sequence": candidate["pam_sequence"],
            "cut_distance": candidate["cut_distance"],
            "gc_content": round(gc_content, 3),
            "safety": {
                "has_terminator": safety["has_terminator"],
                "hairpin_count": safety["hairpin_count"],
                "starts_with_g": safety["starts_with_g"],
                "last_nucleotide": safety["last_nucleotide"]
            },
            "u6_patch": patch["modification"],
            "repair_template": {
                "is_tryptophan": repair_options["is_tryptophan"],
                "too_short_context": repair_options["too_short_context"],
                "templates": repair_options["templates"]
            }
        })
    
    return analyzed


def run_engineer_agent(mutation_index: int, target_base: str, fasta_file_path: str, api_key: str) -> dict:
    print(f"🧬 AGENT STARTED: Analyzing mutation at index {mutation_index}...")

    print("📊 Computing candidate metrics...")
    candidates = analyze_candidates(mutation_index, target_base, fasta_file_path)
    print(f"   Found {len(candidates)} candidates")

    candidate_report = json.dumps(candidates, indent=2)
    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        temperature=0,
        messages=[{
            "role": "user",
            "content": ENGINEER_PROMPT.format(
                mutation_index=mutation_index,
                target_base=target_base,
                candidate_report=candidate_report
            )
        }]
    )
    
    print("\n🤖 FINAL REPORT:\n")
    report = response.content[0].text
    print(report)
    
    return {
        "mutation_index": mutation_index,
        "candidates": candidates,
        "analysis": report
    }


def main():
    """Entry point for CLI script."""
    run_engineer_agent(
        mutation_index=105, 
        target_base="A", 
        fasta_file_path="data/dna_input.fasta",
        api_key=get_api_key()
    )


if __name__ == "__main__":
    main()