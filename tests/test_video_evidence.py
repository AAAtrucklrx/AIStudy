import hashlib
import json
from pathlib import Path
import pytest
from aiforstudy.core.video_evidence import validate_video_evidence, import_video_evidence


def fixture(tmp_path):
    (tmp_path / 'clip.mp4').write_bytes(b'video')
    m = {'schema_version':'1.0', 'course_id':'physics', 'duration_seconds':10, 'width':100, 'height':80, 'time_base':'1/1000', 'files':[{'id':'video', 'path':'clip.mp4', 'sha256':hashlib.sha256(b'video').hexdigest()}], 'observations':[{'id':'o1', 'source_id':'video', 'start':1, 'end':2, 'bbox':[0,0,100,80], 'model_status':'verified'}]}
    p = tmp_path / 'manifest.json'; p.write_text(json.dumps(m)); return p, m


def test_import_and_model_verification(tmp_path):
    p, m = fixture(tmp_path)
    assert validate_video_evidence(p)['ok']
    out = import_video_evidence(p, tmp_path / 'out')
    stored = json.loads((Path(out['bundle']) / 'manifest.json').read_text())
    assert stored['observations'][0].get('host_verified') is not True
    assert (Path(out['bundle']) / 'clip.mp4').read_bytes() == b'video'


@pytest.mark.parametrize('change', ['escape','hash','negative','overflow','timebase','bbox','duplicate','reference'])
def test_reject_invalid(tmp_path, change):
    p, m = fixture(tmp_path)
    if change == 'escape': m['files'][0]['path'] = '../clip.mp4'
    if change == 'hash': m['files'][0]['sha256'] = '0'*64
    if change == 'negative': m['observations'][0]['start'] = -1
    if change == 'overflow': m['observations'][0]['end'] = 11
    if change == 'timebase': m['time_base'] = '0/0'
    if change == 'bbox': m['observations'][0]['bbox'] = [0,0,101,80]
    if change == 'duplicate': m['observations'].append(m['observations'][0])
    if change == 'reference': m['observations'][0]['source_id'] = 'missing'
    p.write_text(json.dumps(m))
    assert not validate_video_evidence(p)['ok']
    with pytest.raises(ValueError): import_video_evidence(p, tmp_path / 'out')


def test_projection_and_course_guard(tmp_path):
    from aiforstudy.core.video_evidence import project_video_evidence
    p, _ = fixture(tmp_path)
    bundle = Path(import_video_evidence(p, tmp_path / 'out')['bundle'])
    with pytest.raises(ValueError): project_video_evidence(bundle, tmp_path / 'view', course_id='complex-analysis')
    result = project_video_evidence(bundle, tmp_path / 'view', course_id='physics')
    assert 'currentTime' in (Path(result['index'])).read_text()
    assert (tmp_path / 'view' / 'clip.mp4').read_bytes() == b'video'


def test_reject_missing_evidence_and_external_symlink(tmp_path):
    p, m = fixture(tmp_path)
    m['observations'][0]['evidence_ids'] = ['absent']
    p.write_text(json.dumps(m))
    assert not validate_video_evidence(p)['ok']
    outside = tmp_path.parent / (tmp_path.name + '-outside')
    outside.write_bytes(b'video')
    (tmp_path / 'clip.mp4').unlink()
    (tmp_path / 'clip.mp4').symlink_to(outside)
    m['observations'][0]['evidence_ids'] = []
    p.write_text(json.dumps(m))
    assert not validate_video_evidence(p)['ok']
