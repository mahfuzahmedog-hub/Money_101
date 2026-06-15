import os
import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from core.db import get_connection, DB_PATH

app = FastAPI(title="Agent Dashboard")

HERE = Path(__file__).parent
SCREENSHOT_DIR = Path(os.path.dirname(DB_PATH or "agent_data.db")) / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(HERE / "templates"))


@app.get("/")
async def home():
    return RedirectResponse(url="/live")


@app.get("/live", response_class=HTMLResponse)
async def live_feed(request: Request):
    conn = get_connection(DB_PATH)
    events = conn.execute(
        "SELECT * FROM events ORDER BY id DESC LIMIT 100"
    ).fetchall()
    handoffs = conn.execute(
        "SELECT * FROM events WHERE status='pending' AND event_type='account_creation' ORDER BY id DESC"
    ).fetchall()
    conn.close()
    events_parsed = []
    for e in events:
        d = dict(e)
        if d.get("detail"):
            try:
                d["detail"] = json.loads(d["detail"])
            except (json.JSONDecodeError, TypeError):
                pass
        events_parsed.append(d)
    handoffs_parsed = []
    for h in handoffs:
        d = dict(h)
        if d.get("detail"):
            try:
                d["detail"] = json.loads(d["detail"])
            except (json.JSONDecodeError, TypeError):
                pass
        handoffs_parsed.append(d)
    return templates.TemplateResponse("live_feed.html", {
        "request": request,
        "events": events_parsed,
        "handoffs": handoffs_parsed,
    })


@app.get("/screenshots/{filename}")
async def get_screenshot(filename: str):
    path = SCREENSHOT_DIR / filename
    if path.exists():
        return FileResponse(str(path), media_type="image/png")
    return HTMLResponse("Screenshot not found", status_code=404)


@app.get("/financial", response_class=HTMLResponse)
async def financial_view(request: Request):
    conn = get_connection(DB_PATH)
    transactions = conn.execute(
        "SELECT * FROM transactions ORDER BY id DESC LIMIT 50"
    ).fetchall()
    quota = conn.execute("SELECT * FROM llm_quota_ledger").fetchall()
    conn.close()
    return templates.TemplateResponse("financial.html", {
        "request": request,
        "transactions": [dict(t) for t in transactions],
        "quota": [dict(q) for q in quota],
    })


@app.get("/decisions", response_class=HTMLResponse)
async def decisions_view(request: Request):
    conn = get_connection(DB_PATH)
    directives = conn.execute(
        "SELECT * FROM directives ORDER BY id DESC LIMIT 50"
    ).fetchall()
    handoffs = conn.execute(
        "SELECT * FROM events WHERE status='pending' AND event_type='account_creation' ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return templates.TemplateResponse("decisions.html", {
        "request": request,
        "directives": [dict(d) for d in directives],
        "handoffs": [dict(h) for h in handoffs],
    })


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("DASHBOARD_PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
