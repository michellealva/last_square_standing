#!/usr/bin/env bash
#
# One-shot deploy / update for Last Square Standing on a Frappe bench.
#
# Run it ON the bench server, from anywhere:
#     apps/last_square_standing/scripts/deploy.sh <site-name>
#
# It pulls the latest code, rebuilds the Vue frontend, migrates the site,
# rebuilds assets, and clears the website cache. Requires Node >= 24.
set -euo pipefail

SITE="${1:?Usage: scripts/deploy.sh <site-name>}"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH_ROOT="$(cd "$APP_DIR/../.." && pwd)"
APP_NAME="last_square_standing"

echo "▶ Bench:  $BENCH_ROOT"
echo "▶ App:    $APP_DIR"
echo "▶ Site:   $SITE"

echo "▶ Pulling latest code…"
git -C "$APP_DIR" pull --ff-only

echo "▶ Building frontend (needs Node >= 24)…"
( cd "$APP_DIR/frontend" && yarn install --frozen-lockfile && yarn build )

cd "$BENCH_ROOT"

echo "▶ Migrating $SITE…"
bench --site "$SITE" migrate

echo "▶ Rebuilding assets…"
bench build --app "$APP_NAME"

echo "▶ Clearing website cache…"
bench --site "$SITE" clear-website-cache

echo "✓ Deployed $APP_NAME to $SITE."
echo "  If running under a process manager, restart it (e.g. 'bench restart' or 'sudo supervisorctl restart all')."
