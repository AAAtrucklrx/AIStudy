"""Validation and portable, content-addressed video evidence bundles.

Observations are records, not assertions of semantic correctness.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import shutil
import tempfile
from pathlib import Path
from .course_library import local_file, sha256


def validate_video_evidence(manifest_path: Path) -> dict:
    path = Path(manifest_path)
    errors = []
    try:
        m = json.loads(path.read_text(encoding='utf-8'))
        if m.get('schema_version') != '1.0' or not isinstance(m.get('course_id'), str) or not m['course_id']:
            errors.append('invalid schema version or course_id')
        duration, width, height = m['duration_seconds'], m['width'], m['height']
        if not (type(duration) in (int, float) and math.isfinite(duration) and duration > 0 and type(width) is int and width > 0 and type(height) is int and height > 0):
            errors.append('invalid media dimensions or duration')
        tb = m['time_base'].split('/')
        if len(tb) != 2 or any(not x.isdigit() or int(x) <= 0 for x in tb): errors.append('invalid time_base')
        ids = set()
        paths = set()
        for f in m['files']:
            if not isinstance(f.get('id'), str) or not f['id'] or f['id'] in ids: errors.append('duplicate or invalid file id')
            ids.add(f['id'])
            if f.get('path') in paths or f.get('path') == 'manifest.json': errors.append('duplicate or reserved file path')
            paths.add(f.get('path'))
            try:
                p = local_file(path.parent, f['path'])
                if not p.is_file() or sha256(p) != f['sha256']: errors.append('file missing or hash mismatch: ' + f['id'])
            except (OSError, ValueError): errors.append('unsafe or unreadable path: ' + f['id'])
        obs_ids = set()
        for o in m['observations']:
            if not isinstance(o.get('id'), str) or not o['id'] or o['id'] in obs_ids: errors.append('duplicate or invalid observation id')
            obs_ids.add(o['id'])
            if o.get('source_id') not in ids: errors.append('missing observation source')
            if not isinstance(o.get('evidence_ids', []), list) or any(ref not in ids for ref in o.get('evidence_ids', [])): errors.append('missing evidence reference')
            start, end = o['start'], o['end']
            if not (type(start) in (int,float) and type(end) in (int,float) and math.isfinite(start) and math.isfinite(end) and 0 <= start <= end <= duration): errors.append('invalid time interval')
            if 'bbox' in o:
                b = o['bbox']
                if not (isinstance(b,list) and len(b)==4 and all(type(x) in (int,float) and math.isfinite(x) for x in b) and 0 <= b[0] < b[2] <= width and 0 <= b[1] < b[3] <= height): errors.append('invalid bbox')
            if o.get('host_verified') is True: errors.append('host verification is not established by manifest')
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        errors.append('invalid manifest: ' + str(exc))
    return {'ok': not errors, 'errors': errors}


def import_video_evidence(manifest_path: Path, destination: Path) -> dict:
    path = Path(manifest_path)
    result = validate_video_evidence(path)
    if not result['ok']: raise ValueError('; '.join(result['errors']))
    raw = path.read_bytes()
    fingerprint = hashlib.sha256(raw).hexdigest()
    dest = Path(destination); dest.mkdir(parents=True, exist_ok=True)
    target = dest / fingerprint
    if target.exists():
        checked = validate_video_evidence(target / 'manifest.json')
        if not checked['ok'] or (target / 'manifest.json').read_bytes() != raw: raise ValueError('existing bundle is invalid')
        return {'bundle': str(target), 'fingerprint': fingerprint}
    stage = Path(tempfile.mkdtemp(prefix='.video-', dir=dest))
    try:
        m = json.loads(raw)
        for f in m['files']:
            source = local_file(path.parent, f['path'])
            out = stage / f['path']; out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, out)
            if sha256(out) != f['sha256']: raise ValueError('file changed during import')
            out.chmod(0o444)
        (stage / 'manifest.json').write_bytes(raw)
        (stage / 'manifest.json').chmod(0o444)
        os.rename(stage, target)
    finally:
        if stage.exists(): shutil.rmtree(stage)
    return {'bundle': str(target), 'fingerprint': fingerprint}


def project_video_evidence(bundle: Path, output: Path, *, course_id: str | None = None) -> dict:
    """Create a standalone local evidence view; never infer course membership."""
    import html
    from urllib.parse import quote
    bundle, output = Path(bundle), Path(output)
    result = validate_video_evidence(bundle / 'manifest.json')
    if not result['ok']: raise ValueError('; '.join(result['errors']))
    m = json.loads((bundle / 'manifest.json').read_text(encoding='utf-8'))
    if course_id is not None and course_id != m['course_id']: raise ValueError('course mismatch')
    if output.exists() and any(output.iterdir()): raise ValueError('output must be empty')
    output.mkdir(parents=True, exist_ok=True)
    for f in m['files']:
        p = output / f['path']; p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local_file(bundle, f['path']), p)
    files = {f['id']: f for f in m['files']}
    video = files[m['observations'][0]['source_id']]['path'] if m['observations'] else m['files'][0]['path']
    rows = []
    for o in m['observations']:
        label = html.escape(str(o.get('text', o['id'])))
        links = ''.join(f' <a href="{html.escape(quote(files[ref]["path"], safe="/"), quote=True)}">{html.escape(ref)}</a>' for ref in o.get('evidence_ids', []))
        category = html.escape(str(o.get('category', '观察')))
        rows.append(f'<li><button type="button" data-time="{o["start"]}">{o["start"]} 秒</button> [{category}] {label}{links}</li>')
    page = '''<!doctype html><html lang="zh"><meta charset="utf-8"><title>视频证据回看</title><h1>视频证据回看</h1><p>观察记录和模型候选不代表语义核验或完整理解。</p><video controls preload="metadata" width="800" src="%s"></video><ul>%s</ul><script>document.querySelectorAll('[data-time]').forEach(b=>b.addEventListener('click',()=>{const v=document.querySelector('video');v.currentTime=Number(b.dataset.time);v.focus()}));</script></html>''' % (html.escape(quote(video, safe='/'), quote=True), ''.join(rows))
    (output / 'index.html').write_text(page, encoding='utf-8')
    return {'index': str(output / 'index.html'), 'course_id': m['course_id'], 'fingerprint': hashlib.sha256((bundle / 'manifest.json').read_bytes()).hexdigest()}
