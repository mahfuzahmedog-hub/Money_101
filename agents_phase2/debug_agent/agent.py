from core.db import get_connection, DB_PATH
from core.event_logger import log_event
from llm_router.router import call_llm


class DebugAgent:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH

    def check_recent_errors(self):
        conn = get_connection(self.db_path)
        errors = conn.execute(
            "SELECT id, summary, detail FROM events WHERE event_type = 'error' AND status = 'failure' ORDER BY id DESC LIMIT 5"
        ).fetchall()
        conn.close()
        for err in errors:
            log_event("debug_agent", "directive",
                      summary=f"Diagnosing error #{err['id']}: {err['summary']}",
                      detail={"event_id": err["id"]},
                      db_path=self.db_path)
