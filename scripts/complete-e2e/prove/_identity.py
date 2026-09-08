from __future__ import annotations
import json, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / ".hurc-harness" / "state" / "complete-e2e"

def identity() -> tuple[str, str, str]:
    snap = os.environ.get("CE2E_SNAPSHOT_ID") or ""
    uni = os.environ.get("CE2E_UNIVERSE_ID") or ""
    run_id = os.environ.get("CE2E_RUN_ID") or ""
    active = STATE / "active-run.json"
    if active.is_file():
        data = json.loads(active.read_text())
        run_id = run_id or str(data.get("run_id") or "")
        snap = snap or str(data.get("snapshot_id") or "")
    if run_id:
        run_json = STATE / "runs" / run_id / "run.json"
        if run_json.is_file():
            rj = json.loads(run_json.read_text())
            snap = snap or str(rj.get("snapshot_id") or "")
        compile_json = STATE / "runs" / run_id / "compile.json"
        if compile_json.is_file():
            cj = json.loads(compile_json.read_text())
            uni = uni or str((cj.get("universe") or {}).get("id") or (cj.get("universe") or {}).get("hash") or "")
    # fallback: any run
    if not snap or not uni:
        runs = sorted((STATE / "runs").glob("ce2e-*/run.json"), reverse=True)
        for rj_path in runs:
            rj = json.loads(rj_path.read_text())
            snap = snap or str(rj.get("snapshot_id") or "")
            cj_path = rj_path.parent / "compile.json"
            if cj_path.is_file():
                cj = json.loads(cj_path.read_text())
                uni = uni or str((cj.get("universe") or {}).get("id") or "")
            run_id = run_id or rj_path.parent.name
            if snap and uni:
                break
    return snap, uni, run_id
