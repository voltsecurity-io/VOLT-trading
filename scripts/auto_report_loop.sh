#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

mkdir -p "$REPO_ROOT/logs"

LOGFILE="$REPO_ROOT/logs/auto_report_loop.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGFILE"
}

log "🔄 Starting auto-report loop (every 15 min)..."
log "   Log: $LOGFILE"
log "   Press Ctrl+C to stop"

cleanup() {
    log "🛑 Stopping auto-report loop..."
    exit 0
}

trap cleanup SIGINT SIGTERM

while true; do
    log "--- Running auto_report.sh ---"
    
    if ./scripts/auto_report.sh >> "$LOGFILE" 2>&1; then
        log "   ✅ Report generated successfully"
    else
        log "   ❌ Report generation failed (exit code: $?)"
    fi
    
    # Add jitter: random 0-60 seconds to avoid :00 collisions
    JITTER=$((RANDOM % 60))
    NEXT=$((900 + JITTER))
    log "   💤 Sleeping $NEXT seconds until next run..."
    
    sleep "$NEXT" || {
        log "   ⚠️ Sleep interrupted, exiting..."
        break
    }
done
