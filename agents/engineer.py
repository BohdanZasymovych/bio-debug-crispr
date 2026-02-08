import json
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

from tools import engineer_tools
from utils.utils import get_api_key
from prompts.engineer_prompt import ENGINEER_PROMPT


def run_engineer_agent(mutation_index: int, target_base: str, fasta_file_path: str, api_key: str) -> dict:
    print(f"🧬 AGENT STARTED: Analyzing mutation at index {mutation_index}...")

    candidates = engineer_tools.analyze_candidates(mutation_index, target_base, fasta_file_path)
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
    
    print("\n🧬 FINAL REPORT:\n")
    report = response.content[0].text
    print(report)
    
    return {
        "mutation_index": mutation_index,
        "candidates": candidates,
        "analysis": report
    }
