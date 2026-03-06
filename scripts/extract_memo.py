"""
extract_memo.py
Transcript -> Account Memo JSON using Gemini Flash (free tier)
Usage:
    python extract_memo.py --transcript data/demo_calls/ACC001_demo.txt --account_id ACC001 --mode demo
    python extract_memo.py --transcript data/onboarding_calls/ACC001_onboarding.txt --account_id ACC001 --mode onboarding
"""

import argparse
import json
import os
import re
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# ── Prompts ────────────────────────────────────────────────────────────────────

DEMO_EXTRACTION_PROMPT = """
You are a structured data extractor for a phone answering service company called Clara Answers.
Your job is to extract key operational details from a sales demo call transcript.

Return ONLY a valid JSON object — no markdown, no code fences, no explanation.
If a field is not mentioned in the transcript, set its value to null.
Never invent or guess values. Only extract what is explicitly stated.

Extract the following schema:

{
  "account_id": "<provided below>",
  "company_name": null,
  "business_hours": {
    "days": null,
    "start": null,
    "end": null,
    "timezone": null
  },
  "office_address": null,
  "services_supported": [],
  "emergency_definition": [],
  "emergency_routing_rules": {
    "primary_contact": null,
    "primary_phone": null,
    "secondary_contact": null,
    "secondary_phone": null,
    "fallback": null
  },
  "non_emergency_routing_rules": null,
  "call_transfer_rules": {
    "timeout_seconds": null,
    "retries": null,
    "message_if_fails": null
  },
  "integration_constraints": [],
  "after_hours_flow_summary": null,
  "office_hours_flow_summary": null,
  "questions_or_unknowns": [],
  "notes": null
}

ACCOUNT_ID: {account_id}

TRANSCRIPT:
{transcript}
"""

ONBOARDING_EXTRACTION_PROMPT = """
You are a structured data extractor for a phone answering service company called Clara Answers.
Your job is to extract ONLY the fields that are explicitly updated or confirmed during this onboarding call.
This is a PATCH — only include fields that were mentioned. Omit fields that were not discussed.

Return ONLY a valid JSON object — no markdown, no code fences, no explanation.
Never invent or guess values.

Use the same schema as below but only include keys that appear in the transcript:

{
  "company_name": null,
  "business_hours": {
    "days": null,
    "start": null,
    "end": null,
    "timezone": null
  },
  "office_address": null,
  "services_supported": [],
  "emergency_definition": [],
  "emergency_routing_rules": {
    "primary_contact": null,
    "primary_phone": null,
    "secondary_contact": null,
    "secondary_phone": null,
    "fallback": null
  },
  "non_emergency_routing_rules": null,
  "call_transfer_rules": {
    "timeout_seconds": null,
    "retries": null,
    "message_if_fails": null
  },
  "integration_constraints": [],
  "after_hours_flow_summary": null,
  "office_hours_flow_summary": null,
  "questions_or_unknowns": [],
  "notes": null
}

TRANSCRIPT:
{transcript}
"""

# ── Core Functions ─────────────────────────────────────────────────────────────

def load_transcript(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def extract_memo(transcript: str, account_id: str, mode: str) -> dict:
    """Call Gemini and return parsed memo dict."""
    if mode == "demo":
        prompt = DEMO_EXTRACTION_PROMPT.replace("{account_id}", account_id).replace("{transcript}", transcript)
    else:
        prompt = ONBOARDING_EXTRACTION_PROMPT.replace("{transcript}", transcript)

    print(f"  [extract_memo] Calling Gemini (mode={mode})...")
    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip any accidental markdown fences
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  [extract_memo] ERROR: Gemini returned invalid JSON: {e}")
        print(f"  Raw response:\n{raw}")
        raise

    # Always stamp account_id on demo extraction
    if mode == "demo":
        parsed["account_id"] = account_id

    return parsed


def save_memo(memo: dict, account_id: str, version: str) -> Path:
    out_dir = Path(f"outputs/accounts/{account_id}/{version}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "memo.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(memo, f, indent=2)
    print(f"  [extract_memo] Saved memo -> {out_path}")
    return out_path


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript", required=True, help="Path to transcript .txt file")
    parser.add_argument("--account_id", required=True, help="e.g. ACC001")
    parser.add_argument("--mode", choices=["demo", "onboarding"], default="demo")
    parser.add_argument("--version", default=None, help="Override version (v1 or v2)")
    args = parser.parse_args()

    version = args.version or ("v1" if args.mode == "demo" else "v2")

    transcript = load_transcript(args.transcript)
    memo = extract_memo(transcript, args.account_id, args.mode)
    save_memo(memo, args.account_id, version)
    print(f"  [extract_memo] Done. account_id={args.account_id} version={version}")


if __name__ == "__main__":
    main()
