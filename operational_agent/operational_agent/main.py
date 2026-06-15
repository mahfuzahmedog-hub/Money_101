import asyncio
import os
import sys
from core.db import init_db, DB_PATH
from core.event_logger import log_event
from operational_agent.vault import CredentialVault
from operational_agent.agent import run_cycle

PASSPHRASE = os.environ.get("AGENT_VAULT_KEY", "changeme-dev-key")


async def main():
    print("=== Autonomous Business Agent — Operational Agent ===")
    print(f"DB: {DB_PATH}")

    init_db(DB_PATH)
    vault = CredentialVault(PASSPHRASE, db_path=DB_PATH)

    approval_mode = os.environ.get("APPROVAL_MODE", "true").lower() == "true"
    print(f"Approval mode: {approval_mode}")
    print("Starting cycle...\n")

    await run_cycle(vault, approval_mode=approval_mode)
    print("\nCycle complete. Check the database for results.")


if __name__ == "__main__":
    asyncio.run(main())
