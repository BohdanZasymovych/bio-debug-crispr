import json
import sys
from pathlib import Path
from anthropic import Anthropic

from prompts.diagnostician_prompt import DIAGNOSTICIAN_PROMPT


def run_diagnostician_agent(mutation_data, target_gene, api_key):
    print(f"🧬 AGENT STARTED: Analyzing mutation at index {mutation_data['index']}...")

    print("📊 Analyzing single mutation...")
    analysis_data = {
        "index": mutation_data["index"],
        "feature": mutation_data["feature"],
        "evidence": mutation_data["evidence"]
    }

    analysis_report = json.dumps(analysis_data, indent=2)
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
    
    result = json.loads(report)
    result["target_gene"] = target_gene
    result["ref"] = mutation_data["ref"]
    result["alt"] = mutation_data["alt"]
    return result
