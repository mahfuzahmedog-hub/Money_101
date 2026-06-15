import asyncio
import os
import sys
from core.db import init_db, get_connection, DB_PATH
from core.event_logger import log_event
from operational_agent.vault import CredentialVault
from operational_agent.agent import run_cycle

PASSPHRASE = os.environ.get("AGENT_VAULT_KEY", "changeme-dev-key")


def store_manual_credentials():
    if len(sys.argv) < 4 or sys.argv[1] != "store":
        return False
    service = sys.argv[2]
    password = sys.argv[3]
    vault = CredentialVault(PASSPHRASE, db_path=DB_PATH)
    username = os.environ.get("FIVERR_EMAIL", "mahfuzahmed.og@gmail.com")
    vault.store(service, username, password, notes="Manually created account")
    print(f"Credentials stored for {service}: {username}")
    return True


async def main():
    print("=== Autonomous Business Agent — Operational Agent ===")
    print(f"DB: {DB_PATH}")

    init_db(DB_PATH)
    vault = CredentialVault(PASSPHRASE, db_path=DB_PATH)

    approval_mode = os.environ.get("APPROVAL_MODE", "true").lower() == "true"
    print(f"Approval mode: {approval_mode}")
    print("Starting cycle...\n")

    result = await run_cycle(vault, approval_mode=approval_mode)

    if result and "manual_account_creation" in result:
        password = result.split(":")[-1]
        print(f"\n{'='*60}")
        print("  FIVERR ACCOUNT NEEDS TO BE CREATED MANUALLY")
        print(f"{'='*60}")
        print(f"  1. Go to https://www.fiverr.com/join in your browser")
        print(f"  2. Sign up with:")
        print(f"     Email:    mahfuzahmed.og@gmail.com")
        print(f"     Username: alexm_content")
        print(f"     Password: {password}")
        print(f"  3. Verify via Gmail")
        print(f"  4. Run: python main.py store fiverr {password}")
        print(f"{'='*60}\n")
    elif result and result.startswith("handoff"):
        print(f"\nAgent paused at handoff: {result}")
        print("Check the dashboard at http://localhost:8080 for details.")
        print("Resolve the issue, then run the agent again.")

    print("\nDone.")


if __name__ == "__main__":
    if store_manual_credentials():
        sys.exit(0)
    asyncio.run(main())
