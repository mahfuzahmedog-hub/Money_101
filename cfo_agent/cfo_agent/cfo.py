from core.db import get_connection
from core.event_logger import log_event
from core.config import get_config, set_config
from core.db import DB_PATH


class CFOAgent:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH

    def calculate_balance(self):
        conn = get_connection(self.db_path)
        income = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'income'"
        ).fetchone()[0]
        expense = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'expense'"
        ).fetchone()[0]
        conn.close()
        return income - expense

    def check_threshold(self):
        threshold = float(get_config("reinvestment_threshold", "30.0", db_path=self.db_path))
        balance = self.calculate_balance()
        if balance >= threshold:
            log_event("cfo_agent", "decision",
                      summary=f"Balance ${balance:.2f} meets threshold ${threshold:.2f}",
                      detail={"balance": balance, "threshold": threshold},
                      db_path=self.db_path)
            return True
        return False

    def propose_directive(self):
        balance = self.calculate_balance()
        threshold = float(get_config("reinvestment_threshold", "30.0", db_path=self.db_path))
        if not self.check_threshold():
            log_event("cfo_agent", "decision",
                      summary=f"Balance ${balance:.2f} below threshold ${threshold:.2f}, no action",
                      cost_usd=0.0, db_path=self.db_path)
            return

        has_paid = get_config("paid_tier_active", "false", db_path=self.db_path)
        if has_paid == "true":
            log_event("cfo_agent", "decision",
                      summary="Paid tier already active, no upgrade needed",
                      db_path=self.db_path)
            return

        conn = get_connection(self.db_path)
        conn.execute(
            """INSERT INTO directives (date, from_agent, directive_type, action, reason, status)
               VALUES (datetime('now'), 'cfo', 'proposal', 'upgrade_llm_tier',
                       ?, 'pending')""",
            (f"Balance ${balance:.2f} exceeds threshold. Propose adding paid priority-tier LLM.",),
        )
        conn.commit()
        conn.close()
        log_event("cfo_agent", "directive",
                  summary="Proposed LLM tier upgrade",
                  detail={"balance": balance, "threshold": threshold},
                  db_path=self.db_path)

    def run_daily(self):
        log_event("cfo_agent", "directive", summary="CFO daily check started", db_path=self.db_path)
        self.propose_directive()
        log_event("cfo_agent", "directive", summary="CFO daily check complete", db_path=self.db_path)
