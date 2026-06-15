#!/usr/bin/env python3
"""
Autonomous Agent System — Main Runner

Usage:
  ./runner.py init          # Initialize DB + seed quota
  ./runner.py agent         # Run operational agent cycle
  ./runner.py cfo           # Run CFO daily check
  ./runner.py ceo           # Run CEO weekly cycle
  ./runner.py dash          # Start dashboard (port 8080)
  ./runner.py all           # Run full cycle: agent + cfo + ceo
"""

import os
import sys
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "agent_data.db"
ROOT_VENV = HERE / ".venv"


def _use_root_venv():
    python = ROOT_VENV / "bin" / "python"
    if python.exists() and sys.executable != str(python):
        os.execv(str(python), [str(python), __file__] + sys.argv[1:])


_use_root_venv()

os.environ["AGENT_DB_PATH"] = str(DB_PATH)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_KEY:
    print("WARNING: GEMINI_API_KEY not set.")


def cmd_init():
    from core.db import init_db
    from llm_router.providers import seed_quota_ledger
    init_db()
    seed_quota_ledger()
    print(f"+ Database initialized at {DB_PATH}")
    print("+ Quota ledger seeded with free providers.")


def cmd_agent():
    subprocess.run([
        HERE / "operational_agent" / ".venv" / "bin" / "python",
        HERE / "operational_agent" / "operational_agent" / "main.py",
    ], cwd=HERE, env={**os.environ})


def cmd_cfo():
    python = HERE / "cfo_agent" / ".venv" / "bin" / "python"
    if not python.exists():
        subprocess.run([ROOT_VENV / "bin" / "python", "-m", "venv", str(python.parent.parent)])
        subprocess.run([python, "-m", "pip", "install", "--quiet", "-e", "core/", "-e", "cfo_agent/"], cwd=HERE)
    subprocess.run([str(python), HERE / "cfo_agent" / "cfo_agent" / "main.py"], cwd=HERE, env={**os.environ})


def cmd_ceo():
    python = HERE / "ceo_agent" / ".venv" / "bin" / "python"
    if not python.exists():
        subprocess.run([ROOT_VENV / "bin" / "python", "-m", "venv", str(python.parent.parent)])
        subprocess.run([python, "-m", "pip", "install", "--quiet", "-e", "core/", "-e", "llm_router/", "-e", "ceo_agent/"], cwd=HERE)
    subprocess.run([str(python), HERE / "ceo_agent" / "ceo_agent" / "main.py"], cwd=HERE, env={**os.environ})


def cmd_dash():
    subprocess.run([
        HERE / "dashboard" / ".venv" / "bin" / "python",
        HERE / "dashboard" / "dashboard" / "app.py",
    ], cwd=HERE, env={**os.environ})


def cmd_all():
    cmd_init()
    cmd_agent()
    cmd_cfo()
    cmd_ceo()
    print("+ Full cycle complete. Run './runner.py dash' to view results.")


if __name__ == "__main__":
    commands = {
        "init": cmd_init,
        "agent": cmd_agent,
        "cfo": cmd_cfo,
        "ceo": cmd_ceo,
        "dash": cmd_dash,
        "all": cmd_all,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print(__doc__[1:])
        sys.exit(1)
    commands[sys.argv[1]]()
