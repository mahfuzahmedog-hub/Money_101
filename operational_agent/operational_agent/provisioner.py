import asyncio
import secrets
from core.event_logger import log_event
from core.db import get_connection, DB_PATH
from operational_agent.browser_controller import BrowserController
from operational_agent.vault import CredentialVault

PERSONA = {
    "name": "Alex Morgan",
    "email": "mahfuzahmed.og@gmail.com",
    "username": "alexm_content",
}


def _generate_password():
    return "Agt" + secrets.token_hex(8) + "!"


def _check_manual_account():
    conn = get_connection(DB_PATH)
    row = conn.execute("SELECT username, status FROM vault WHERE service='fiverr'").fetchone()
    conn.close()
    return row is not None and row["status"] == "active"


async def provision_fiverr(browser: BrowserController, vault: CredentialVault):
    log_event("provisioner", "account_creation",
              summary="Starting Fiverr account provisioning",
              detail={"email": PERSONA["email"], "username": PERSONA["username"]},
              db_path=DB_PATH)

    await browser.goto("https://www.fiverr.com/join")
    await asyncio.sleep(3)
    await browser._screenshot("fiverr_signup_page")

    page_title = ""
    try:
        page_title = await browser._page.title()
    except:
        pass

    if "human" in page_title.lower() or browser._page.url == "https://www.fiverr.com/join":
        has_inputs = await browser.is_visible("input", timeout=2000)
        if not has_inputs:
            password = _generate_password()
            log_event("provisioner", "account_creation",
                      summary="FIVERR BOT DETECTION — manual account creation needed",
                      detail={
                          "instructions": "Fiverr blocked the automated browser. Please create the account manually:",
                          "steps": [
                              f"1. Go to https://www.fiverr.com/join in your OWN browser (not this one)",
                              f"2. Sign up with: email={PERSONA['email']}, username={PERSONA['username']}",
                              f"3. Use password: {password}",
                              f"4. Verify your email at mail.google.com",
                              f"5. Once done, tell me 'account created' and I'll store the credentials"
                          ],
                          "email": PERSONA["email"],
                          "username": PERSONA["username"],
                          "generated_password": password,
                      },
                      status="pending", db_path=DB_PATH)
            await browser._screenshot("fiverr_bot_block")
            return f"handoff: manual_account_creation:{password}"

    for sel in ["input[name='email']", "input[type='email']", "#email"]:
        if await browser.is_visible(sel, timeout=2000):
            await browser.fill(sel, PERSONA["email"])
            break

    for sel in ["input[name='username']", "#username"]:
        if await browser.is_visible(sel, timeout=2000):
            await browser.fill(sel, PERSONA["username"])
            break

    for sel in ["input[name='password']", "input[type='password']", "#password"]:
        if await browser.is_visible(sel, timeout=2000):
            password = _generate_password()
            await browser.fill(sel, password)
            break

    await browser._screenshot("fiverr_form_filled")

    for btn_sel in ["button[type='submit']", "button:has-text('Join')", "button:has-text('Sign Up')", "[data-test='submit']"]:
        if await browser.is_visible(btn_sel, timeout=2000):
            await browser.click(btn_sel)
            break

    await asyncio.sleep(4)
    await browser._screenshot("fiverr_after_submit")

    has_captcha = await browser.is_visible(
        "[aria-label*='captcha' i], iframe[src*='recaptcha'], [src*='challenge']",
        timeout=3000,
    )
    if has_captcha:
        log_event("provisioner", "account_creation",
                  summary="CAPTCHA detected — human help needed to solve it",
                  detail={"email": PERSONA["email"]},
                  status="pending", db_path=DB_PATH)
        return "handoff: captcha"

    needs_verification = await browser.is_visible("text=verify", timeout=3000) or \
                         await browser.is_visible("text=check your email", timeout=3000)
    if needs_verification:
        log_event("provisioner", "account_creation",
                  summary="EMAIL VERIFICATION — check Gmail inbox",
                  detail={
                      "instructions": f"Check mail.google.com for the Fiverr verification email. Click the link, then the agent can proceed.",
                      "email": PERSONA["email"],
                  },
                  status="pending", db_path=DB_PATH)
        await browser._screenshot("fiverr_verify_email")
        return "handoff: email_verification"

    success = "fiverr.com/dashboard" in browser._page.url
    if not success:
        try:
            success = await browser.is_visible("text=Welcome", timeout=3000)
        except:
            pass

    if success:
        vault.store("fiverr", PERSONA["email"], password,
                    notes=f"Fiverr account for {PERSONA['name']}")
        log_event("provisioner", "account_creation",
                  summary="Fiverr account created successfully",
                  status="success", db_path=DB_PATH)
        return "success"

    log_event("provisioner", "account_creation",
              summary="UNKNOWN STATE — check dashboard screenshot",
              detail={"url": browser._page.url, "title": page_title},
              status="pending", db_path=DB_PATH)
    return f"handoff: unknown_state"
