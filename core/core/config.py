from core.db import get_connection


def get_config(key, default=None, db_path=None):
    conn = get_connection(db_path)
    row = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_config(key, value, db_path=None):
    conn = get_connection(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value)
    )
    conn.commit()
    conn.close()
