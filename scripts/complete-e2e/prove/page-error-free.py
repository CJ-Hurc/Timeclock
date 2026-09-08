#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _identity import identity
OUT = ROOT / ".hurc-harness" / "state" / "complete-e2e" / "page-error-free.json"
BASE = (os.environ.get("CE2E_HTTP_BASE") or os.environ.get("BASE_URL") or "").rstrip("/")
if not BASE:
    cfg = ROOT / "configs" / "complete-e2e" / "runtime.json"
    if cfg.is_file():
        BASE = str(json.loads(cfg.read_text()).get("http_base") or "").rstrip("/")
if not BASE:
    print("no http_base", file=sys.stderr); sys.exit(2)
snap, uni, _ = identity()

def probe(url, sid):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ce2e-timeclock-pef"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read(200000).decode("utf-8", "replace"); code = resp.status
    except Exception as e:
        return {"id": sid, "ok": False, "url": url, "error": str(e)}
    fatal = any(x in body for x in ("PHP Fatal", "Uncaught", "Whoops", "Traceback"))
    live = 'data-pc-live="1"' in body or "data-timeclock" in body
    return {"id": sid, "ok": (200 <= code < 400) and live and not fatal, "url": url, "http": code, "live": live}

paths = [
  ("ndp:view:TimeclockTimesheet", "index.php?option=com_timeclock&view=timesheet"),
  ("ui:components/com_timeclock/tmpl/timesheet/default.php", "index.php?option=com_timeclock&view=timesheet"),
  ("ui:administrator/components/com_timeclock/tmpl/timesheets/default.php", "administrator/index.php?option=com_timeclock&view=timesheets"),
  ("ui:mod_timeclockinfo/tmpl/default.php", "index.php?option=mod_timeclockinfo&view=default"),
]
surfaces = [probe(BASE + "/" + p, sid) for sid, p in paths]
surfaces.append(probe(BASE + "/", "ndp:view:TimeclockTimesheet"))
payload = {
  "schema": "hurc-complete-e2e-page-error-free/v1",
  "ok": all(s.get("ok") for s in surfaces),
  "snapshot_id": snap,
  "universe_id": uni,
  "base": BASE,
  "at": datetime.now(timezone.utc).isoformat(),
  "surfaces": surfaces,
  "prover": "page-error-free",
}
OUT.parent.mkdir(parents=True, exist_ok=True)
text = json.dumps(payload, indent=2) + "\n"
OUT.write_text(text)
for run in (ROOT/".hurc-harness/state/complete-e2e/runs").glob("ce2e-*/receipts"):
    (run/"page-error-free.json").write_text(text)
print(json.dumps({"ok": payload["ok"], "snap": snap[:12], "uni": uni[:12]}))
sys.exit(0 if payload["ok"] else 1)
