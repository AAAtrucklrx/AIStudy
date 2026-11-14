"""Pinned, offline PCM cache for independently running native speech workers."""
import hashlib
import json
from pathlib import Path
import shutil
from .narration_providers import _wave_info


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def cache_key(text, identity):
    return hashlib.sha256(json.dumps({'text':text,'identity':identity},ensure_ascii=False,sort_keys=True,allow_nan=False).encode()).hexdigest()


class LocalCacheBackend:
    """No synthesis fallback: a worker must first publish a verified PCM entry."""
    def __init__(self, config):
        self.config=config
        self.source=json.loads(json.dumps(config['identity']))
        self.cache=Path(config['cache_dir'])

    def synthesize(self,text,destination):
        key=cache_key(text,self.source);folder=self.cache/key
        try:
            result=json.loads((folder/'result.json').read_text())
            audio=folder/'audio.wav'
            if (result.get('cache_key')!=key or result.get('audio_sha256')!=digest(audio)
                    or result.get('identity')!=self.source or result.get('text')!=text):
                raise ValueError('identity/hash mismatch')
            info=_wave_info(audio.read_bytes())
        except (OSError,ValueError,KeyError) as exc:
            raise ValueError(f'Local narration cache missing or invalid ({key}); run the pinned worker; no fallback') from exc
        shutil.copyfile(audio,destination)
        return {**info,'alignment':{'status':'unavailable','tracks':[]},'local_cache_key':key}
