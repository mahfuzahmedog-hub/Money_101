import os
import time
import httpx
from core.db import get_connection
from core.event_logger import log_event

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


def call_gemini(prompt, model="gemini-2.5-flash", tier="standard"):
    key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return None, "no_gemini_key"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    start = time.time()
    try:
        resp = httpx.post(url, json=payload, timeout=60)
        latency = (time.time() - start) * 1000
        if resp.status_code == 429:
            return None, "rate_limited"
        if resp.status_code != 200:
            return None, f"http_{resp.status_code}"
        data = resp.json()
        text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
        return {
            "content": text,
            "provider": "gemini",
            "model": model,
            "tier": tier,
            "tokens": tokens,
            "cost_usd": 0.0,
            "latency_ms": round(latency, 1),
            "success": True,
        }, None
    except httpx.TimeoutException:
        return None, "timeout"
    except Exception as e:
        return None, f"error: {e}"


FREE_PROVIDERS = [
    {
        "name": "gemini",
        "model": "gemini-2.5-flash",
        "limit_type": "requests_per_day",
        "limit_value": 1500,
        "tier": "priority,standard",
        "priority_order": 1,
        "call_fn": call_gemini,
    },
    {
        "name": "gemini-pro",
        "model": "gemini-2.5-pro",
        "limit_type": "requests_per_day",
        "limit_value": 50,
        "tier": "priority",
        "priority_order": 2,
        "call_fn": call_gemini,
    },
]


def seed_quota_ledger(db_path=None):
    conn = get_connection(db_path)
    for p in FREE_PROVIDERS:
        conn.execute(
            """INSERT OR IGNORE INTO llm_quota_ledger
               (provider, model, limit_type, limit_value, tier, priority_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (p["name"], p["model"], p["limit_type"], p["limit_value"], p["tier"], p["priority_order"]),
        )
    conn.commit()
    conn.close()


def get_providers_for_tier(tier, exclude=None, db_path=None):
    conn = get_connection(db_path)
    tier_lower = tier.lower()
    rows = conn.execute(
        """SELECT * FROM llm_quota_ledger
           WHERE tier LIKE ? AND used_today < limit_value
           ORDER BY priority_order""",
        (f"%{tier_lower}%",),
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        if exclude and row["provider"] == exclude:
            continue
        p = next((fp for fp in FREE_PROVIDERS if fp["name"] == row["provider"]), None)
        if p:
            results.append({**row, "call_fn": p["call_fn"]})
    return results


def mark_exhausted(provider, db_path=None):
    conn = get_connection(db_path)
    conn.execute(
        "UPDATE llm_quota_ledger SET used_today = limit_value WHERE provider = ?",
        (provider,),
    )
    conn.commit()
    conn.close()
