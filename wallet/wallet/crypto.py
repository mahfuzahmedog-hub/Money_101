from core.event_logger import log_event
from core.db import get_connection, DB_PATH


class WalletManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH

    def get_address(self):
        conn = get_connection(self.db_path)
        row = conn.execute(
            "SELECT value FROM config WHERE key = 'wallet_address'"
        ).fetchone()
        conn.close()
        return row["value"] if row else None

    def set_address(self, address):
        conn = get_connection(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('wallet_address', ?)",
            (address,),
        )
        conn.commit()
        conn.close()
        log_event("wallet", "onchain_tx",
                  summary=f"Wallet address set to {address}",
                  db_path=self.db_path)

    def record_transaction(self, tx_hash, amount, tx_type, source):
        conn = get_connection(self.db_path)
        conn.execute(
            """INSERT INTO transactions (date, amount, source, type, tx_hash)
               VALUES (datetime('now'), ?, ?, ?, ?)""",
            (amount, source, tx_type, tx_hash),
        )
        conn.commit()
        conn.close()
        log_event("wallet", "onchain_tx",
                  summary=f"Transaction recorded: {tx_type} ${amount:.2f}",
                  detail={"tx_hash": tx_hash, "source": source},
                  db_path=self.db_path)
