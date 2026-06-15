from core.db import get_connection, DB_PATH
from core.event_logger import log_event
from llm_router.router import call_llm


class OverseerAgent:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH

    def generate_report(self):
        conn = get_connection(self.db_path)
        event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        pending_directives = conn.execute(
            "SELECT COUNT(*) FROM directives WHERE status = 'pending'"
        ).fetchone()[0]
        balance = conn.execute(
            "SELECT COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE -amount END), 0) FROM transactions"
        ).fetchone()[0]
        conn.close()

        summary = f"""Daily Report
====================
Events logged: {event_count}
Pending directives: {pending_directives}
Current balance: ${balance:.2f}
"""
        log_event("overseer", "directive",
                  summary="Daily report generated",
                  detail={"report": summary},
                  db_path=self.db_path)
        return summary
