import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from core.db import get_connection, DB_PATH

app = FastAPI(title="Agent Dashboard")

HERE = Path(__file__).parent
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
    conn.close()
    return templates.TemplateResponse("live_feed.html", {
        "request": request,
        "events": [dict(e) for e in events],
    })


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
    conn.close()
    return templates.TemplateResponse("decisions.html", {
        "request": request,
        "directives": [dict(d) for d in directives],
    })


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("DASHBOARD_PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
