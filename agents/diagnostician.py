import json
import sys
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

from tools import diagnostician_tools
from utils.utils import get_api_key
from prompts.diagnostician_prompt import DIAGNOSTICIAN_PROMPT


def analyze_mutations(patient_dna_string):
    """
    Analyzes the patient's DNA: finds mutations, gets gene features, and gathers evidence.
    Returns a dict with all analysis data for the LLM.
    """
    mutations = diagnostician_tools.align_sequence(patient_dna_string)
    indices = [v["index"] for v in mutations["variants"]]
    features = {idx: diagnostician_tools.get_gene_feature(idx) for idx in indices}
    evidences = diagnostician_tools.get_evidence_batch(indices)
    
    return {
        "mutations": mutations,
        "features": features,
        "evidences": evidences
    }


def run_diagnostician_agent(patient_dna_string, api_key):
    print(f"🧬 AGENT STARTED: Analyzing patient DNA...")

    print("📊 Computing mutations and evidence...")
    data = analyze_mutations(patient_dna_string)
    print(f"   Found {data['mutations']['mutations_found']} mutations")

    analysis_report = json.dumps(data, indent=2)
    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        temperature=0,
        messages=[{
            "role": "user",
            "content": DIAGNOSTICIAN_PROMPT.format(
                mutations_data=analysis_report
            )
        }]
    )
    
    print("\n🤖 FINAL REPORT:\n")
    report = response.content[0].text
    print(report)
    
    return json.loads(report)


def main():
    """Entry point for CLI script."""
    with open(project_root / "data" / "reference_hbb.fasta", 'r') as f:
        lines = f.readlines()
        reference = "".join(line.strip() for line in lines if not line.startswith(">"))
    
    patient_dna = list(reference)
    patient_dna[70] = "T"
    patient_dna[139] = "A"
    patient_dna = "".join(patient_dna)
    
    result = run_diagnostician_agent(patient_dna, get_api_key())
    print("\nParsed Result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
