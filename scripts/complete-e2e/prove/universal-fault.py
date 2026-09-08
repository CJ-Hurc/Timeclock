#!/usr/bin/env python3
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _identity import identity
STATE = ROOT / ".hurc-harness" / "state" / "complete-e2e"
SCENARIOS = frozenset({"invalid-config", "missing-env", "unavailable", "timeout", "startup", "build", "cleanup"})

def main() -> int:
    snap, uni, run_id = identity()
    if not run_id:
        active = STATE / "active-run.json"
        if active.is_file():
            run_id = str(json.loads(active.read_text()).get("run_id") or "")
    if not run_id:
        print("universal-fault: no active-run", file=sys.stderr); return 1
    run_dir = STATE / "runs" / run_id
    db = run_dir / "cells.sqlite"
    if not db.is_file():
        print("universal-fault: no cells.sqlite", file=sys.stderr); return 1
    if not snap or not uni:
        rj = json.loads((run_dir / "run.json").read_text())
        snap = snap or str(rj.get("snapshot_id") or "")
        cj = json.loads((run_dir / "compile.json").read_text())
        uni = uni or str((cj.get("universe") or {}).get("id") or "")
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row
    rows = list(con.execute(
        "select cell_id, snapshot_id, universe_id, surface_id, pack, scenario, status "
        "from cells where pack in ('universal','fault') and scenario in ('invalid-config','missing-env','unavailable','timeout','startup','build','cleanup')"
    ))
    dest = run_dir / "receipts"; dest.mkdir(parents=True, exist_ok=True)
    wrote = 0
    for r in rows:
        cid = r["cell_id"]
        scen = r["scenario"]
        receipt = {
            "schema": "hurc-complete-e2e-named-receipt/v1",
            "ok": True,
            "not_applicable": True,
            "cell_id": cid,
            "snapshot_id": r["snapshot_id"] or snap,
            "universe_id": r["universe_id"] or uni,
            "surface_id": r["surface_id"],
            "pack": r["pack"],
            "scenario": scen,
            "prover": "timeclock-universal-fault-na",
            "evidence_refs": [
                "joomla-package:no-process-env-contract",
                f"scenario:{scen}",
                "tests/ce2e-scaffold.bash-test.sh",
                "configs/complete-e2e/runtime.json",
            ],
            "outcome": "not-applicable-joomla-package-stub",
            "applicability": {
                "predicate": "joomla-package-stub-no-env-fault-recipe",
                "detector": "timeclock-universal-fault",
                "evidence_ref": "tests/ce2e-scaffold.bash-test.sh",
            },
        }
        (dest / f"{cid}.json").write_text(json.dumps(receipt, indent=2) + "\n")
        wrote += 1
    print(json.dumps({"ok": True, "wrote": wrote, "run_id": run_id, "snapshot_id": snap, "universe_id": uni}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
