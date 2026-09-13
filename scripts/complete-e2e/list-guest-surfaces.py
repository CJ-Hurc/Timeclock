#!/usr/bin/env python3
"""Emit Timeclock guest/web-ui surfaces. Unknown flags fail-closed."""
from __future__ import annotations
import argparse
import json
import sys

SURFACES = [
    {
        "id": "ndp:view:TimeclockTimesheet",
        "kind": "web-ui",
        "path": "index.php?option=com_timeclock&view=timesheet",
        "origin": "runtime",
        "discovered": True,
        "behavior_proven": False,
    },
    {
        "id": "ui:components/com_timeclock/tmpl/timesheet/default.php",
        "kind": "web-ui",
        "path": "components/com_timeclock/tmpl/timesheet/default.php",
        "origin": "runtime",
        "discovered": True,
        "behavior_proven": False,
    },
    {
        "id": "ui:administrator/components/com_timeclock/tmpl/timesheets/default.php",
        "kind": "web-ui",
        "path": "administrator/components/com_timeclock/tmpl/timesheets/default.php",
        "origin": "runtime",
        "discovered": True,
        "behavior_proven": False,
    },
    {
        "id": "ui:mod_timeclockinfo/tmpl/default.php",
        "kind": "web-ui",
        "path": "mod_timeclockinfo/tmpl/default.php",
        "origin": "runtime",
        "discovered": True,
        "behavior_proven": False,
    },
]


def main() -> int:
    ap = argparse.ArgumentParser(description="usage: list-guest-surfaces.py [--help]")
    ap.parse_args()
    print(json.dumps({"surfaces": SURFACES}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
