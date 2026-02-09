from __future__ import annotations

from typing import Dict, Any, Optional
import json
import os
import anthropic

from tools.reporter_tools import build_markdown_report
from prompts.reporter_prompt import REPORTER_SYSTEM_PROMPT


def polish_with_llm(markdown: str, api_key: str) -> Optional[str]:
    """
    DEBUG version: prints errors and forces a visible watermark.
    """
    try:
        client = anthropic.Anthropic(api_key=api_key)

        user_content = (
            markdown
            + "\n\nIMPORTANT:\n"
              "- Rewrite the text to be more user-friendly.\n"
              "- Add the exact line at the very end: <!-- polished_by_llm -->\n"
              "- Do not change any code blocks.\n"
        )

        # print("[reporter] Calling Anthropic API...")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            system=REPORTER_SYSTEM_PROMPT,
            max_tokens=2000,
            temperature=0,
            messages=[{"role": "user", "content": user_content}],
        )

       
        parts = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)

        polished = "\n".join(parts).strip()

        return polished if polished else None

    except Exception as e:
        print(f"❌ LLM polish failed: {repr(e)}")
        return None


def run_reporter_agent(
    results: Dict[str, Any],
    api_key: Optional[str] = None,
    enable_llm_polish: bool = True,
) -> Dict[str, Any]:
    """
    Generate a final human-readable clinical report from a single aggregated results JSON.
    - Always builds a deterministic markdown skeleton.
    - Optionally polishes it with an LLM (if api_key provided).
    """
    
    num_variants = len(results) if isinstance(results, dict) else 0
    print(f"📊 Building report for {num_variants} variant(s)...")
    
    skeleton_md = build_markdown_report(results)
    final_md = skeleton_md

    if enable_llm_polish and api_key:
        print("🤖 Polishing report with AI...")
        polished = polish_with_llm(skeleton_md, api_key)

        if polished:
            final_md = polished
            print("✅ Report polished successfully.")
        else:
            final_md = skeleton_md
            print("⚠️ Polish failed, using base report.")
    else:
        print("📄 Using base report (no AI polish).")

    # Report summary
    print("\n📝 REPORT SUMMARY:")
    print("-" * 40)
    print(f"📋 Report length: {len(final_md)} characters")
    print("-" * 40)

    return {
        "report_md": final_md,
        "raw_results": results,
    }


def main():
    """
    Local test:
    - expects results.json in current working directory
    - prints the generated markdown report
    """
    path = "results.json"
    if not os.path.exists(path):
        print("results.json not found in current directory.")
        return

    with open(path, "r", encoding="utf-8") as f:
        results = json.load(f)

    out = run_reporter_agent(
        results,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        enable_llm_polish=True,
    )

    # print(out["report_md"])


if __name__ == "__main__":
    main()
