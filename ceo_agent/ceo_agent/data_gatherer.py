from core.db import get_connection
from core.db import DB_PATH


class DataGatherer:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH

    def get_task_summary(self):
        conn = get_connection(self.db_path)
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status"
        ).fetchall()
        conn.close()
        return {r["status"]: r["cnt"] for r in rows}

    def get_outcome_aggregation(self):
        conn = get_connection(self.db_path)
        rows = conn.execute("""
            SELECT niche, COUNT(*) as attempts,
                   SUM(CASE WHEN converted = 1 THEN 1 ELSE 0 END) as successes,
                   AVG(price) as avg_price
            FROM outcomes GROUP BY niche
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_financial_summary(self):
        conn = get_connection(self.db_path)
        income = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'income'"
        ).fetchone()[0]
        expense = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'expense'"
        ).fetchone()[0]
        conn.close()
        return {"income": income, "expense": expense, "balance": income - expense}
