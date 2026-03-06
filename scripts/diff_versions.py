"""
diff_versions.py
Merges v1 memo + onboarding patch -> v2 memo, produces changelog.md
Usage:
    python diff_versions.py --account_id ACC001 --patch_json '{"business_hours": {"end": "6:00 PM"}}'
    python diff_versions.py --account_id ACC001  # auto-reads v2/memo.json as patch
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from deepdiff import DeepDiff


# ── Merge Logic ────────────────────────────────────────────────────────────────

def deep_merge(base: dict, patch: dict) -> dict:
    """
    Recursively merge patch into base.
    - patch keys with non-null values overwrite base keys
    - patch keys with null values are skipped (keeps base value)
    - lists in patch fully replace lists in base (not appended)
    """
    result = base.copy()
    for key, val in patch.items():
        if val is None:
            continue  # skip nulls — don't overwrite with nothing
        if isinstance(val, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = val
    return result


# ── Changelog Builder ──────────────────────────────────────────────────────────

def build_changelog(v1: dict, v2: dict, account_id: str) -> str:
    diff = DeepDiff(v1, v2, ignore_order=True)

    lines = [
        f"# Changelog — {account_id}",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"Transition: v1 → v2 (onboarding update)",
        "",
    ]

    if not diff:
        lines.append("No changes detected between v1 and v2.")
        return "\n".join(lines)

    # Values changed
    if "values_changed" in diff:
        lines.append("## Updated Fields")
        for path, change in diff["values_changed"].items():
            clean_path = path.replace("root['", "").replace("']['", ".").replace("']", "")
            lines.append(f"- **{clean_path}**")
            lines.append(f"  - Before: `{change['old_value']}`")
            lines.append(f"  - After:  `{change['new_value']}`")
        lines.append("")

    # New items added
    if "dictionary_item_added" in diff:
        lines.append("## Added Fields")
        for path in diff["dictionary_item_added"]:
            clean_path = path.replace("root['", "").replace("']['", ".").replace("']", "")
            lines.append(f"- **{clean_path}** (newly added)")
        lines.append("")

    # Items removed
    if "dictionary_item_removed" in diff:
        lines.append("## Removed Fields")
        for path in diff["dictionary_item_removed"]:
            clean_path = path.replace("root['", "").replace("']['", ".").replace("']", "")
            lines.append(f"- **{clean_path}** (removed)")
        lines.append("")

    # List changes
    if "iterable_item_added" in diff:
        lines.append("## List Items Added")
        for path, val in diff["iterable_item_added"].items():
            clean_path = path.replace("root['", "").replace("']['", ".").replace("']", "")
            lines.append(f"- **{clean_path}**: `{val}`")
        lines.append("")

    if "iterable_item_removed" in diff:
        lines.append("## List Items Removed")
        for path, val in diff["iterable_item_removed"].items():
            clean_path = path.replace("root['", "").replace("']['", ".").replace("']", "")
            lines.append(f"- **{clean_path}**: `{val}`")
        lines.append("")

    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def run_diff(account_id: str, patch: dict | None = None):
    v1_path = Path(f"outputs/accounts/{account_id}/v1/memo.json")
    v2_dir = Path(f"outputs/accounts/{account_id}/v2")
    v2_dir.mkdir(parents=True, exist_ok=True)

    if not v1_path.exists():
        print(f"  [diff_versions] ERROR: v1 memo not found at {v1_path}")
        raise SystemExit(1)

    with open(v1_path, "r") as f:
        v1_memo = json.load(f)

    # If no patch provided inline, look for existing v2 memo (from extract_memo in onboarding mode)
    if patch is None:
        v2_patch_path = v2_dir / "memo.json"
        if not v2_patch_path.exists():
            print(f"  [diff_versions] ERROR: no patch provided and no v2/memo.json found")
            raise SystemExit(1)
        print(f"  [diff_versions] Loading patch from {v2_patch_path}")
        with open(v2_patch_path, "r") as f:
            patch = json.load(f)

    # Merge
    v2_memo = deep_merge(v1_memo, patch)

    # Always ensure account_id and version are correct in v2
    v2_memo["account_id"] = account_id
    v2_memo["version"] = "v2"

    # Save merged v2 memo
    v2_memo_path = v2_dir / "memo.json"
    with open(v2_memo_path, "w") as f:
        json.dump(v2_memo, f, indent=2)
    print(f"  [diff_versions] Saved merged v2 memo -> {v2_memo_path}")

    # Generate changelog
    changelog = build_changelog(v1_memo, v2_memo, account_id)
    changelog_path = v2_dir / "changelog.md"
    with open(changelog_path, "w") as f:
        f.write(changelog)
    print(f"  [diff_versions] Saved changelog -> {changelog_path}")

    return v2_memo, changelog


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--account_id", required=True)
    parser.add_argument("--patch_json", default=None, help="Inline JSON patch string (optional)")
    args = parser.parse_args()

    patch = json.loads(args.patch_json) if args.patch_json else None
    run_diff(args.account_id, patch)
    print(f"  [diff_versions] Done. account_id={args.account_id}")


if __name__ == "__main__":
    main()
