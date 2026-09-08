#!/usr/bin/env python3
from __future__ import annotations
import json
surfaces = [
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
print(json.dumps({"surfaces": surfaces}, separators=(",", ":")))
