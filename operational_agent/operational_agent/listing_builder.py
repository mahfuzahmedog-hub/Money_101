from core.event_logger import log_event
from core.db import get_connection, DB_PATH
from llm_router.router import call_llm


LISTINGS_SYSTEM_PROMPT = """You are a Fiverr gig listing creator. Create a clear, scoped service listing.

Given a niche and desired price point, produce a JSON object with these fields:
- title: short, clear gig title (max 80 chars)
- category: Fiverr category
- description: 2-3 paragraph description focused on buyer value, scope, and delivery
- price: the price in USD
- delivery_days: estimated delivery in days (1-7)
- keywords: 3-5 relevant tags

Output valid JSON only."""


LISTING_CANDIDATES = [
    {"niche": "research_summaries", "price": 15},
    {"niche": "data_cleanup_formatting", "price": 10},
    {"niche": "short_form_content", "price": 20},
    {"niche": "spreadsheet_templates", "price": 25},
    {"niche": "ai_prompt_engineering", "price": 30},
]


def build_listings(db_path=None):
    outcomes = []
    for candidate in LISTING_CANDIDATES:
        prompt = f"Create a Fiverr gig listing for niche: {candidate['niche']}, target price: ${candidate['price']}"
        result = call_llm(prompt, tier="priority", db_path=db_path)
        if result and result.get("content"):
            listing = result["content"]
            oc = dict(
                task_type="gig_listing",
                platform="fiverr",
                niche=candidate["niche"],
                price=candidate["price"],
                content_summary=listing,
                llm_tier_used="priority",
            )
            outcomes.append(oc)
            log_event("listing_builder", "decision",
                      summary=f"Built listing: {candidate['niche']} @ ${candidate['price']}",
                      detail={"niche": candidate["niche"], "price": candidate["price"], "listing": listing},
                      db_path=db_path)
        else:
            log_event("listing_builder", "error",
                      summary=f"Failed to build listing for {candidate['niche']}",
                      status="failure", db_path=db_path)
    return outcomes


def save_outcomes(outcomes, db_path=None):
    conn = get_connection(db_path)
    for oc in outcomes:
        conn.execute(
            """INSERT INTO outcomes (task_type, platform, niche, price, content_summary, posting_time, llm_tier_used)
               VALUES (?, ?, ?, ?, ?, datetime('now'), ?)""",
            (oc["task_type"], oc["platform"], oc["niche"], oc["price"], oc["content_summary"], oc["llm_tier_used"]),
        )
    conn.commit()
    conn.close()
