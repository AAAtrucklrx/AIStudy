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


def worker_identity(manifest):
    hashes={f["file"]:f["sha256"] for f in manifest["files"]}
    return {'backend':'local-qwen3-tts','adapter_version':'local-pcm-cache-1','model':manifest['repo'],'revision':manifest['revision'],'files':hashes,'voice':'serena','language':'chinese','seed':20261115,'instruction':'用清晰、自然、温和的普通话讲解数学。语速适中，在句意完整的地方停顿，关键术语读清楚。','max_tokens':2304,'stream':False,'mlx_audio_version':'0.6.5','neural':True,'normalization':'none; float raw retained; PCM16 conversion only'}


class AutoLocalQwenBackend(LocalCacheBackend):
    """Cache hit stays CPU-only; a cross-process lock serializes cache misses."""
    def __init__(self, config):
        import os
        self.paths={}
        for key in ('model_dir','model_manifest','python','cache_dir'):
            value=config.get(key) or os.environ.get(config.get(key+'_env','AIFORSTUDY_TTS_'+key.upper()))
            if not value:raise ValueError('Local Qwen requires '+key+'; configure its explicit path/environment; no fallback')
            self.paths[key]=str(Path(value).expanduser().absolute() if key=='python' else Path(value).expanduser().resolve())
        manifest=json.loads(Path(self.paths['model_manifest']).read_text())
        if manifest.get('status')!='verified_complete':raise ValueError('Local Qwen model manifest must be verified')
        super().__init__({'identity':worker_identity(manifest),'cache_dir':self.paths['cache_dir']})
        self.timeout=float(config.get('timeout',900))
        if not 0<self.timeout<=3600:raise ValueError('Local worker timeout must be 0..3600 seconds')
        self.lock=Path(config.get('lock_file') or os.environ.get('AIFORSTUDY_TTS_LOCK_FILE',str(Path.home()/'.cache/aiforstudy/tts-gpu.lock'))).expanduser()

    def synthesize(self,text,destination):
        import fcntl
        import os
        import subprocess
        import tempfile
        import time
        if not isinstance(text,str) or not text.strip():raise ValueError('Nonempty spoken text required')
        receipt=self.cache/cache_key(text,self.source)/'result.json'
        if receipt.exists():return super().synthesize(text,destination)
        self.lock.parent.mkdir(parents=True,exist_ok=True)
        with self.lock.open('a') as lock:
            deadline=time.monotonic()+self.timeout
            while True:
                try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
                except BlockingIOError:
                    if time.monotonic()>=deadline:raise TimeoutError('Local Qwen GPU lock timeout; no fallback')
                    time.sleep(.05)
            try:
                if receipt.exists():return super().synthesize(text,destination)
                self.cache.mkdir(parents=True,exist_ok=True)
                with tempfile.TemporaryDirectory(prefix='.worker-',dir=self.cache) as directory:
                    directory=Path(directory);corpus=directory/'request.json'
                    corpus.write_text(json.dumps({'records':[{'id':cache_key(text,self.source),'comparison_spoken_text':text}]},ensure_ascii=False))
                    argv=[self.paths['python'],'-m','aiforstudy.blocks.media.local_speech_worker','--model-dir',self.paths['model_dir'],
                          '--model-manifest',self.paths['model_manifest'],'--corpus',str(corpus),'--cache-dir',str(self.cache),'--output-config',str(directory/'config.json')]
                    env=dict(os.environ)
                    env['PYTHONPATH']=str(Path(__file__).resolve().parents[3])
                    try:
                        subprocess.run(argv,check=True,timeout=self.timeout,env=env,capture_output=True)
                    except subprocess.CalledProcessError as exc:
                        raise RuntimeError('Local Qwen worker failed; no fallback: '+exc.stderr.decode('utf-8','replace')[-2000:]) from exc
                return super().synthesize(text,destination)
            finally:fcntl.flock(lock,fcntl.LOCK_UN)
