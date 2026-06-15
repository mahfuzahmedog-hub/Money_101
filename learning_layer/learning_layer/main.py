from core.db import init_db, DB_PATH
from learning_layer.outcome_tracker import update_outcomes

def main():
    print("=== Learning Layer ===")
    init_db(DB_PATH)
    pending = update_outcomes(db_path=DB_PATH)
    print(f"Pending outcomes to check: {pending}")
    print("Done.")

if __name__ == "__main__":
    main()
