from core.db import get_connection, DB_PATH
from core.event_logger import log_event
from ceo_agent.data_gatherer import DataGatherer
from llm_router.router import call_llm


class CEOAgent:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.gatherer = DataGatherer(db_path)

    def _build_context(self):
        tasks = self.gatherer.get_task_summary()
        outcomes = self.gatherer.get_outcome_aggregation()
        financial = self.gatherer.get_financial_summary()
        return f"""Context for this week's strategy review:

Tasks: {tasks}
Financial: Income ${financial['income']:.2f}, Expenses ${financial['expense']:.2f}, Balance ${financial['balance']:.2f}
Outcomes by niche: {outcomes}
"""

    def run_weekly(self):
        log_event("ceo_agent", "directive", summary="CEO weekly cycle started", db_path=self.db_path)
        context = self._build_context()

        prompt = f"""{context}

Based on this data, decide whether to:
1. CONTINUE — current approach is working, no changes needed
2. ADJUST — tweak pricing, wording, or timing
3. PIVOT — try a different niche or platform

Output your decision as JSON: {{"action": "continue|adjust|pivot", "reason": "..."}}
"""
        result = call_llm(prompt, tier="standard", db_path=self.db_path)
        if not result or not result.get("content"):
            log_event("ceo_agent", "error",
                      summary="CEO proposal failed — no LLM response",
                      status="failure", db_path=self.db_path)
            return

        conn = get_connection(self.db_path)
        conn.execute(
            """INSERT INTO directives (date, from_agent, directive_type, model_used, action, reason, status)
               VALUES (datetime('now'), 'ceo', 'proposal', ?, ?, ?, 'pending')""",
            (result.get("model", "unknown"), result["content"][:500], result["content"]),
        )
        conn.commit()
        proposal_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        action = "continue"
        if '"adjust"' in result["content"].lower() or '"pivot"' in result["content"].lower():
            action = "adjust"
        if '"pivot"' in result["content"].lower():
            action = "pivot"

        if action in ("adjust", "pivot"):
            exclude = result.get("provider")
            critique = call_llm(
                f"Review this proposal and raise any concerns:\n{result['content']}\n\nContext:\n{context}",
                tier="standard",
                exclude_provider=exclude,
                db_path=self.db_path,
            )
            if critique and critique.get("content"):
                conn = get_connection(self.db_path)
                conn.execute(
                    """INSERT INTO directives (date, from_agent, directive_type, related_directive_id, model_used, action, reason, status)
                       VALUES (datetime('now'), 'ceo', 'critique', ?, ?, ?, ?, 'pending')""",
                    (proposal_id, critique.get("model", "unknown"), critique["content"][:500], critique["content"]),
                )
                conn.commit()
                conn.close()

        log_event("ceo_agent", "directive",
                  summary=f"CEO cycle complete — action: {action}",
                  detail={"proposal_id": proposal_id, "action": action},
                  db_path=self.db_path)
