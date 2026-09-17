#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# [ai] Goal     : list-surfaces rejects the reserved --hurc-ce2e-* unknown option.
# Purpose  : Product prover for complete-e2e universal invalid-config fault.
# Consumers: complete-e2e occupancy; exec _exec_product_universal_fault; humans.
# Inputs   : cwd = repo root.
# Outputs  : PASS/FAIL on stdout.
# Exit codes: 0 product fail-closed / 1 product accepted invalid option / 2 usage
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

command -v python3 >/dev/null 2>&1 || fail "python3 missing"
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
python3 "$TARGET" --hurc-ce2e-no-such-flag \
	>"$tmp/out" 2>"$tmp/err"
rc=$?
set -e
text="$(cat "$tmp/out" "$tmp/err" 2>/dev/null || true)"
[[ "$rc" -ne 0 ]] || fail "list-surfaces accepted --hurc-ce2e-no-such-flag (rc=$rc)"
printf '%s' "$text" | grep -qiE 'unrecognized arguments|unknown option|usage:' \
	|| fail "unknown-option diagnostic missing from fail-closed output"
echo "PASS invalid-config reserved --hurc-ce2e-* fail-closed rc=$rc"
exit 0
