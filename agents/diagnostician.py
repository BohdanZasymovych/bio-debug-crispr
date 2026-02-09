import json
import sys
from pathlib import Path
from anthropic import Anthropic

from prompts.diagnostician_prompt import DIAGNOSTICIAN_PROMPT


def run_diagnostician_agent(mutation_data, target_gene, api_key):
    print(f"🔹 Analyzing mutation at index {mutation_data['index']}...")

    print("📊 Gathering evidence...")
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
    
    report = response.content[0].text
    
    try:
        result = json.loads(report)
        print("\n🕵️  DIAGNOSIS REPORT:")
        print("-" * 40)
        
        diag = result.get("diagnostic", {})
        risk = diag.get("risk_level", "Unknown")
        reason = diag.get("reasoning", "No reasoning provided.")
        
        # Emoji based on risk. Matches ui/components/zone_c.py visuals roughly
        risk_emoji = "🔴" if "Pathogenic" in risk else ("🟢" if "Benign" in risk else "🟡")
        
        print(f"{risk_emoji}  RISK LEVEL: {risk.upper()}")
        print(f"📝  REASONING:  {reason}")
        print("-" * 40)
        
    except json.JSONDecodeError:
        print("❌ Error: Could not parse agent response for logging.")
        print(report) # Fallback to raw if parsing fails
        result = {"diagnostic": {"risk_level": "Error", "reasoning": "Parse Error"}}

    # result is used below, so we ensure it exists

    result["target_gene"] = target_gene
    result["ref"] = mutation_data["ref"]
    result["alt"] = mutation_data["alt"]
    return result
