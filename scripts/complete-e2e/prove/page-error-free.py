#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys, urllib.request, re
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / ".hurc-harness" / "state" / "complete-e2e" / "page-error-free.json"

def _stamp(payload: dict) -> None:
    active = ROOT / ".hurc-harness" / "state" / "complete-e2e" / "active-run.json"
    if not active.is_file():
        return
    try:
        act = json.loads(active.read_text(encoding="utf-8"))
        run_id = str(act.get("run_id") or "")
        run_dir = ROOT / ".hurc-harness" / "state" / "complete-e2e" / "runs" / run_id
        run_meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        comp = json.loads((run_dir / "compile.json").read_text(encoding="utf-8"))
        uni = comp.get("universe_id") or (comp.get("universe") or {}).get("id") or (comp.get("universe") or {}).get("hash")
        snap = run_meta.get("snapshot_id")
        if snap:
            payload["snapshot_id"] = snap
        if uni:
            payload["universe_id"] = uni
        if run_id:
            payload["run_id"] = run_id
    except (OSError, json.JSONDecodeError, TypeError):
        return
BASE = (os.environ.get("CE2E_HTTP_BASE") or os.environ.get("BASE_URL") or "").rstrip("/")
if not BASE:
    cfg = ROOT / "configs" / "complete-e2e" / "runtime.json"
    if cfg.is_file():
        BASE = str(json.loads(cfg.read_text()).get("http_base") or "").rstrip("/")
if not BASE:
    print("no http_base", file=sys.stderr); sys.exit(2)

def route_for(rel: str) -> str:
    rel = rel.replace("\\", "/")
    m = re.search(r"(?:^|/)administrator/components/(com_[^/]+)/tmpl/([^/]+)/([^/]+)\.php$", rel)
    if m:
        option, view, layout = m.group(1), m.group(2), m.group(3)
        q = f"administrator/index.php?option={option}&view={view}"
        if layout not in {"default", "row"} and not layout.startswith("_"):
            q += f"&layout={layout}"
        return q
    m = re.search(r"(?:^|/)components/(com_[^/]+)/tmpl/([^/]+)/(?:.+/)?([^/]+)\.php$", rel)
    if m:
        option, view, layout = m.group(1), m.group(2), m.group(3)
        q = f"index.php?option={option}&view={view}"
        if layout not in {"default", "row", "header", "toolbar", "totals", "category", "entry", "name", "subtotals", "psubtotals", "dataset"} and not layout.startswith("_"):
            q += f"&layout={layout}"
        return q
    m = re.search(r"(?:^|/)mod_([^/]+)/tmpl/([^/]+)\.php$", rel)
    if m:
        return f"index.php?option=mod_{m.group(1)}&view={m.group(2)}"
    return "index.php?option=com_timeclock&view=timesheet"

def probe(url: str, sid: str) -> dict:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ce2e-timeclock-pef"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read(200000).decode("utf-8", "replace"); code = resp.status
    except Exception as e:
        return {"id": sid, "ok": False, "url": url, "error": str(e)}
    fatal = any(x in body for x in ("PHP Fatal", "Uncaught", "Whoops", "Traceback"))
    live = 'data-pc-live="1"' in body or "data-timeclock" in body
    return {"id": sid, "ok": (200 <= code < 400) and live and not fatal, "url": url, "http": code, "live": live}

surfaces = []
tmpl_files = [p for p in ROOT.rglob("*.php") if "/tmpl/" in str(p).replace("\\","/") and ".hurc-harness" not in str(p) and "/build/" not in str(p)]
for p in sorted(tmpl_files, key=lambda x: str(x)):
    rel = str(p.relative_to(ROOT)).replace("\\", "/")
    surfaces.append(probe(BASE + "/" + route_for(rel), f"ui:{rel}"))
for sid, path in [
    ("ndp:view:TimeclockTimesheet", "index.php?option=com_timeclock&view=timesheet"),
    ("joomla:option:com_timeclock", "index.php?option=com_timeclock&view=timesheet"),
]:
    surfaces.append(probe(BASE + "/" + path, sid))
# also probe home
surfaces.append(probe(BASE + "/", "ndp:view:TimeclockTimesheet"))

payload = {
  "schema": "hurc-complete-e2e-page-error-free/v1",
  "ok": all(s.get("ok") for s in surfaces),
  "snapshot_id": os.environ.get("CE2E_SNAPSHOT_ID") or "",
  "universe_id": os.environ.get("CE2E_UNIVERSE_ID") or "",
  "base": BASE,
  "at": datetime.now(timezone.utc).isoformat(),
  "surfaces": surfaces,
  "prover": "page-error-free",
}
_stamp(payload)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n")
for run in (ROOT/".hurc-harness/state/complete-e2e/runs").glob("ce2e-*/receipts"):
    (run/"page-error-free.json").write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps({"ok": payload["ok"], "count": len(surfaces), "failed": [s["id"] for s in surfaces if not s.get("ok")][:10]}))
sys.exit(0 if payload["ok"] else 1)
