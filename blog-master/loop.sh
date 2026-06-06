#!/usr/bin/env bash
# Daily scheduler. Sleeps until DAILY_UTC_HOUR each day, then runs one review.
# Deliberately not cron — avoids cron's env-stripping footgun in containers.
set -euo pipefail

HOUR="${DAILY_UTC_HOUR:-13}"

if [ "${RUN_ON_START:-false}" = "true" ]; then
  /opt/blog-master/entrypoint.sh || echo "[blog-master] initial run failed; continuing schedule"
fi

while true; do
  now=$(date -u +%s)
  next=$(date -u -d "today ${HOUR}:00:00" +%s)
  [ "$next" -le "$now" ] && next=$(date -u -d "tomorrow ${HOUR}:00:00" +%s)
  wait_s=$(( next - now ))
  echo "[blog-master] sleeping ${wait_s}s until $(date -u -d "@${next}" +%FT%TZ)"
  sleep "$wait_s"
  /opt/blog-master/entrypoint.sh || echo "[blog-master] run failed; will retry next cycle"
done
