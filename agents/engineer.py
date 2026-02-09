import json
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

from tools import engineer_tools
from utils.utils import get_api_key
from prompts.engineer_prompt import ENGINEER_PROMPT


def run_engineer_agent(mutation_index: int, target_base: str, fasta_file_path: str, api_key: str) -> dict:
    print(f"🔹 Designing for mutation at index {mutation_index}...")

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
    
    report = response.content[0].text
    
    try:
        data = json.loads(report)
        print("\n💊  DESIGN REPORT:")
        print("-" * 40)
        
        reasoning = data.get("global_reasoning", "No global reasoning provided.")
        options = data.get("repair_options", [])
        
        print(f"🧠  STRATEGY: {reasoning}")
        print(f"\n🧬  CANDIDATES ({len(options)} generated):")
        
        for i, opt in enumerate(options, 1):
            rank = opt.get('rank', i)
            pam = opt.get('pam_used', 'N/A')
            # Truncate template for cleaner logs
            full_temp = opt.get('repair_template', '')
            short_temp = full_temp[:10] + "..." + full_temp[-10:] if len(full_temp) > 20 else full_temp
            
            print(f"   • Rank {rank}: PAM={pam} | Template={short_temp}")
            
        print("-" * 40)

    except json.JSONDecodeError:
        print("❌ Error: Could not parse engineer response.")
        print(report)
    
    return {
        "mutation_index": mutation_index,
        "candidates": candidates,
        "analysis": report
    }
