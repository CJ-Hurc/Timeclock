#!/usr/bin/env bash
set -euo pipefail
# complete-e2e universal startup/build/cleanup scaffold proof
test -f configs/complete-e2e/runtime.json
test -f configs/complete-e2e/actors.json
curl -fsS "${CE2E_HTTP_BASE:-http://127.0.0.1:18090}/index.php?option=com_timeclock&view=timesheet" | grep -q 'data-pc-live'
exit 0
