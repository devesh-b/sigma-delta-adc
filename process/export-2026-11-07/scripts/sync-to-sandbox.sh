#!/usr/bin/env bash
# sync-to-sandbox.sh — push the working tree to the sandbox and rewrite the
# river_core config for the remote paths.
#
# Regressions run on the sandbox (6 cores, ~800G free); short runs stay local.
# Execution there is driven with `rta` (rt bound to the `alpha` tmux session).
#
#   ./scripts/sync-to-sandbox.sh          push code + regenerate config
#   ./scripts/sync-to-sandbox.sh --pull   bring build/mywork results back
#
# <confidential-dir>/ is deliberately never sent: the verification flow does not read it.
set -euo pipefail

HOST=${RT_HOST:-sandbox}
LOCAL_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REMOTE_ROOT=/home/mempool/AlphaOneSoC

if [ "${1:-}" = "--pull" ]; then
  # Results only — never pull the remote tree over local sources.
  mkdir -p "$LOCAL_ROOT/build"
  rsync -a --info=stats2 \
    --exclude 'riscv-dv/' \
    "$HOST:$REMOTE_ROOT/build/mywork/" "$LOCAL_ROOT/build/mywork-sandbox/"
  echo "pulled -> $LOCAL_ROOT/build/mywork-sandbox/"
  exit 0
fi

rsync -a --delete --info=stats2 \
  --exclude '<confidential-dir>/' \
  --exclude 'build/' \
  --exclude 'localFiles/' \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  --exclude '*.pyc' \
  --exclude 'plugins/river_core.log' \
  --exclude 'plugins/failure.log' \
  --exclude 'river_core.log' \
  "$LOCAL_ROOT/" "$HOST:$REMOTE_ROOT/"

# The config carries absolute paths, so it cannot be shared verbatim between
# the two machines. Rewrite the prefix in place on the remote copy.
ssh "$HOST" "sed -i 's|$LOCAL_ROOT|$REMOTE_ROOT|g' $REMOTE_ROOT/plugins/river-config.ini && \
             grep -c '$REMOTE_ROOT' $REMOTE_ROOT/plugins/river-config.ini" \
  | xargs -I{} echo "rewrote {} paths in river-config.ini"

echo "synced $LOCAL_ROOT -> $HOST:$REMOTE_ROOT"
