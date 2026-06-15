import asyncio
from core.event_logger import log_event
from core.db import DB_PATH
from operational_agent.browser_controller import BrowserController
from operational_agent.vault import CredentialVault
from operational_agent.provisioner import provision_fiverr
from operational_agent.listing_builder import build_listings, save_outcomes

APPROVAL_CONFIG_KEY = "operational_agent.approval_mode"


async def run_cycle(vault: CredentialVault, approval_mode=True):
    log_event("operational_agent", "directive",
              summary="Starting operational agent cycle",
              detail={"approval_mode": approval_mode}, db_path=DB_PATH)

    browser = BrowserController(headless=True)
    await browser.start()

    try:
        username, password = vault.retrieve("fiverr")
        if not username:
            log_event("operational_agent", "directive",
                      summary="No Fiverr credentials found — provisioning",
                      db_path=DB_PATH)
            result = await provision_fiverr(browser, vault)
            if result.startswith("handoff"):
                log_event("operational_agent", "directive",
                          summary=f"Provisioning needs human: {result}",
                          detail={"handoff_reason": result},
                          status="failure", db_path=DB_PATH)
                return

        username, password = vault.retrieve("fiverr")
        if username:
            log_event("operational_agent", "directive",
                      summary=f"Logging into Fiverr as {username}", db_path=DB_PATH)
            await browser.goto("https://www.fiverr.com/login")
            await asyncio.sleep(2)
            await browser.fill("input[name='email']", username)
            await browser.fill("input[name='password']", password)
            await browser.click("button[type='submit']")
            await asyncio.sleep(3)
        else:
            log_event("operational_agent", "error",
                      summary="No Fiverr credentials available",
                      status="failure", db_path=DB_PATH)
            return

        listings = build_listings(db_path=DB_PATH)
        save_outcomes(listings, db_path=DB_PATH)

        if approval_mode:
            log_event("operational_agent", "decision",
                      summary="Approval mode — listings saved to outcomes, not posted live",
                      detail={"listing_count": len(listings)},
                      db_path=DB_PATH)
        else:
            log_event("operational_agent", "directive",
                      summary="Posting mode — would submit listings to Fiverr",
                      detail={"listing_count": len(listings)},
                      db_path=DB_PATH)

    finally:
        await browser.close()

    log_event("operational_agent", "directive",
              summary="Operational agent cycle complete",
              detail={"listings_created": len(listings) if 'listings' in dir() else 0},
              db_path=DB_PATH)
