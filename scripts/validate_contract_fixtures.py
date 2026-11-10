#!/usr/bin/env python3
"""JSON Schema validation only. Cannot verify signatures/actual API runtime."""
from pathlib import Path
import json,sys
try:
 import jsonschema
except ImportError:
 print('MISSING_DEPENDENCY: install jsonschema==4.26.0 (CI installs it)')
 sys.exit(2)
root=Path(__file__).resolve().parents[1]
items=[('question_v1','question_valid',True),('question_v1','question_invalid',False),('evidence_bundle_v1','evidence_valid_schema_only',True),('grade_event_v1','grade_valid',True),('grade_event_v1','grade_invalid_correction',False),('course_operation_v1','course_operation_valid',True)]
for schema_name,fixture_name,expected in items:
 schema=json.loads((root/f'contracts/schemas/{schema_name}.schema.json').read_text())
 jsonschema.Draft202012Validator.check_schema(schema)
 obj=json.loads((root/f'contracts/fixtures/{fixture_name}.json').read_text())
 valid=not list(jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).iter_errors(obj))
 assert valid==expected,f'{fixture_name} Schema expected {expected}, got {valid}'
 print('PASS:',fixture_name,'valid' if valid else 'rejected as designed')
print('6/6 fixture schema tests PASS. Crypto, expiry, revocation and real HTTP are NOT TESTED.')
