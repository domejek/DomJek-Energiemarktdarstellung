#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

PIDS=()
cleanup() {
    info "Fahre Dienste herunter..."
    for pid in "${PIDS[@]:+${PIDS[@]}}"; do kill "$pid" 2>/dev/null || true; done
    wait 2>/dev/null
    ok "Alle Dienste beendet."
}
trap cleanup EXIT INT TERM

# ──── Prerequisites ────
check_prereqs() {
    info "Prüfe Voraussetzungen..."
    command -v python3  >/dev/null || { err "python3 nicht gefunden"; exit 1; }
    command -v node     >/dev/null || { err "node nicht gefunden"; exit 1; }
    command -v npm      >/dev/null || { err "npm nicht gefunden"; exit 1; }
    ok "python3 $(python3 --version | cut -d' ' -f2), node $(node --version), npm $(npm --version)"
}

# ──── Backend-Setup ────
setup_backend() {
    info "Richte Backend ein..."

    if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
        python3 -m venv "$BACKEND_DIR/.venv"
        ok "Virtualenv erstellt"
    fi

    source "$BACKEND_DIR/.venv/bin/activate"
    pip install --quiet -r "$BACKEND_DIR/requirements.txt"
    pip install --quiet -r "$ROOT_DIR/requirements.txt" 2>/dev/null || true
    pip install --quiet pytest httpx 2>/dev/null || true
    deactivate
    ok "Backend-Dependencies installiert"
}

# ──── Frontend-Setup ────
setup_frontend() {
    info "Richte Frontend ein..."
    cd "$FRONTEND_DIR"
    if [[ ! -d "node_modules" ]]; then
        npm install --legacy-peer-deps 2>&1 | tail -1
        ok "Frontend-Dependencies installiert"
    else
        ok "Frontend-Dependencies bereits installiert"
    fi
}

# ──── Tests ausführen ────
run_tests() {
    local exit_code=0

    # Backend-Tests
    source "$BACKEND_DIR/.venv/bin/activate"
    export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"
    echo -e "\n${CYAN}▶ Backend-Tests${NC}"
    cd "$ROOT_DIR"
    python -m pytest tests/ backend/tests/ -v --tb=short --cov=backend 2>&1 || exit_code=1

    # Frontend-Tests
    echo -e "\n${CYAN}▶ Frontend-Tests${NC}"
    cd "$FRONTEND_DIR"
    npx ng test --watch=false --browsers=ChromeHeadless 2>&1 || exit_code=1

    if [[ $exit_code -eq 0 ]]; then
        ok "Alle Tests bestanden!"
    else
        err "Tests fehlgeschlagen"
    fi
    return $exit_code
}

# ──── Backend starten ────
start_backend() {
    info "Starte FastAPI Backend (Port 8000)..."
    source "$BACKEND_DIR/.venv/bin/activate"
    export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"
    cd "$ROOT_DIR"
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
    PIDS+=("$!")

    for i in $(seq 1 15); do
        if curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
            ok "Backend läuft unter http://localhost:8000"
            break
        fi
        if [[ $i -eq 15 ]]; then
            err "Backend konnte nicht gestartet werden"
            exit 1
        fi
        sleep 1
    done
}

# ──── Frontend starten ────
start_frontend() {
    info "Starte Angular Dev Server (Port 4200)..."
    cd "$FRONTEND_DIR"
    export NG_CLI_ANALYTICS=false
    npx ng serve --host 0.0.0.0 --port 4200 --proxy-config proxy.conf.json &
    PIDS+=("$!")

    for i in $(seq 1 30); do
        if curl -sf http://localhost:4200 >/dev/null 2>&1; then
            ok "Frontend läuft unter http://localhost:4200"
            return 0
        fi
        if [[ $i -eq 30 ]]; then
            warn "Frontend konnte nicht erreicht werden — prüfe Logs mit: npx ng serve"
        fi
        sleep 2
    done
}

# ──── Browser öffnen ────
open_browser() {
    case "$(uname -s)" in
        Darwin)  open "http://localhost:4200" 2>/dev/null || true ;;
        Linux)   xdg-open "http://localhost:4200" 2>/dev/null || true ;;
    esac
}

# ──── Main ────
main() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║   DomJek Energiemarktdarstellung v3.0   ║${NC}"
    echo -e "${CYAN}║   Angular + FastAPI Local Dev Runner     ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
    echo ""

    case "${1:-}" in
        test|--test)
            check_prereqs
            setup_backend
            setup_frontend
            run_tests
            ;;
        backend)
            check_prereqs
            setup_backend
            start_backend
            wait
            ;;
        frontend)
            check_prereqs
            setup_frontend
            start_frontend
            wait
            ;;
        *)
            check_prereqs
            setup_backend
            setup_frontend
            start_backend
            start_frontend
            open_browser
            echo ""
            ok "Alle Dienste laufen!"
            echo -e "   Frontend: ${GREEN}http://localhost:4200${NC}"
            echo -e "   Backend:  ${GREEN}http://localhost:8000${NC}"
            echo -e "   API Docs: ${GREEN}http://localhost:8000/docs${NC}"
            echo ""
            echo -e "${YELLOW}Drücke Ctrl+C um alle Dienste zu beenden.${NC}"
            echo ""
            wait
            ;;
    esac
}

main "$@"
