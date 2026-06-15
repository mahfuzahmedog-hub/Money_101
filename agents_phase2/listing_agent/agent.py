from core.event_logger import log_event
from core.db import get_connection, DB_PATH
from llm_router.router import call_llm

class ListingAgent:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH

    def refresh_listings(self):
        conn = get_connection(self.db_path)
        underperforming = conn.execute(
            "SELECT id, niche, price FROM outcomes WHERE converted = 0 OR converted IS NULL"
        ).fetchall()
        conn.close()
        for listing in underperforming:
            log_event("listing_agent", "directive",
                      summary=f"Would refresh listing: {listing['niche']}",
                      detail={"id": listing["id"]},
                      db_path=self.db_path)
