import json
from core.db import get_connection, utcnow


def log_event(
    agent_id,
    event_type,
    summary=None,
    detail=None,
    cost_usd=None,
    status="success",
    db_path=None,
):
    conn = get_connection(db_path)
    detail_json = json.dumps(detail) if detail else None
    conn.execute(
        """
        INSERT INTO events (timestamp, agent_id, event_type, summary, detail, cost_usd, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (utcnow(), agent_id, event_type, summary, detail_json, cost_usd, status),
    )
    conn.commit()
    event_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return event_id
