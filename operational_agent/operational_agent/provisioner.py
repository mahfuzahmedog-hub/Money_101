import asyncio
import secrets
import string
from core.event_logger import log_event
from core.db import DB_PATH
from operational_agent.browser_controller import BrowserController
from operational_agent.vault import CredentialVault

PERSONA = {
    "name": "Alex Morgan",
    "email": "mahfuzahmed.og@gmail.com",
    "username": "alexm_content",
}


def _generate_password():
    return "Agt" + secrets.token_hex(8) + "!"


async def provision_fiverr(browser: BrowserController, vault: CredentialVault):
    password = _generate_password()

    log_event("provisioner", "account_creation",
              summary="Starting Fiverr account provisioning",
              detail={"email": PERSONA["email"], "username": PERSONA["username"]},
              db_path=DB_PATH)

    await browser.goto("https://www.fiverr.com/join")
    await asyncio.sleep(3)
    await browser._screenshot("fiverr_signup_page")

    for sel in ["input[name='email']", "input[type='email']", "#email"]:
        if await browser.is_visible(sel):
            await browser.fill(sel, PERSONA["email"])
            break

    for sel in ["input[name='username']", "#username"]:
        if await browser.is_visible(sel):
            await browser.fill(sel, PERSONA["username"])
            break

    for sel in ["input[name='password']", "input[type='password']", "#password"]:
        if await browser.is_visible(sel):
            await browser.fill(sel, password)
            break

    await browser._screenshot("fiverr_form_filled")

    for btn_sel in ["button[type='submit']", "button:has-text('Join')", "button:has-text('Sign Up')", "[data-test='submit']"]:
        if await browser.is_visible(btn_sel):
            await browser.click(btn_sel)
            break

    await asyncio.sleep(4)
    await browser._screenshot("fiverr_after_submit")

    has_captcha = await browser.is_visible(
        "[aria-label*='captcha' i], [aria-label*='recaptcha' i], iframe[src*='recaptcha'], [src*='challenge']"
    )
    if has_captcha:
        log_event("provisioner", "account_creation",
                  summary="CAPTCHA detected — human help needed",
                  detail={"email": PERSONA["email"]},
                  status="pending", db_path=DB_PATH)
        return "handoff: captcha"

    needs_verification = await browser.is_visible("text=verify", timeout=3000) or \
                         await browser.is_visible("text=check your email", timeout=3000)
    if needs_verification:
        log_event("provisioner", "account_creation",
                  summary="EMAIL VERIFICATION NEEDED — check Gmail inbox for Fiverr verification link",
                  detail={
                      "email": PERSONA["email"],
                      "instructions": "Open mail.google.com, find the Fiverr verification email, click the link, then come back here. The agent will wait.",
                  },
                  status="pending", db_path=DB_PATH)
        await browser._screenshot("fiverr_verify_email")
        return "handoff: email_verification"

    success = await browser.is_visible("text=Welcome", timeout=3000) or \
              await browser.is_visible("[data-test='dashboard']", timeout=3000) or \
              "fiverr.com/dashboard" in browser._page.url

    if success:
        vault.store("fiverr", PERSONA["email"], password,
                    notes=f"Fiverr account for {PERSONA['name']}")
        log_event("provisioner", "account_creation",
                  summary="Fiverr account created successfully",
                  status="success", db_path=DB_PATH)
        return "success"

    log_event("provisioner", "account_creation",
              summary="UNKNOWN STATE — human check needed (check dashboard screenshot)",
              detail={"url": browser._page.url, "email": PERSONA["email"]},
              status="pending", db_path=DB_PATH)
    return "handoff: unknown_state"
