#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="${ROOT_DIR}/agent_data.db"

export AGENT_DB_PATH="$DB_PATH"

echo "=== Autonomous Agent System ==="
echo "DB path: $DB_PATH"
echo ""

setup_venv() {
    local dir="$1"
    local name="$2"
    if [ ! -d "$dir/.venv" ]; then
        echo "Setting up $name environment..."
        python3 -m venv "$dir/.venv"
        "$dir/.venv/bin/pip" install --quiet --upgrade pip
        "$dir/.venv/bin/pip" install --quiet -e "$ROOT_DIR/core"
        if [ -f "$dir/requirements.txt" ]; then
            "$dir/.venv/bin/pip" install --quiet -r "$dir/requirements.txt"
        fi
        echo "  done"
    fi
}

setup_venv "$ROOT_DIR/core" "core"
setup_venv "$ROOT_DIR/llm_router" "llm_router"
setup_venv "$ROOT_DIR/operational_agent" "operational_agent"
setup_venv "$ROOT_DIR/dashboard" "dashboard"

echo ""
echo "=== Setup complete ==="
echo ""
echo "Available commands:"
echo "  ./start.sh agent    — Run the operational browser agent"
echo "  ./start.sh db       — Initialize database schema"
echo "  ./start.sh dash     — Start the dashboard (port 8080)"
echo "  ./start.sh setup    — Re-run setup (add new agents)"
echo ""

case "${1:-}" in
    agent)
        cd "$ROOT_DIR/operational_agent"
        exec .venv/bin/python main.py
        ;;
    db)
        cd "$ROOT_DIR/core"
        exec .venv/bin/python -c "from core.db import init_db; init_db('$DB_PATH'); print('Database initialized')"
        ;;
    dash)
        cd "$ROOT_DIR/dashboard"
        exec .venv/bin/python app.py
        ;;
    setup|"")
        # already did setup above
        ;;
    *)
        echo "Usage: $0 {agent|db|dash|setup}"
        exit 1
        ;;
esac
