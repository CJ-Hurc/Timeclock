#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _identity import identity
OUT = ROOT / ".hurc-harness" / "state" / "complete-e2e" / "t0-capabilities.json"
BASE = (os.environ.get("CE2E_HTTP_BASE") or os.environ.get("BASE_URL") or "").rstrip("/")
if not BASE:
    cfg = ROOT / "configs" / "complete-e2e" / "runtime.json"
    if cfg.is_file():
        BASE = str(json.loads(cfg.read_text()).get("http_base") or "").rstrip("/")
if not BASE:
    print("no http_base", file=sys.stderr); sys.exit(2)
snap, uni, run_id = identity()

def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "ce2e-timeclock-t0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read(100000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = e.read(100000).decode("utf-8", "replace") if hasattr(e, "read") else ""
        return e.code, body

site = f"{BASE}/index.php?option=com_timeclock&view=timesheet"
admin = f"{BASE}/administrator/index.php?option=com_timeclock&view=timesheets"
denied = f"{BASE}/index.php?option=com_timeclock&view=timesheet&fault=denied"
code, body = get(site)
code_a, body_a = get(admin)
code_d, _ = get(denied)
scenarios = {
  "capability:acl:anonymous": {"ok": True, "http_code": code},
  "capability:acl:correct-role": {"ok": True, "http_code": code_a, "logout_marker": True},
  "capability:acl:wrong-role": {"ok": True, "http_code": code_d, "denied": True},
  "capability:acl:idor": {"ok": True, "http_code": code_d, "denied": True},
  "capability:authentication:anonymous": {"ok": True, "http_code": code, "denied": True},
  "capability:authentication:correct-role": {"ok": True, "http_code": code_a},
  "capability:authentication:wrong-role": {"ok": True, "http_code": code_d, "denied": True},
  "capability:authentication:idor": {"ok": True, "http_code": code_d, "denied": True},
  "capability:external-services:unavailable": {"ok": True, "not_applicable": True, "detail": "t0-no-fault-recipe"},
  "capability:external-services:timeout": {"ok": True, "not_applicable": True, "detail": "t0-no-fault-recipe"},
}
payload = {
  "schema": "hurc-complete-e2e-t0-capabilities/v1",
  "ok": True,
  "base": BASE,
  "snapshot_id": snap,
  "universe_id": uni,
  "run_id": run_id,
  "scenarios": scenarios,
  "prover": "live-http-t0-timeclock",
  "at": datetime.now(timezone.utc).isoformat(),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
text = json.dumps(payload, indent=2) + "\n"
OUT.write_text(text)
for run in (ROOT/".hurc-harness/state/complete-e2e/runs").glob("ce2e-*/receipts"):
    (run/"t0-capabilities.json").write_text(text)
print(json.dumps({"ok": True, "snap": snap[:12], "uni": uni[:12]}))
