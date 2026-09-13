#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# [ai] Goal     : list-surfaces fail-closes when python3 is not on PATH.
# Purpose  : Product prover for complete-e2e universal missing-env fault.
# Consumers: complete-e2e occupancy; exec _exec_product_universal_fault; humans.
# Inputs   : cwd = repo root. Forces PATH to a directory without python3.
# Outputs  : PASS/FAIL on stdout.
# Exit codes: 0 product fail-closed / 1 product passed when it must not / 2 usage
# Side effects: none.
# -----------------------------------------------------------------------------
set -uo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
	sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
	exit 0
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT" || exit 2
fail() { echo "FAIL: $*" >&2; exit 1; }

TARGET=""
for cand in \
	"$ROOT/scripts/complete-e2e/list-surfaces.py" \
	"$ROOT/scripts/complete-e2e/list-guest-surfaces.py"; do
	if [[ -f "$cand" ]]; then TARGET="$cand"; break; fi
done
[[ -n "$TARGET" ]] || fail "list-surfaces.py missing"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

set +e
PATH="$tmp/no-bin" python3 "$TARGET" >/dev/null 2>"$tmp/err"
rc=$?
set -e
[[ "$rc" -ne 0 ]] || fail "list-surfaces ran with python3 missing from PATH (rc=$rc)"
echo "PASS missing-env python3-not-on-PATH fail-closed rc=$rc"
exit 0
