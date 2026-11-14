import json
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from aiforstudy.blocks.media.local_narration import AutoLocalQwenBackend


def backend(tmp_path):
    manifest=tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'status':'verified_complete','repo':'test','revision':'a','files':[]}))
    return AutoLocalQwenBackend({'model_dir':str(tmp_path),'model_manifest':str(manifest),'python':str(tmp_path/'python'),'cache_dir':str(tmp_path/'cache'),'lock_file':str(tmp_path/'gpu.lock'),'timeout':2})


def publish(b,text):
    import wave
    from aiforstudy.blocks.media.local_narration import cache_key,digest
    folder=b.cache/cache_key(text,b.source);folder.mkdir(parents=True,exist_ok=True)
    with wave.open(str(folder/'audio.wav'),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b'\x01\x00'*24000)
    (folder/'result.json').write_text(json.dumps({'cache_key':folder.name,'identity':b.source,'text':text,'audio_sha256':digest(folder/'audio.wav')}))


def test_miss_worker_protocol_and_concurrent_same_text_hit(tmp_path,monkeypatch):
    b=backend(tmp_path);calls=[]
    def run(args,**kwargs):
        request=json.loads(Path(args[args.index('--corpus')+1]).read_text())
        text=request['records'][0]['comparison_spoken_text'];calls.append(text)
        time.sleep(.05);publish(b,text)
    monkeypatch.setattr(subprocess,'run',run)
    with ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda i:b.synthesize('新句',tmp_path/f'{i}.wav'),range(2)))
    assert calls==['新句']
    b.synthesize('新句',tmp_path/'hit.wav');assert len(calls)==1


@pytest.mark.parametrize('failure',[RuntimeError('failed'),subprocess.TimeoutExpired('worker',2)])
def test_worker_failure_and_timeout_never_fallback(tmp_path,monkeypatch,failure):
    b=backend(tmp_path)
    def fail(*a,**k):raise failure
    monkeypatch.setattr(subprocess,'run',fail)
    with pytest.raises((RuntimeError,subprocess.TimeoutExpired)):b.synthesize('失败',tmp_path/'out.wav')
    assert not (tmp_path/'out.wav').exists()


def test_corrupt_cache_rejected_without_worker(tmp_path,monkeypatch):
    b=backend(tmp_path);publish(b,'坏缓存')
    next(b.cache.glob('*/audio.wav')).write_bytes(b'broken')
    monkeypatch.setattr(subprocess,'run',lambda *a,**k:pytest.fail('must not silently regenerate corrupt cache'))
    with pytest.raises(ValueError,match='cache'):b.synthesize('坏缓存',tmp_path/'out.wav')


def test_different_misses_serialized_and_identity_revision_changes_key(tmp_path,monkeypatch):
    from aiforstudy.blocks.media.local_narration import cache_key
    b=backend(tmp_path);active=0;peak=0
    def run(args,**kwargs):
        nonlocal active,peak
        active+=1;peak=max(peak,active);time.sleep(.05)
        text=json.loads(Path(args[args.index('--corpus')+1]).read_text())['records'][0]['comparison_spoken_text']
        publish(b,text);active-=1
    monkeypatch.setattr(subprocess,'run',run)
    with ThreadPoolExecutor(2) as pool:list(pool.map(lambda i:b.synthesize(str(i),tmp_path/f'{i}.wav'),range(2)))
    assert peak==1
    old=cache_key('0',b.source)
    manifest=tmp_path/'manifest.json';data=json.loads(manifest.read_text());data['revision']='b';manifest.write_text(json.dumps(data))
    changed=AutoLocalQwenBackend({**b.paths,'lock_file':str(b.lock)})
    assert cache_key('0',changed.source)!=old


def test_interpreter_symlink_preserves_virtualenv_entrypoint(tmp_path):
    b=backend(tmp_path)
    target=tmp_path/'system-python';target.touch()
    link=tmp_path/'python';link.symlink_to(target)
    b=AutoLocalQwenBackend({**b.paths,'lock_file':str(b.lock)})
    assert b.paths['python']==str(link)
