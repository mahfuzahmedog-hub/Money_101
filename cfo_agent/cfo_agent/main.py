import os
from core.db import init_db, DB_PATH
from cfo_agent.cfo import CFOAgent

def main():
    print("=== CFO Agent — Daily Check ===")
    init_db(DB_PATH)
    cfo = CFOAgent(db_path=DB_PATH)
    cfo.run_daily()
    balance = cfo.calculate_balance()
    print(f"Balance: ${balance:.2f}")
    print("Done.")

if __name__ == "__main__":
    main()
