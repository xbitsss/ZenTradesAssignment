"""
pipeline_b.py
Full Pipeline B: Onboarding transcript -> v2 memo (merged) -> v2 agent spec -> changelog
Usage:
    python pipeline_b.py --transcript data/onboarding_calls/ACC001_onboarding.txt --account_id ACC001
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extract_memo import load_transcript, extract_memo, save_memo
from generate_agent import build_agent_spec, save_agent_spec
from diff_versions import run_diff
from create_task import update_notion_task


def run_pipeline_b(transcript_path: str, account_id: str):
    print(f"\n{'='*60}")
    print(f"  PIPELINE B — {account_id}")
    print(f"  Input: {transcript_path}")
    print(f"{'='*60}")

    # ── Check v1 exists ──────────────────────────────────────────
    v1_memo_path = Path(f"outputs/accounts/{account_id}/v1/memo.json")
    if not v1_memo_path.exists():
        print(f"  ERROR: v1 memo not found. Run pipeline_a.py for {account_id} first.")
        raise SystemExit(1)

    # ── Step 1: Load transcript ──────────────────────────────────
    print("\n[1/4] Loading onboarding transcript...")
    transcript = load_transcript(transcript_path)
    print(f"  Loaded {len(transcript)} characters")

    # Save transcript copy
    out_dir = Path(f"outputs/accounts/{account_id}/v2")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "transcript.txt").write_text(transcript, encoding="utf-8")

    # ── Step 2: Extract onboarding patch ────────────────────────
    print("\n[2/4] Extracting onboarding updates (patch only)...")
    patch = extract_memo(transcript, account_id, mode="onboarding")
    # Save raw patch temporarily as v2/memo.json — diff_versions will overwrite with merged
    save_memo(patch, account_id, version="v2")

    # ── Step 3: Merge + Diff ─────────────────────────────────────
    print("\n[3/4] Merging v1 + patch -> v2, generating changelog...")
    v2_memo, changelog = run_diff(account_id)

    # Print changelog summary
    change_lines = [l for l in changelog.split("\n") if l.startswith("- **")]
    if change_lines:
        print(f"  Changes detected ({len(change_lines)} fields):")
        for line in change_lines[:5]:  # show first 5
            print(f"    {line}")
        if len(change_lines) > 5:
            print(f"    ... and {len(change_lines) - 5} more")
    else:
        print("  No field changes detected")

    # ── Step 4: Generate v2 Agent Spec ──────────────────────────
    print("\n[4/4] Generating Retell Agent Draft Spec (v2)...")
    spec = build_agent_spec(v2_memo, version="v2")
    save_agent_spec(spec, account_id, version="v2")
    print(f"  Agent name: {spec.get('agent_name')}")

    # Update Notion task if configured
    update_notion_task(
        account_id=account_id,
        status="Onboarding Complete — v2 Ready"
    )

    print(f"\n✅ Pipeline B complete for {account_id}")
    print(f"   Outputs: outputs/accounts/{account_id}/v2/")
    print(f"   Changelog: outputs/accounts/{account_id}/v2/changelog.md")
    print(f"{'='*60}\n")

    return v2_memo, spec


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--account_id", required=True)
    args = parser.parse_args()
    run_pipeline_b(args.transcript, args.account_id)


if __name__ == "__main__":
    main()
