"""
batch_run.py
Runs Pipeline A on all demo calls, then Pipeline B on all onboarding calls.
File naming convention: ACC001_demo.txt / ACC001_onboarding.txt

Usage:
    python batch_run.py
    python batch_run.py --demo_dir data/demo_calls --onboarding_dir data/onboarding_calls
"""

import argparse
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pipeline_a import run_pipeline_a
from pipeline_b import run_pipeline_b


def extract_account_id(filename: str) -> str:
    """Extract ACC001 from ACC001_demo.txt"""
    return Path(filename).stem.split("_")[0]


def run_batch(demo_dir: str, onboarding_dir: str):
    demo_path = Path(demo_dir)
    onboarding_path = Path(onboarding_dir)

    demo_files = sorted(demo_path.glob("*.txt")) + sorted(demo_path.glob("*.md"))
    onboarding_files = sorted(onboarding_path.glob("*.txt")) + sorted(onboarding_path.glob("*.md"))

    results = []

    # ── Pipeline A ───────────────────────────────────────────────
    print(f"\n{'#'*60}")
    print(f"  BATCH: Pipeline A — {len(demo_files)} demo calls")
    print(f"{'#'*60}")

    for f in demo_files:
        account_id = extract_account_id(f.name)
        try:
            run_pipeline_a(str(f), account_id)
            results.append({"account_id": account_id, "pipeline": "A", "status": "success"})
        except Exception as e:
            print(f"\n  ❌ Pipeline A FAILED for {account_id}: {e}")
            traceback.print_exc()
            results.append({"account_id": account_id, "pipeline": "A", "status": "failed", "error": str(e)})

    # ── Pipeline B ───────────────────────────────────────────────
    print(f"\n{'#'*60}")
    print(f"  BATCH: Pipeline B — {len(onboarding_files)} onboarding calls")
    print(f"{'#'*60}")

    for f in onboarding_files:
        account_id = extract_account_id(f.name)
        try:
            run_pipeline_b(str(f), account_id)
            results.append({"account_id": account_id, "pipeline": "B", "status": "success"})
        except Exception as e:
            print(f"\n  ❌ Pipeline B FAILED for {account_id}: {e}")
            traceback.print_exc()
            results.append({"account_id": account_id, "pipeline": "B", "status": "failed", "error": str(e)})

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'#'*60}")
    print("  BATCH SUMMARY")
    print(f"{'#'*60}")
    successes = [r for r in results if r["status"] == "success"]
    failures = [r for r in results if r["status"] == "failed"]
    print(f"  ✅ Succeeded: {len(successes)}/{len(results)}")
    print(f"  ❌ Failed:    {len(failures)}/{len(results)}")

    if failures:
        print("\n  Failed accounts:")
        for r in failures:
            print(f"    - {r['account_id']} (Pipeline {r['pipeline']}): {r.get('error', '')}")

    print(f"\n  All outputs: outputs/accounts/")
    print(f"{'#'*60}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo_dir", default="data/demo_calls")
    parser.add_argument("--onboarding_dir", default="data/onboarding_calls")
    args = parser.parse_args()
    run_batch(args.demo_dir, args.onboarding_dir)


if __name__ == "__main__":
    main()
