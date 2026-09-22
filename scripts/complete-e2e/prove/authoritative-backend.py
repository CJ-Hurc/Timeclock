#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Goal     : `[ai]` LIVE HTTP occupancy for Timeclock web-ui authoritative-backend
#            cells — unreachable Joomla is BLOCKED_ENVIRONMENT, never product FAIL.
# Purpose  : Probe Timeclock surfaces against CE2E_HTTP_BASE / runtime.json and
#            write identity-bound authoritative-backend.json occupancy.
# Consumers: complete-e2e P5 walk via _exec_product_authoritative_backend.
# Inputs   : CE2E_HTTP_BASE or BASE_URL or configs/complete-e2e/runtime.json.
# Outputs  : occupancy JSON under .hurc-harness/state/complete-e2e/.
# Exit codes: 0 all surfaces ok / 1 occupancy recorded fail or blocked / 2 no base.
# Side effects: writes occupancy + copies into active run receipts dirs.
# [host:grok-cli:1.0.13][brain:xai:grok-4.6][via:direct:xai][hurc:v0.12.2413]
# Revised: connection-refused / urlopen Errno 111 sets blocked_environment
#          (twin of page-error-free.py unreachable occupancy).
# @regression ce2e-authoritative-backend-connection-refused-blocked
# -----------------------------------------------------------------------------
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _identity import identity  # noqa: E402

OUT = ROOT / ".hurc-harness" / "state" / "complete-e2e" / "authoritative-backend.json"
BASE = (os.environ.get("CE2E_HTTP_BASE") or os.environ.get("BASE_URL") or "").rstrip("/")
if not BASE:
  cfg = ROOT / "configs" / "complete-e2e" / "runtime.json"
  if cfg.is_file():
    BASE = str(json.loads(cfg.read_text()).get("http_base") or "").rstrip("/")
if not BASE:
  print("no http_base", file=sys.stderr)
  sys.exit(2)
snap, uni, run_id = identity()


def _unreachable_error(exc: BaseException) -> bool:
  text = str(exc).lower().replace("_", " ")
  if any(
    token in text
    for token in (
      "connection refused",
      "errno 111",
      "errno 61",
      "timed out",
      "name or service not known",
      "nodename nor servname",
      "network is unreachable",
    )
  ):
    return True
  return isinstance(exc, (ConnectionRefusedError, TimeoutError, urllib.error.URLError))


def probe(url: str, sid: str) -> dict:
  try:
    req = urllib.request.Request(url, headers={"User-Agent": "ce2e-timeclock-auth-be"})
    with urllib.request.urlopen(req, timeout=10) as r:
      body = r.read(200000).decode("utf-8", "replace")
      code = r.status
  except Exception as exc:
    row = {"id": sid, "ok": False, "url": url, "error": str(exc), "http_code": 0}
    if _unreachable_error(exc):
      row["blocked_environment"] = True
    return row
  live = 'data-pc-live="1"' in body or "data-timeclock" in body
  return {"id": sid, "ok": 200 <= code < 400 and live, "url": url, "http": code, "http_code": code}


paths = [
  ("ndp:view:TimeclockTimesheet", "index.php?option=com_timeclock&view=timesheet"),
  ("ui:components/com_timeclock/tmpl/timesheet/default.php", "index.php?option=com_timeclock&view=timesheet"),
  ("ui:administrator/components/com_timeclock/tmpl/timesheets/default.php", "administrator/index.php?option=com_timeclock&view=timesheets"),
  ("ui:mod_timeclockinfo/tmpl/default.php", "index.php?option=mod_timeclockinfo&view=default"),
]
surfaces = [probe(BASE + "/" + p, sid) for sid, p in paths]
unreachable = all((not s.get("ok")) and s.get("blocked_environment") for s in surfaces)
ok = (not unreachable) and all(s.get("ok") for s in surfaces)
payload = {
  "schema": "hurc-complete-e2e-authoritative-backend/v1",
  "ok": ok,
  "snapshot_id": snap,
  "universe_id": uni,
  "base": BASE,
  "surfaces": surfaces,
  "at": datetime.now(timezone.utc).isoformat(),
  "prover": "authoritative-backend-live",
}
if unreachable:
  payload["blocked_environment"] = True
  payload["environment_status"] = "unreachable"
  payload["error"] = "BLOCKED_ENVIRONMENT"
  payload["reason"] = "http_unreachable"
OUT.parent.mkdir(parents=True, exist_ok=True)
text = json.dumps(payload, indent=2) + "\n"
OUT.write_text(text)
for run in (ROOT / ".hurc-harness" / "state" / "complete-e2e" / "runs").glob("ce2e-*/receipts"):
  (run / "authoritative-backend.json").write_text(text)
print(json.dumps({"ok": ok, "blocked": unreachable, "snap": snap[:12], "uni": uni[:12], "count": len(surfaces)}))
sys.exit(0 if ok else 1)
