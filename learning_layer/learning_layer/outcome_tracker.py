from core.db import get_connection, DB_PATH
from core.event_logger import log_event


def update_outcomes(db_path=None):
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT id, task_type, platform FROM outcomes WHERE converted IS NULL"
    ).fetchall()
    conn.close()
    for row in rows:
        log_event("outcome_tracker", "directive",
                  summary=f"Would check outcome for {row['task_type']} on {row['platform']} (id={row['id']})",
                  detail={"outcome_id": row["id"]},
                  status="pending", db_path=db_path)
    return len(rows)
