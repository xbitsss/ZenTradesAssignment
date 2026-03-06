"""
create_task.py
Creates and updates Notion tasks for account tracking.
Gracefully skips if NOTION_API_KEY is not set.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_VERSION = "2022-06-28"


def _headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def create_notion_task(account_id: str, company_name: str, version: str, status: str, notes: str = "") -> str | None:
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        return None  # Skip silently if not configured

    # Check if a page already exists for this account_id to stay idempotent
    existing = _find_page(account_id)
    if existing:
        print(f"  [create_task] Task already exists for {account_id}, skipping creation.")
        return existing

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": f"{company_name} ({account_id})"}}]},
            "Account ID": {"rich_text": [{"text": {"content": account_id}}]},
            "Status": {"select": {"name": status}},
            "Version": {"select": {"name": version}},
            "Notes": {"rich_text": [{"text": {"content": notes}}]},
        }
    }

    resp = requests.post("https://api.notion.com/v1/pages", headers=_headers(), json=payload)
    if resp.status_code == 200:
        page_id = resp.json().get("id")
        print(f"  [create_task] Notion task created: {page_id}")
        return page_id
    else:
        print(f"  [create_task] Notion API error: {resp.status_code} {resp.text}")
        return None


def update_notion_task(account_id: str, status: str) -> bool:
    if not NOTION_API_KEY:
        return False

    page_id = _find_page(account_id)
    if not page_id:
        print(f"  [create_task] No existing Notion task found for {account_id}")
        return False

    payload = {
        "properties": {
            "Status": {"select": {"name": status}},
            "Version": {"select": {"name": "v2"}},
        }
    }

    resp = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=_headers(), json=payload)
    if resp.status_code == 200:
        print(f"  [create_task] Notion task updated for {account_id}")
        return True
    else:
        print(f"  [create_task] Notion update error: {resp.status_code} {resp.text}")
        return False


def _find_page(account_id: str) -> str | None:
    """Query Notion DB for a page matching account_id."""
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        return None

    payload = {
        "filter": {
            "property": "Account ID",
            "rich_text": {"equals": account_id}
        }
    }
    resp = requests.post(
        f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query",
        headers=_headers(),
        json=payload
    )
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        if results:
            return results[0]["id"]
    return None
