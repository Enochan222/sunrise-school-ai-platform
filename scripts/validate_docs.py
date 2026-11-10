#!/usr/bin/env python3
"""GitHub backward-compatible name; semantic and structural checks now invoked here."""
from verify_kit import validate
from validate_stage_controls import inspect
from pathlib import Path
import json,sys
root=Path(__file__).resolve().parents[1]
p,e=validate(root)
q,extra=inspect(root)
p+=q
e.extend(extra)
print(json.dumps({'result':'PASS' if not e else 'FAIL','checks_passed':p,'checks_failed':len(e),'failures':e[:60],'scope':'STATIC CONTRACT QA, NOT RUNTIME'},ensure_ascii=False,indent=2))
sys.exit(bool(e))
