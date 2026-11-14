#!/usr/bin/env python3
"""Validate, import, or project a prepared video-evidence manifest."""
import argparse
import json
from pathlib import Path
from aiforstudy.core.video_evidence import validate_video_evidence, import_video_evidence, project_video_evidence

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('command', choices=('validate', 'import', 'project'))
p.add_argument('input', type=Path)
p.add_argument('output', type=Path, nargs='?')
p.add_argument('--course-id')
a = p.parse_args()
if a.command == 'validate':
    result = validate_video_evidence(a.input)
else:
    if a.output is None: p.error('output is required')
    result = (import_video_evidence(a.input, a.output) if a.command == 'import' else project_video_evidence(a.input, a.output, course_id=a.course_id))
print(json.dumps(result, ensure_ascii=False, indent=2))
if result.get('ok') is False: raise SystemExit(1)
