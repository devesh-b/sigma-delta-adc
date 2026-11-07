#!/usr/bin/env bash
# sync-to-sandbox.sh — push the tt tree to the sandbox; pull results back.
#
# Everything runs on the sandbox (user rule); the Mac only edits and dispatches.
# Drive runs with `rta-tt` (rt pinned to the `tt` tmux session).
#
#   scripts/sync-to-sandbox.sh          push sources (rsync --delete)
#   scripts/sync-to-sandbox.sh --pull   bring ~/regr/tt results back into sandbox-out/
#
# Results are pulled into a separate dir, never over local sources.
set -euo pipefail

HOST=${RT_HOST:-sandbox}
LOCAL_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REMOTE_ROOT=/home/mempool/tt-sd   # own dir; /home/mempool/tt belongs to AlphaOneSoC (TT tools)
# Runs write here, OUTSIDE the synced tree, so --delete never wipes results.
REGR=/home/mempool/regr/tt

if [ "${1:-}" = "--pull" ]; then
  mkdir -p "$LOCAL_ROOT/sandbox-out"
  rsync -a --stats \
    --exclude '*.raw' \
    "$HOST:$REGR/" "$LOCAL_ROOT/sandbox-out/"
  echo "pulled -> $LOCAL_ROOT/sandbox-out/"
  exit 0
fi

# Safety: rsync --delete must only ever target OUR tree. Refuse if the remote
# dir exists, is non-empty, and lacks the marker (2026-11-07: a push into
# AlphaOneSoC's /home/mempool/tt deleted its files).
ssh "$HOST" "if [ -d $REMOTE_ROOT ] && [ -n \"\$(ls -A $REMOTE_ROOT)\" ] && [ ! -f $REMOTE_ROOT/.tt-sd-root ]; then
               echo 'sync: $REMOTE_ROOT exists, is non-empty and has no .tt-sd-root marker; refusing --delete' >&2; exit 3; fi
             mkdir -p $REMOTE_ROOT $REGR && touch $REMOTE_ROOT/.tt-sd-root"
rsync -a --delete --stats \
  --exclude '.venv/' \
  --exclude '.venv-sbx/' \
  --exclude '.tt-sd-root' \
  --exclude 'sandbox-out/' \
  --exclude '.claude/' \
  --exclude 'memory/' \
  --exclude 'process/export-*/home/' \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  --exclude 'model/out/' \
  "$LOCAL_ROOT/" "$HOST:$REMOTE_ROOT/"

echo "synced $LOCAL_ROOT -> $HOST:$REMOTE_ROOT ($(date '+%F %T'))"
