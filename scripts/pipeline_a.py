"""
pipeline_a.py
Full Pipeline A: Demo transcript -> v1 memo -> v1 agent spec -> Notion task
Usage:
    python pipeline_a.py --transcript data/demo_calls/ACC001_demo.txt --account_id ACC001
"""

import argparse
import json
import sys
from pathlib import Path

# Add scripts dir to path so we can import siblings
sys.path.insert(0, str(Path(__file__).parent))

from extract_memo import load_transcript, extract_memo, save_memo
from generate_agent import build_agent_spec, save_agent_spec
from create_task import create_notion_task


def run_pipeline_a(transcript_path: str, account_id: str):
    print(f"\n{'='*60}")
    print(f"  PIPELINE A — {account_id}")
    print(f"  Input: {transcript_path}")
    print(f"{'='*60}")

    # ── Step 1: Load transcript ──────────────────────────────────
    print("\n[1/4] Loading transcript...")
    transcript = load_transcript(transcript_path)
    print(f"  Loaded {len(transcript)} characters")

    # Save a copy of the transcript to outputs for traceability
    out_dir = Path(f"outputs/accounts/{account_id}/v1")
    out_dir.mkdir(parents=True, exist_ok=True)
    transcript_out = out_dir / "transcript.txt"
    transcript_out.write_text(transcript, encoding="utf-8")
    print(f"  Saved transcript copy -> {transcript_out}")

    # ── Step 2: Extract Account Memo ─────────────────────────────
    print("\n[2/4] Extracting Account Memo from transcript...")
    memo = extract_memo(transcript, account_id, mode="demo")
    save_memo(memo, account_id, version="v1")

    # Print a quick summary of what was found
    print(f"  Company: {memo.get('company_name', 'N/A')}")
    print(f"  Business hours: {memo.get('business_hours')}")
    unknowns = memo.get("questions_or_unknowns") or []
    if unknowns:
        print(f"  ⚠ Unknowns flagged: {unknowns}")

    # ── Step 3: Generate Agent Spec ──────────────────────────────
    print("\n[3/4] Generating Retell Agent Draft Spec (v1)...")
    spec = build_agent_spec(memo, version="v1")
    save_agent_spec(spec, account_id, version="v1")
    print(f"  Agent name: {spec.get('agent_name')}")

    # ── Step 4: Create Notion task ───────────────────────────────
    print("\n[4/4] Creating Notion tracking task...")
    task_result = create_notion_task(
        account_id=account_id,
        company_name=memo.get("company_name") or "Unknown",
        version="v1",
        status="Demo Complete — Awaiting Onboarding",
        notes=f"Unknowns: {unknowns}" if unknowns else "No unknowns flagged"
    )
    if task_result:
        print(f"  Notion task created: {task_result}")
    else:
        print("  Notion task skipped (no API key configured)")

    print(f"\n✅ Pipeline A complete for {account_id}")
    print(f"   Outputs: outputs/accounts/{account_id}/v1/")
    print(f"{'='*60}\n")

    return memo, spec


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--account_id", required=True)
    args = parser.parse_args()
    run_pipeline_a(args.transcript, args.account_id)


if __name__ == "__main__":
    main()
