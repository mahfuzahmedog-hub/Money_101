import time
from core.db import get_connection
from core.event_logger import log_event
from llm_router.providers import get_providers_for_tier, mark_exhausted, call_gemini


def call_llm(prompt, tier="standard", exclude_provider=None, db_path=None):
    providers = get_providers_for_tier(tier, exclude=exclude_provider, db_path=db_path)
    if not providers:
        log_event(
            "llm_router", "error",
            summary=f"No providers available for tier '{tier}'",
            detail={"tier": tier, "exclude": exclude_provider},
            status="failure",
            db_path=db_path,
        )
        return None

    for p in providers:
        provider_name = p["provider"]
        model = p["model"]
        call_fn = p.get("call_fn", call_gemini)
        result, err = call_fn(prompt, model=model, tier=tier)
        if result:
            conn = get_connection(db_path)
            conn.execute(
                "UPDATE llm_quota_ledger SET used_today = used_today + 1 WHERE provider = ?",
                (provider_name,),
            )
            conn.commit()
            conn.close()
            log_event(
                "llm_router", "llm_call",
                summary=f"{provider_name}/{model} ({tier})",
                detail={"prompt_preview": prompt[:200], "tokens": result["tokens"]},
                cost_usd=result["cost_usd"],
                status="success",
                db_path=db_path,
            )
            return result
        elif err == "rate_limited":
            log_event(
                "llm_router", "llm_call",
                summary=f"{provider_name} rate limited, marking exhausted",
                detail={"provider": provider_name},
                status="failure",
                db_path=db_path,
            )
            mark_exhausted(provider_name, db_path=db_path)
            continue
        else:
            log_event(
                "llm_router", "error",
                summary=f"{provider_name} call failed: {err}",
                detail={"provider": provider_name, "error": err},
                status="failure",
                db_path=db_path,
            )
            continue

    log_event(
        "llm_router", "decision",
        summary=f"All providers exhausted for tier '{tier}', consider adding paid capacity",
        detail={"tier": tier, "exclude": exclude_provider},
        status="failure",
        db_path=db_path,
    )
    return None
