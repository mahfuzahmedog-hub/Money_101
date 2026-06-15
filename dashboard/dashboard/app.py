import os
import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from core.db import get_connection, DB_PATH

app = FastAPI(title="Agent Dashboard")
SCREENSHOT_DIR = Path(os.path.dirname(DB_PATH or "agent_data.db")) / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

PAGE_HEAD = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agent Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,system-ui,monospace;background:#0d1117;color:#c9d1d9;padding:20px}
nav{margin-bottom:20px;padding-bottom:10px;border-bottom:1px solid #30363d}
nav a{color:#58a6ff;text-decoration:none;margin-right:20px;font-weight:600}
nav a:hover{text-decoration:underline}
h1,h2{margin-bottom:12px;margin-top:20px}
.card{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:12px;margin-bottom:8px}
.card .time{color:#8b949e;font-size:.85em}
.card .agent{color:#d2a8ff}
.card .type{color:#7ee787;font-weight:600}
.card.fail .type{color:#f85149}
.card.pending .type{color:#d29922}
.handoff{background:#3d1f0022;border:2px solid #d29922;border-radius:8px;padding:16px;margin-bottom:16px}
.handoff h2{color:#d29922;margin:0 0 8px 0}
table{width:100%;border-collapse:collapse;margin-bottom:20px}
th,td{text-align:left;padding:8px;border-bottom:1px solid #30363d}
th{color:#8b949e}
.income{color:#3fb950}
.expense{color:#f85149}
.screenshot{max-width:100%;border:1px solid #30363d;border-radius:4px;margin-top:8px;display:none}
.screenshot-link{color:#58a6ff;font-size:.85em;cursor:pointer}
</style></head><body>
<nav><a href="/live">Live Feed</a> <a href="/financial">Financial</a> <a href="/decisions">Decisions</a></nav>
"""

PAGE_TAIL = """</body></html>"""


def get_events():
    conn = get_connection(DB_PATH)
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("detail"):
            try:
                d["detail"] = json.loads(d["detail"])
            except (json.JSONDecodeError, TypeError):
                d["detail"] = {}
        result.append(d)
    return result


def get_handoffs():
    conn = get_connection(DB_PATH)
    rows = conn.execute(
        "SELECT * FROM events WHERE status='pending' AND event_type='account_creation' ORDER BY id DESC"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("detail"):
            try:
                d["detail"] = json.loads(d["detail"])
            except (json.JSONDecodeError, TypeError):
                d["detail"] = {}
        result.append(d)
    return result


@app.get("/")
async def home():
    return RedirectResponse(url="/live")


@app.get("/live", response_class=HTMLResponse)
async def live_feed():
    events = get_events()
    handoffs = get_handoffs()
    html = PAGE_HEAD + "<h1>Live Feed</h1>"
    for h in handoffs:
        html += f'<div class="handoff"><h2>⚠️ HUMAN HELP NEEDED</h2><p>{h["summary"]}</p>'
        detail = h.get("detail", {})
        if detail:
            instr = detail.get("instructions") or detail.get("email") or str(detail)
            html += f"<p>{instr}</p>"
        html += "</div>"
    for e in events:
        cls = "fail" if e["status"] == "failure" else ("pending" if e["status"] == "pending" else "")
        html += f'<div class="card {cls}"><span class="time">{e["timestamp"]}</span> <span class="agent">{e["agent_id"]}</span> <span class="type">{e["event_type"]}</span> [{e["status"]}]<br><span>{e["summary"]}</span>'
        detail = e.get("detail", {})
        if isinstance(detail, dict) and detail.get("screenshot"):
            fn = Path(detail["screenshot"]).name
            html += f'<br><span class="screenshot-link" onclick="document.getElementById(\'ss_{e["id"]}\').style.display=\'block\'">📷 View Screenshot</span>'
            html += f'<img id="ss_{e["id"]}" class="screenshot" src="/screenshots/{fn}" />'
        html += "</div>"
    if not events:
        html += "<p>No events yet. Run the agent.</p>"
    return HTMLResponse(html + PAGE_TAIL)


@app.get("/screenshots/{filename}")
async def get_screenshot(filename: str):
    path = SCREENSHOT_DIR / filename
    if path.exists():
        return FileResponse(str(path), media_type="image/png")
    return HTMLResponse("Not found", status_code=404)


@app.get("/financial", response_class=HTMLResponse)
async def financial_view():
    conn = get_connection(DB_PATH)
    transactions = conn.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 50").fetchall()
    quota = conn.execute("SELECT * FROM llm_quota_ledger").fetchall()
    conn.close()
    html = PAGE_HEAD + "<h1>Financial</h1><h2>LLM Quota</h2><table><tr><th>Provider</th><th>Model</th><th>Limit</th><th>Used</th><th>Tier</th></tr>"
    for q in quota:
        html += f"<tr><td>{q['provider']}</td><td>{q['model']}</td><td>{q['limit_value']}</td><td>{q['used_today']}</td><td>{q['tier']}</td></tr>"
    html += "</table><h2>Transactions</h2><table><tr><th>Date</th><th>Type</th><th>Amount</th><th>Source</th></tr>"
    for t in transactions:
        cls = "income" if t["type"] == "income" else "expense"
        html += f"<tr><td>{t['date']}</td><td class='{cls}'>{t['type']}</td><td>${t['amount']:.2f}</td><td>{t['source']}</td></tr>"
    html += "</table>"
    if not transactions:
        html += "<p>No transactions yet.</p>"
    return HTMLResponse(html + PAGE_TAIL)


@app.get("/decisions", response_class=HTMLResponse)
async def decisions_view():
    conn = get_connection(DB_PATH)
    directives = conn.execute("SELECT * FROM directives ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    handoffs = get_handoffs()
    html = PAGE_HEAD + "<h1>Decisions</h1>"
    for h in handoffs:
        html += f'<div class="handoff"><h2>⚠️ {h["summary"]}</h2><p>{h["detail"]}</p></div>'
    html += "<h2>Directives</h2>"
    for d in directives:
        html += f'<div class="card"><b>{d["from_agent"]}</b> {d["action"]} [{d["status"]}]<br>{d["reason"]}</div>'
    if not directives:
        html += "<p>No directives yet.</p>"
    return HTMLResponse(html + PAGE_TAIL)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("DASHBOARD_PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
