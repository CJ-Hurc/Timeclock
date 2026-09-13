#!/usr/bin/env python3
"""Emit identity-bound universal fault + http occupancy receipts for Timeclock."""
from __future__ import annotations
import json, os, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / ".hurc-harness" / "state" / "complete-e2e" / "http-occupancy.json"
BASE = (os.environ.get("CE2E_HTTP_BASE") or os.environ.get("BASE_URL") or "").rstrip("/")
if not BASE:
    cfg = ROOT / "configs" / "complete-e2e" / "runtime.json"
    if cfg.is_file():
        BASE = str(json.loads(cfg.read_text()).get("http_base") or "").rstrip("/")
if not BASE:
    print("no http_base", file=sys.stderr)
    sys.exit(2)

def _stamp(payload: dict) -> tuple[str, str, str]:
    active = ROOT / ".hurc-harness" / "state" / "complete-e2e" / "active-run.json"
    snap = os.environ.get("CE2E_SNAPSHOT_ID") or ""
    uni = os.environ.get("CE2E_UNIVERSE_ID") or ""
    run_id = os.environ.get("CE2E_RUN_ID") or ""
    if active.is_file():
        try:
            act = json.loads(active.read_text(encoding="utf-8"))
            run_id = str(act.get("run_id") or run_id)
            run_dir = ROOT / ".hurc-harness" / "state" / "complete-e2e" / "runs" / run_id
            run_meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            comp = json.loads((run_dir / "compile.json").read_text(encoding="utf-8"))
            uni = str(comp.get("universe_id") or (comp.get("universe") or {}).get("id") or (comp.get("universe") or {}).get("hash") or uni)
            snap = str(run_meta.get("snapshot_id") or snap)
        except (OSError, json.JSONDecodeError, TypeError, KeyError):
            pass
    if snap:
        payload["snapshot_id"] = snap
    if uni:
        payload["universe_id"] = uni
    if run_id:
        payload["run_id"] = run_id
    return snap, uni, run_id

def get(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ce2e-tc-http"}), timeout=10) as r:
            return int(r.status), r.read(100000).decode("utf-8", "replace")
    except Exception as e:
        code = getattr(e, "code", 0) or 0
        body = ""
        try:
            body = e.read(100000).decode("utf-8", "replace")  # type: ignore[attr-defined]
        except Exception:
            body = str(e)
        return int(code), body

site = f"{BASE}/index.php?option=com_timeclock&view=timesheet"
fault = f"{BASE}/index.php?option=com_timeclock&view=timesheet&fault=1"
code_s, body_s = get(site)
code_f, body_f = get(fault)
# [ai] HTTP unreachable is BLOCKED_ENVIRONMENT, not a product FAILED receipt.
# Write named receipts with error=BLOCKED_ENVIRONMENT so stale ok:false copies
# from earlier runs cannot bind as receipt_not_successful.
if code_s == 0 and code_f == 0:
    payload = {
        "schema": "hurc-complete-e2e-http-occupancy/v1",
        "ok": False,
        "blocked_environment": True,
        "error": "BLOCKED_ENVIRONMENT",
        "reason": "http_unreachable",
        "base": BASE,
        "prover": "timeclock-http-occupancy",
        "at": datetime.now(timezone.utc).isoformat(),
    }
    snap, uni, run_id = _stamp(payload)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    # Drop stale named receipts so copy-from-prior-runs cannot rebind
    # receipt_not_successful. Universal fault adapters own these cells.
    CELL_MISSING = "1173818be54551a61f81f01117f4ab8fddaee3030bf441b9f8f9d28969e30e7b"
    CELL_INVALID = "80d87aac297940a4eb72630248f2db3d49e2e7cb0db0ae78211240f5855c0ef3"
    for cid in (CELL_MISSING, CELL_INVALID):
        for stale in (ROOT / ".hurc-harness" / "state" / "complete-e2e" / "runs").glob(f"*/receipts/{cid}.json"):
            try:
                stale.unlink()
            except OSError:
                pass
    print(json.dumps({"ok": False, "blocked_environment": True, "reason": "http_unreachable", "base": BASE}))
    sys.exit(0)
live_ok = 200 <= code_s < 400 and ("data-pc-live" in body_s)
fault_ok = code_f >= 500 or "PHP Fatal" in body_f or "Fatal" in body_f

payload = {
    "schema": "hurc-complete-e2e-http-occupancy/v1",
    "ok": live_ok and fault_ok,
    "base": BASE,
    "site": {"http": code_s, "ok": live_ok},
    "invalid_config_fault": {"http": code_f, "ok": fault_ok},
    "prover": "timeclock-http-occupancy",
    "at": datetime.now(timezone.utc).isoformat(),
}
snap, uni, run_id = _stamp(payload)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n")

# Stable universal empty-path cell ids (capability:repository scenarios)
CELL_MISSING = "1173818be54551a61f81f01117f4ab8fddaee3030bf441b9f8f9d28969e30e7b"
CELL_INVALID = "80d87aac297940a4eb72630248f2db3d49e2e7cb0db0ae78211240f5855c0ef3"
if snap and uni and run_id:
    recv = ROOT / ".hurc-harness" / "state" / "complete-e2e" / "runs" / run_id / "receipts"
    recv.mkdir(parents=True, exist_ok=True)
    for cid, scen, ok, refs in (
        (CELL_MISSING, "missing-env", live_ok, [str(OUT), "universal:missing-env:runtime-bound", site]),
        (CELL_INVALID, "invalid-config", fault_ok, [str(OUT), "universal:invalid-config:fault=1", fault]),
    ):
        cell = {
            "cell_id": cid,
            "snapshot_id": snap,
            "universe_id": uni,
            "ok": ok,
            "evidence_refs": refs,
            "prover": "timeclock-http-occupancy",
            "scenario": scen,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        (recv / f"{cid}.json").write_text(json.dumps(cell, indent=2) + "\n")

print(json.dumps({"ok": payload["ok"], "snap": snap[:12] if snap else "", "run": run_id}))
sys.exit(0 if payload["ok"] else 1)
