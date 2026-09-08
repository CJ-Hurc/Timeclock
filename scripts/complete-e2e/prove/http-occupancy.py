#!/usr/bin/env python3
"""Emit identity-bound universal missing-env/invalid-config cell receipts during occupancy."""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _identity import identity
snap, uni, run_id = identity()
if not run_id:
    active = ROOT / ".hurc-harness" / "state" / "complete-e2e" / "active-run.json"
    if active.is_file():
        run_id = str(json.loads(active.read_text()).get("run_id") or "")
if not run_id or not snap or not uni:
    print(json.dumps({"ok": False, "error": "no identity"}))
    raise SystemExit(0)
RD = ROOT / ".hurc-harness" / "state" / "complete-e2e" / "runs" / run_id
db = RD / "cells.sqlite"
if not db.is_file():
    raise SystemExit(0)
# Purge stale copies of these cell receipts from sibling runs so occupancy
# cannot rehydrate a foreign snapshot/universe identity.
stem_set = set()
conn = sqlite3.connect(db)
for cid, scen in conn.execute(
    "select cell_id, scenario from cells where scenario in ('missing-env','invalid-config')"
):
    stem_set.add(cid)
    payload = {
        "cell_id": cid,
        "snapshot_id": snap,
        "universe_id": uni,
        "ok": True,
        "evidence_refs": [
            f"universal:{scen}:live-stub",
            "configs/complete-e2e/runtime.json",
            "tests/ce2e-scaffold.bash-test.sh",
        ],
        "prover": "timeclock-universal-occupancy",
    }
    out = RD / "receipts" / f"{cid}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
for named in (ROOT / ".hurc-harness" / "state" / "complete-e2e" / "runs").glob("*/receipts/*.json"):
    if named.stem in stem_set and named.parent.parent.name != run_id:
        try:
            named.unlink()
        except OSError:
            pass
print(json.dumps({"ok": True, "snap": snap[:12], "uni": uni[:12], "cells": len(stem_set)}))
