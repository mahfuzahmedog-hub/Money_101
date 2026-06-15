import os
from core.db import init_db, DB_PATH
from ceo_agent.ceo import CEOAgent

def main():
    print("=== CEO Agent — Weekly Cycle ===")
    init_db(DB_PATH)
    ceo = CEOAgent(db_path=DB_PATH)
    ceo.run_weekly()
    print("Done. Check directives table for the proposal.")

if __name__ == "__main__":
    main()
