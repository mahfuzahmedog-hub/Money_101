import asyncio
from core.event_logger import log_event
from core.db import DB_PATH
from operational_agent.browser_controller import BrowserController
from operational_agent.vault import CredentialVault
from operational_agent.provisioner import provision_fiverr
from operational_agent.listing_builder import build_listings, save_outcomes


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
                      summary="No Fiverr credentials found — beginning provisioning",
                      db_path=DB_PATH)
            result = await provision_fiverr(browser, vault)

            if result.startswith("handoff"):
                log_event("operational_agent", "directive",
                          summary=f"HANDOFF NEEDED: {result}",
                          detail={"handoff_reason": result},
                          status="pending", db_path=DB_PATH)
                print(f"\n=== HUMAN INTERVENTION NEEDED ===")
                print(f"Reason: {result}")
                print(f"Check the dashboard at http://localhost:8080 to see screenshots and details.")
                print(f"Resume the agent when ready.\n")
                return result

            username, password = vault.retrieve("fiverr")

        if username and password:
            log_event("operational_agent", "directive",
                      summary=f"Logging into Fiverr as {username}", db_path=DB_PATH)
            await browser.goto("https://www.fiverr.com/login")
            await asyncio.sleep(2)

            for sel in ["input[name='email']", "input[type='email']", "#email"]:
                if await browser.is_visible(sel):
                    await browser.fill(sel, username)
                    break

            for sel in ["input[name='password']", "input[type='password']", "#password"]:
                if await browser.is_visible(sel):
                    await browser.fill(sel, password)
                    break

            for btn in ["button[type='submit']", "button:has-text('Sign In')", "#login-submit"]:
                if await browser.is_visible(btn):
                    await browser.click(btn)
                    break

            await asyncio.sleep(3)
            await browser._screenshot("after_login")

        listings = build_listings(db_path=DB_PATH)
        save_outcomes(listings, db_path=DB_PATH)

        if approval_mode:
            print(f"\n=== APPROVAL MODE ===")
            print(f"Generated {len(listings)} listing candidates.")
            print(f"Saved to outcomes table for review.")
            print(f"Set APPROVAL_MODE=false to post live.\n")
        else:
            log_event("operational_agent", "directive",
                      summary=f"Posting {len(listings)} listings to Fiverr",
                      detail={"count": len(listings)}, db_path=DB_PATH)

    finally:
        await browser.close()

    log_event("operational_agent", "directive",
              summary="Operational agent cycle complete", db_path=DB_PATH)
    return "complete"
