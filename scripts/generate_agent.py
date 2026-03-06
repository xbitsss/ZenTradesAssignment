"""
generate_agent.py
Account Memo JSON -> Retell Agent Draft Spec JSON
Usage:
    python generate_agent.py --account_id ACC001 --version v1
    python generate_agent.py --account_id ACC001 --version v2
"""

import argparse
import json
from pathlib import Path

# ── System Prompt Template ─────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are a professional virtual receptionist for {company_name}.

## Your Role
You answer calls on behalf of {company_name}. You are warm, concise, and efficient.
You do not mention that you are an AI unless directly asked. You never mention "function calls", "tools", or internal systems.

## Business Hours
{company_name} operates {business_days}, from {business_start} to {business_end} {timezone}.

## Office Hours Flow
When a caller contacts you during business hours:
1. Greet warmly: "Thank you for calling {company_name}, this is Clara. How can I help you today?"
2. Listen to their reason for calling.
3. If they need to speak with someone, collect: full name and callback number.
4. Attempt to transfer the call.
5. If transfer fails: "I wasn't able to connect you directly. I've noted your information and someone will call you back shortly. Is there anything else I can help you with?"
6. Confirm next steps and close warmly.

## After Hours Flow
When a caller contacts you outside of business hours:
1. Greet: "Thank you for calling {company_name}. Our office is currently closed. I'm here to assist you."
2. Ask: "Are you calling about an emergency or something that requires urgent attention?"
3. If YES (emergency): Collect full name, callback number, and service address immediately.
   - Attempt to reach the on-call contact.
   - If transfer fails: "I wasn't able to reach our on-call team directly. I've logged your emergency and someone will contact you as soon as possible. Please stay available at the number you provided."
4. If NO (non-emergency): "I'll make sure a team member follows up with you during business hours. Can I get your name and a good number to reach you?"
5. Always close: "Is there anything else I can help you with?" then thank them.

## Emergency Definition
The following situations are considered emergencies:
{emergency_definition}

## Emergency Routing
- Primary: {emergency_primary_contact} at {emergency_primary_phone}
- Secondary: {emergency_secondary_contact} at {emergency_secondary_phone}
- Fallback: {emergency_fallback}

## Non-Emergency Routing
{non_emergency_routing}

## Call Transfer Rules
- Wait up to {transfer_timeout} seconds for the call to connect.
- If no answer, retry {transfer_retries} time(s).
- If all attempts fail, say: "{transfer_fail_message}"

## Constraints
{integration_constraints}

## Key Rules
- Never ask more questions than necessary.
- Only collect name, number, and address when required for dispatch.
- Never mention internal tools, APIs, or system names to the caller.
- Always be warm, concise, and professional.
- If you are unsure, do not guess. Offer a callback.
"""


# ── Builder ────────────────────────────────────────────────────────────────────

def build_agent_spec(memo: dict, version: str) -> dict:
    """Construct the full Retell Agent Draft Spec from a memo."""

    bh = memo.get("business_hours") or {}
    er = memo.get("emergency_routing_rules") or {}
    tr = memo.get("call_transfer_rules") or {}

    # Format emergency definition as bullet list
    emergencies = memo.get("emergency_definition") or []
    emergency_str = "\n".join(f"- {e}" for e in emergencies) if emergencies else "- Not specified"

    # Format constraints
    constraints = memo.get("integration_constraints") or []
    constraints_str = "\n".join(f"- {c}" for c in constraints) if constraints else "- None specified"

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        company_name=memo.get("company_name") or "the company",
        business_days=bh.get("days") or "Monday through Friday",
        business_start=bh.get("start") or "8:00 AM",
        business_end=bh.get("end") or "5:00 PM",
        timezone=bh.get("timezone") or "local time",
        emergency_definition=emergency_str,
        emergency_primary_contact=er.get("primary_contact") or "on-call technician",
        emergency_primary_phone=er.get("primary_phone") or "[primary number not provided]",
        emergency_secondary_contact=er.get("secondary_contact") or "backup contact",
        emergency_secondary_phone=er.get("secondary_phone") or "[secondary number not provided]",
        emergency_fallback=er.get("fallback") or "Log the message and assure callback",
        non_emergency_routing=memo.get("non_emergency_routing_rules") or "Route to voicemail or log for next business day.",
        transfer_timeout=tr.get("timeout_seconds") or 30,
        transfer_retries=tr.get("retries") or 1,
        transfer_fail_message=tr.get("message_if_fails") or "I wasn't able to connect you. Someone will follow up shortly.",
        integration_constraints=constraints_str,
    )

    agent_spec = {
        "version": version,
        "account_id": memo.get("account_id"),
        "agent_name": f"{memo.get('company_name', 'Unknown')} - Clara Receptionist ({version})",
        "voice_style": "professional-warm",
        "language": "en-US",
        "system_prompt": system_prompt,
        "key_variables": {
            "company_name": memo.get("company_name"),
            "timezone": bh.get("timezone"),
            "business_hours": f"{bh.get('days')} {bh.get('start')}–{bh.get('end')} {bh.get('timezone')}",
            "office_address": memo.get("office_address"),
            "emergency_primary_phone": er.get("primary_phone"),
            "emergency_secondary_phone": er.get("secondary_phone"),
        },
        "tool_invocation_placeholders": [
            "transfer_call(phone_number)",
            "log_call(caller_name, caller_number, reason, is_emergency)",
            "send_sms_alert(contact_phone, message)"
        ],
        "call_transfer_protocol": {
            "method": "warm_transfer",
            "timeout_seconds": tr.get("timeout_seconds") or 30,
            "retries": tr.get("retries") or 1,
            "on_failure": tr.get("message_if_fails") or "I wasn't able to connect you. Someone will follow up shortly."
        },
        "fallback_protocol": {
            "action": "log_and_assure",
            "message": "I've noted your information and someone will reach out to you as soon as possible.",
            "escalation": er.get("fallback") or "No escalation path defined"
        }
    }

    return agent_spec


def save_agent_spec(spec: dict, account_id: str, version: str) -> Path:
    out_dir = Path(f"outputs/accounts/{account_id}/{version}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "agent_spec.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)
    print(f"  [generate_agent] Saved agent spec -> {out_path}")
    return out_path


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--account_id", required=True)
    parser.add_argument("--version", choices=["v1", "v2"], default="v1")
    args = parser.parse_args()

    memo_path = Path(f"outputs/accounts/{args.account_id}/{args.version}/memo.json")
    if not memo_path.exists():
        print(f"  [generate_agent] ERROR: memo not found at {memo_path}")
        raise SystemExit(1)

    with open(memo_path, "r") as f:
        memo = json.load(f)

    spec = build_agent_spec(memo, args.version)
    save_agent_spec(spec, args.account_id, args.version)
    print(f"  [generate_agent] Done. account_id={args.account_id} version={args.version}")


if __name__ == "__main__":
    main()
