import asyncio
from core.event_logger import log_event
from core.db import DB_PATH
from operational_agent.browser_controller import BrowserController
from operational_agent.vault import CredentialVault


PERSONA = {
    "name": "Alex Morgan",
    "email": "alex.m@example.com",
    "username": "alexm_creator",
}


async def provision_fiverr(browser: BrowserController, vault: CredentialVault):
    log_event("provisioner", "account_creation",
              summary="Starting Fiverr account provisioning",
              detail={"persona": PERSONA["name"]}, db_path=DB_PATH)

    await browser.goto("https://www.fiverr.com/join")
    await asyncio.sleep(2)

    has_captcha = await browser.is_visible("[aria-label*='captcha' i], [aria-label*='recaptcha' i], iframe[src*='recaptcha']")
    if has_captcha:
        log_event("provisioner", "account_creation",
                  summary="CAPTCHA detected — handoff required",
                  status="pending", db_path=DB_PATH)
        return "handoff: captcha"

    await browser.fill("input[name='email']", PERSONA["email"])
    await browser.fill("input[name='username']", PERSONA["username"])
    await browser.fill("input[name='password']", "TempPass123!")
    await browser.click("button[type='submit']")
    await asyncio.sleep(3)

    needs_verification = await browser.is_visible("text=verify your email")
    if needs_verification:
        log_event("provisioner", "account_creation",
                  summary="Email verification needed — handoff required",
                  detail={"email": PERSONA["email"]},
                  status="pending", db_path=DB_PATH)
        return "handoff: email_verification"

    success = await browser.is_visible("text=Welcome to Fiverr")
    if success:
        vault.store("fiverr", PERSONA["email"], "TempPass123!",
                    notes=f"Fiverr account for {PERSONA['name']}")
        log_event("provisioner", "account_creation",
                  summary="Fiverr account created successfully",
                  status="success", db_path=DB_PATH)
        return "success"

    log_event("provisioner", "account_creation",
              summary="Fiverr signup — unexpected state, handoff",
              detail={"url": browser._page.url},
              status="pending", db_path=DB_PATH)
    return "handoff: unknown_state"
