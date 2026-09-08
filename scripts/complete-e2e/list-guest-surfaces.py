#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
surfaces = []
for rel in sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in ROOT.rglob("*.php") if "/tmpl/" in str(p).replace("\\", "/") and ".hurc-harness" not in str(p) and "/build/" not in str(p)):
    surfaces.append({
        "id": f"ui:{rel}",
        "kind": "web-ui",
        "path": rel,
        "origin": "runtime",
        "discovered": True,
        "behavior_proven": False,
    })
# Module + option surfaces
surfaces.append({
    "id": "joomla:option:com_timeclock",
    "kind": "web-ui",
    "path": "index.php?option=com_timeclock&view=timesheet",
    "origin": "runtime",
    "discovered": True,
    "behavior_proven": False,
})
surfaces.append({
    "id": "ndp:view:TimeclockTimesheet",
    "kind": "web-ui",
    "path": "index.php?option=com_timeclock&view=timesheet",
    "origin": "runtime",
    "discovered": True,
    "behavior_proven": False,
})
print(json.dumps({"surfaces": surfaces}, separators=(",", ":")))
