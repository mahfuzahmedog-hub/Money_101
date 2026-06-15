import os
import time
import httpx
from core.db import get_connection
from core.event_logger import log_event

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")


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


def call_groq(prompt, model="llama-3.3-70b-versatile", tier="standard"):
    key = GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
    if not key:
        return None, "no_groq_key"
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    start = time.time()
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=60)
        latency = (time.time() - start) * 1000
        if resp.status_code == 429:
            return None, "rate_limited"
        if resp.status_code != 200:
            return None, f"http_{resp.status_code}"
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return {
            "content": text,
            "provider": "groq",
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


def call_openrouter(prompt, model="meta-llama/llama-3.3-70b-instruct", tier="standard"):
    key = OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return None, "no_openrouter_key"
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/mahfuzahmedog-hub/Money_101",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    start = time.time()
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=60)
        latency = (time.time() - start) * 1000
        if resp.status_code == 429:
            return None, "rate_limited"
        if resp.status_code != 200:
            return None, f"http_{resp.status_code}"
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return {
            "content": text,
            "provider": "openrouter",
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
    {
        "name": "groq",
        "model": "llama-3.3-70b-versatile",
        "limit_type": "requests_per_day",
        "limit_value": 14400,
        "tier": "standard,bulk",
        "priority_order": 3,
        "call_fn": call_groq,
    },
    {
        "name": "groq-fast",
        "model": "llama-3.1-8b-instant",
        "limit_type": "requests_per_day",
        "limit_value": 14400,
        "tier": "bulk",
        "priority_order": 4,
        "call_fn": call_groq,
    },
    {
        "name": "openrouter-llama",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "limit_type": "requests_per_day",
        "limit_value": 200,
        "tier": "standard,priority",
        "priority_order": 5,
        "call_fn": call_openrouter,
    },
    {
        "name": "openrouter-gemma",
        "model": "google/gemma-4-31b-it:free",
        "limit_type": "requests_per_day",
        "limit_value": 200,
        "tier": "standard,bulk",
        "priority_order": 6,
        "call_fn": call_openrouter,
    },
    {
        "name": "openrouter-qwen",
        "model": "qwen/qwen3-coder:free",
        "limit_type": "requests_per_day",
        "limit_value": 200,
        "tier": "bulk",
        "priority_order": 7,
        "call_fn": call_openrouter,
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
