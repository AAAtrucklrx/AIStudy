"""Persistent local video analysis. All model work uses the configured production Gateway.

Public inputs identify controlled uploads; filesystem imports are a separate CLI API.
Process locks are inherited by workers so restarting a server cannot reuse a live job.
"""
from __future__ import annotations

import base64
import contextlib
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import threading
import time
from types import SimpleNamespace
import uuid

from .jsonio import write_json_atomic
from ..errors import Cancelled
from ..pipeline.services import CancelToken

VERSION = 'video-analysis-v1.0'
STAGES = ('probe', 'audio', 'frames', 'asr', 'ocr', 'vision', 'lesson', 'review', 'export')
ACTIVE = {'queued', 'running', 'cancelling'}
ID = re.compile(r'^[a-f0-9]{32}$')
VIDEO_COMPONENTS = ('core/video_analysis.py', 'core/video_analysis_models.py', 'core/video_recognition_worker.py')


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _safe_public(value):
    if isinstance(value, dict):
        return {k: _safe_public(v) for k, v in value.items() if k not in {'worker_pid', 'config', 'owner', 'artifacts'}}
    if isinstance(value, list):
        return [_safe_public(v) for v in value]
    if isinstance(value, str) and value.startswith('/'):
        return Path(value).name
    return value


def validate_lesson(value, source_ids, duration):
    """Reject fabricated evidence and out-of-video timestamps; preserve model text."""
    if not isinstance(value, dict) or not isinstance(value.get('sections'), list) or not value['sections']:
        raise ValueError('lesson requires nonempty sections')
    for section in value['sections']:
        if not isinstance(section, dict) or not all(isinstance(section.get(k), str) and section[k].strip() for k in ('id', 'title', 'markdown')):
            raise ValueError('Invalid section text')
        start, end = section.get('start'), section.get('end')
        if not all(type(v) in (float, int) and math.isfinite(v) for v in (start, end)) or not 0 <= start < end <= duration + .1:
            raise ValueError('Invalid section time range')
        refs = section.get('evidence_ids')
        if not isinstance(refs, list) or not refs or any(not isinstance(r, str) or r not in source_ids for r in refs):
            raise ValueError('Invalid evidence source ids')
        inline = re.findall(r'\[((?:frame|asr)-[a-zA-Z0-9-]+)\]', section['markdown'])
        if any(reference not in refs or reference not in source_ids for reference in inline):
            raise ValueError('Invalid inline evidence source ids')
    if not isinstance(value.get('formulas', []), list):
        raise ValueError('Invalid formulas list')
    for formula in value.get('formulas', []):
        if not isinstance(formula, dict):
            raise ValueError('Invalid formula object')
        refs = formula.get('source_ids')
        if not isinstance(formula.get('latex'), str) or not isinstance(refs, list) or not refs or any(not isinstance(r, str) or r not in source_ids for r in refs):
            raise ValueError('Invalid formula source ids')
        if not isinstance(formula.get('uncertainty', ''), str):
            raise ValueError('Invalid formula uncertainty')
    if not isinstance(value.get('uncertainties', []), list) or any(not isinstance(x, str) for x in value.get('uncertainties', [])):
        raise ValueError('Invalid uncertainties')
    return value


class _FileCancel(CancelToken):
    def __init__(self, path):
        super().__init__(grace_seconds=3)
        self.path = path

    def checkpoint(self):
        if self.path.exists():
            self.cancel('用户取消视频解析')
        super().checkpoint()


class VideoAnalysisService:
    def __init__(self, workspace_root):
        self.workspace_root = Path(workspace_root).resolve()
        self.root = self.workspace_root / 'data' / 'video-analysis'
        self.uploads, self.jobs = self.root / 'uploads', self.root / 'jobs'
        self.uploads.mkdir(parents=True, exist_ok=True)
        self.jobs.mkdir(parents=True, exist_ok=True)
        self._mutex = threading.RLock()
        self._threads, self._tokens = {}, {}
        self._local = threading.local()
        config_path = self.workspace_root / 'config' / 'video-analysis.json'
        config = _read(config_path) if config_path.is_file() else {}
        self.config = {
            'version': VERSION,
            'asr_python': os.environ.get('AIFORSTUDY_VIDEO_ASR_PYTHON', config.get('asr_python', '')),
            'asr_model': os.environ.get('AIFORSTUDY_VIDEO_ASR_MODEL', config.get('asr_model', '')),
            'ocr_python': os.environ.get('AIFORSTUDY_VIDEO_OCR_PYTHON', config.get('ocr_python', '')),
            'sample': os.environ.get('AIFORSTUDY_VIDEO_SAMPLE', config.get('sample', '')),
            'sample_url': config.get('sample_url', ''),
            'frame_interval': float(config.get('frame_interval', 20)),
            'max_frames': int(config.get('max_frames', 96)),
            'scene_threshold': float(config.get('scene_threshold', .12)),
            'vision_batch_size': int(config.get('vision_batch_size', 6)),
            'chapter_seconds': float(config.get('chapter_seconds', 240)),
            'review': bool(config.get('review', True)),
            'max_duration_seconds': float(config.get('max_duration_seconds', 14400)),
        }
        if self.config['frame_interval'] < 5 or not 4 <= self.config['max_frames'] <= 300 or not 1 <= self.config['vision_batch_size'] <= 8 or self.config['chapter_seconds'] < 30:
            raise ValueError('Invalid video analysis bounds')
        self.max_upload_bytes = int(config.get('max_upload_bytes', 2 * 1024 ** 3))
        for path in self.jobs.glob('*/job.json'):
            self._recover(path.parent.name)

    @contextlib.contextmanager
    def _lock(self, path, blocking=True):
        with Path(path).open('a+b') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
            try:
                yield handle
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def _jobdir(self, job_id):
        if not isinstance(job_id, str) or not ID.fullmatch(job_id):
            raise KeyError('Unknown video job')
        directory = self.jobs / job_id
        if not (directory / 'job.json').is_file():
            raise KeyError('Unknown video job')
        return directory

    def _recover(self, job_id):
        directory = self._jobdir(job_id)
        with self._mutex:
            job = _read(directory / 'job.json')
            if job['state'] not in ACTIVE or job_id in self._threads:
                return
            try:
                with self._lock(directory / 'worker.lock', False):
                    self._update(job_id, state='cancelled' if (directory / 'cancel.request').exists() else 'interrupted', error='上次处理已停止，可恢复已完成阶段。')
            except BlockingIOError:
                pass  # A live worker (including inherited child lock) still owns it.

    def capabilities(self):
        dependencies = {
            'ffmpeg': bool(shutil.which('ffmpeg')),
            'ffprobe': bool(shutil.which('ffprobe')),
            'asr_python': bool(self.config['asr_python'] and Path(self.config['asr_python']).is_file()),
            'asr_model': bool(self.config['asr_model'] and Path(self.config['asr_model']).exists()),
            'ocr_python': bool((self.config['ocr_python'] or self.config['asr_python']) and Path(self.config['ocr_python'] or self.config['asr_python']).is_file()),
        }
        try:
            from ..providers.factory import configured_providers
            from .workspace import Workspace
            dependencies['model_transport'] = configured_providers(SimpleNamespace(profile=SimpleNamespace(value='release')), Workspace(self.workspace_root)).llm is not None
        except Exception:
            dependencies['model_transport'] = False
        return {'available': all(dependencies.values()), 'dependencies': dependencies,
                'max_upload_bytes': self.max_upload_bytes,
                'sample_available': bool(self.config['sample'] and Path(self.config['sample']).is_file()),
                'stages': list(STAGES), 'coverage_note': '音频按重叠窗口覆盖全片；画面为定时和变化采样，并非逐帧解析。'}

    def register_upload(self, stream, length, filename):
        if type(length) is not int or not 0 < length <= self.max_upload_bytes:
            raise ValueError('Invalid upload length or upload exceeds limit')
        filename = str(filename).replace('\\', '/').rsplit('/', 1)[-1].strip()[:180] or 'video.mp4'
        if Path(filename).suffix.lower() not in {'.mp4', '.mov', '.mkv', '.webm', '.m4v', '.avi'}:
            raise ValueError('Unsupported video filename extension')
        source_id = uuid.uuid4().hex
        partial = self.uploads / (source_id + '.part')
        target = self.uploads / (source_id + '.video')
        digest = hashlib.sha256()
        try:
            remaining = length
            with partial.open('xb') as out:
                while remaining:
                    data = stream.read(min(1024 * 1024, remaining))
                    if not isinstance(data, bytes) or not data or len(data) > remaining:
                        raise ValueError('Upload length mismatch; incomplete upload')
                    out.write(data); digest.update(data); remaining -= len(data)
                out.flush(); os.fsync(out.fileno())
            os.replace(partial, target)
            row = {'id': source_id, 'source_id': source_id, 'filename': filename, 'bytes': length, 'sha256': digest.hexdigest(), 'created_at': time.time()}
            write_json_atomic(self.uploads / (source_id + '.json'), row)
            return row
        except BaseException:
            partial.unlink(missing_ok=True); target.unlink(missing_ok=True)
            raise

    def import_source(self, source_path):
        """Explicit local CLI only. Never called with browser JSON."""
        path = Path(source_path).expanduser().resolve(strict=True)
        if not path.is_file():
            raise ValueError('Source must be a regular video file')
        with path.open('rb') as stream:
            return self.register_upload(stream, path.stat().st_size, path.name)

    def sample(self):
        if not self.config['sample']:
            raise ValueError('No video sample configured')
        path = Path(self.config['sample'])
        digest = _sha(path)
        for metadata in self.uploads.glob('*.json'):
            row = _read(metadata)
            if row['sha256'] == digest and (self.uploads / (row['id'] + '.video')).is_file():
                return row
        return self.import_source(path)

    def _dependency_identity(self):
        # Reuse the media cache's declared component and effective-provider identity.
        # No credential values or credential digests are read into this descriptor.
        from ..blocks.media.dependencies import component_identity, file_identity, model_role_identity
        from ..pipeline.runtime_dependencies import COMMON
        from .video_recognition_worker import _model_identity
        from ..providers.factory import configured_providers
        from .workspace import Workspace
        dependencies = {'components': component_identity(VIDEO_COMPONENTS + COMMON)}
        model = self.config['asr_model']
        dependencies['asr_model'] = _model_identity(model) if model and Path(model).is_dir() else 'unconfigured'
        runtimes = {}
        worker = Path(__file__).with_name('video_recognition_worker.py')
        script = 'import runpy,sys,json; print(json.dumps(runpy.run_path(sys.argv[1])["_runtime"](sys.argv[2])))'
        for mode in ('asr', 'ocr'):
            interpreter = self.config[mode + '_python'] or (self.config['asr_python'] if mode == 'ocr' else '')
            identity = {'interpreter': file_identity(interpreter)}
            if interpreter and Path(interpreter).is_file():
                result = subprocess.run([interpreter, '-c', script, str(worker), mode], capture_output=True, text=True, timeout=20)
                if result.returncode:
                    raise ValueError('Unable to identify ' + mode + ' runtime')
                identity['runtime'] = json.loads(result.stdout)
            runtimes[mode] = identity
        dependencies['runtimes'] = runtimes
        dependencies['media_tools'] = {tool: file_identity(shutil.which(tool)) for tool in ('ffmpeg', 'ffprobe', 'clang')}
        dependencies['ocr_executable'] = file_identity(os.environ.get('AIFORSTUDY_VIDEO_OCR_EXECUTABLE'))
        config_path = self.workspace_root / 'config' / 'models.json'
        dependencies['roles'] = {}
        if config_path.is_file():
            workspace = Workspace(self.workspace_root)
            providers = configured_providers(SimpleNamespace(profile=SimpleNamespace(value='release')), workspace)
            ctx = SimpleNamespace(workspace=workspace, services=SimpleNamespace(providers=providers))
            roles = set(_read(config_path).get('roles', {})) & {'source_repair', 'lesson', 'text_judge'}
            for role in sorted(roles):
                dependencies['roles'][role] = model_role_identity(ctx, role)
                transport = providers.llm.for_role(role) if hasattr(providers.llm, 'for_role') else providers.llm
                if getattr(transport, 'harness_app', None):
                    app = Path(transport.harness_app)
                    dependencies['roles'][role]['account_sdk'] = {
                        'app_archive': file_identity(app / 'Contents/Resources/app.asar'),
                        'executable': file_identity(app / 'Contents/MacOS/DeepSeek Harness')}
        return dependencies

    def _config_snapshot(self):
        model_config = self.workspace_root / 'config' / 'models.json'
        execution = self.workspace_root / 'config' / 'execution.json'
        return dict(self.config, model_config_sha256=_sha(model_config) if model_config.is_file() else '',
                    execution_policy_sha256=_sha(execution) if execution.is_file() else '', dependencies=self._dependency_identity())

    def submit(self, payload):
        if not isinstance(payload, dict) or set(payload) - {'source_id', 'title', 'course_id', 'force'}:
            raise ValueError('Only source_id, title, course_id and force are accepted')
        source_id = payload.get('source_id')
        if not isinstance(source_id, str) or not ID.fullmatch(source_id):
            raise ValueError('Invalid source_id')
        path = self.uploads / (source_id + '.json')
        if not path.is_file():
            raise KeyError('Unknown source_id')
        source = _read(path)
        if _sha(self.uploads / (source_id + '.video')) != source['sha256']:
            raise ValueError('Uploaded source integrity mismatch')
        title = str(payload.get('title') or Path(source['filename']).stem)[:200]
        course_id = str(payload.get('course_id') or 'video-course')[:100]
        cfg = self._config_snapshot()
        identity = _digest({'source': source['sha256'], 'config': cfg, 'title': title, 'course_id': course_id})
        with self._lock(self.root / 'registry.lock'):
            if not payload.get('force'):
                for path in self.jobs.glob('*/job.json'):
                    existing = _read(path)
                    if existing['identity'] == identity:
                        return self.get(existing['job_id'])
            job_id = uuid.uuid4().hex; directory = self.jobs / job_id; directory.mkdir()
            row = {'job_id': job_id, 'source_id': source_id, 'title': title, 'course_id': course_id,
                   'identity': identity, 'config': cfg, 'source_sha256': source['sha256'], 'source_filename': source['filename'],
                   'state': 'queued', 'stage': 'queued', 'progress': 0, 'created_at': time.time(), 'updated_at': time.time(),
                   'stages': {s: {'state': 'pending', 'progress': 0} for s in STAGES}, 'events': [], 'artifacts': [], 'error': None}
            write_json_atomic(directory / 'job.json', row)
            self._launch(job_id)
            return self.get(job_id)

    def list_jobs(self):
        return sorted([self.get(p.parent.name, include_result=False) for p in self.jobs.glob('*/job.json')], key=lambda x: x['created_at'], reverse=True)

    def get(self, job_id, include_result=True):
        row = _read(self._jobdir(job_id) / 'job.json')
        if row['state'] in {'running', 'cancelling'} and job_id not in self._threads:
            self._recover(job_id)
            row = _read(self._jobdir(job_id) / 'job.json')
        # Queued jobs may legitimately be waiting for their first thread start.
        public = _safe_public(row)
        if include_result and row['state'] == 'completed':
            public['result'] = _read(self._jobdir(job_id) / 'result.json')
        return public

    def _update(self, job_id, **values):
        directory = self._jobdir(job_id)
        with self._mutex, self._lock(directory / 'metadata.lock'):
            row = _read(directory / 'job.json'); row.update(values); row['updated_at'] = time.time()
            write_json_atomic(directory / 'job.json', row)
            return row

    def _event(self, job_id, message, **values):
        with self._mutex:
            row = _read(self._jobdir(job_id) / 'job.json')
            event = {'time': time.time(), 'message': message, **values}
            row['events'] = (row['events'] + [event])[-200:]
            with (self._jobdir(job_id) / 'events.jsonl').open('a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
            self._update(job_id, events=row['events'])

    def cancel(self, job_id):
        row = self.get(job_id, False)
        if row['state'] in ACTIVE:
            (self._jobdir(job_id) / 'cancel.request').touch()
            token = self._tokens.get(job_id)
            if token:
                token.cancel('用户取消视频解析')
            self._update(job_id, state='cancelling')
            if job_id not in self._threads:
                self._recover(job_id)
        return self.get(job_id)

    def resume(self, job_id):
        directory = self._jobdir(job_id)
        self._recover(job_id)
        row = _read(directory / 'job.json')
        if row['state'] == 'completed':
            return self.get(job_id)
        if row['state'] in ACTIVE:
            raise ValueError('任务仍有活动worker，不能重复恢复')
        current_config = self._config_snapshot()
        if row['config'] != current_config:
            raise ValueError('运行配置已改变，请重新分析，不能混用先前结果')
        (directory / 'cancel.request').unlink(missing_ok=True)
        self._update(job_id, state='queued', error=None)
        self._launch(job_id)
        return self.get(job_id)

    def _register_artifacts(self, job_id, paths):
        with self._mutex:
            row = _read(self._jobdir(job_id) / 'job.json')
            self._update(job_id, artifacts=sorted(set(row['artifacts']) | set(paths)))

    def artifact(self, job_id, relative):
        try:
            directory = self._jobdir(job_id)
            if not isinstance(relative, str) or '\\' in relative or '..' in Path(relative).parts or Path(relative).is_absolute():
                return None
            if relative not in _read(directory / 'job.json')['artifacts']:
                return None
            target = (directory / relative).resolve()
            return target if target.is_relative_to(directory.resolve()) and target.is_file() else None
        except (KeyError, OSError, ValueError):
            return None

    def _launch(self, job_id):
        handle = (self._jobdir(job_id) / 'worker.lock').open('a+b')
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close(); raise ValueError('已有worker正在处理此任务')
        token = _FileCancel(self._jobdir(job_id) / 'cancel.request')
        self._tokens[job_id] = token
        thread = threading.Thread(target=self._run, args=(job_id, token, handle), name='video-' + job_id[:8], daemon=True)
        self._threads[job_id] = thread; thread.start()

    def _process(self, args, log, token, timeout=3600):
        """No shell; isolate process group; cancel, kill on grace expiry, always reap."""
        env = dict(os.environ)
        env['PYTHONPATH'] = str(self.workspace_root / 'src') + os.pathsep + env.get('PYTHONPATH', '')
        start = time.monotonic()
        last_progress = 0.0
        with Path(log).open('wb') as output:
            process = subprocess.Popen([str(x) for x in args], stdout=output, stderr=subprocess.STDOUT,
                start_new_session=True, env=env, pass_fds=tuple(getattr(self._local, 'lock_fds', ())))
            try:
                while process.poll() is None:
                    token.checkpoint()
                    if time.monotonic() - start > timeout:
                        raise TimeoutError('Video worker exceeded deadline')
                    if '--mode' in args and '--output' in args and time.monotonic() - last_progress >= 1:
                        last_progress = time.monotonic()
                        mode = args[args.index('--mode') + 1]
                        partial = Path(args[args.index('--output') + 1])
                        if partial.is_file() and getattr(self._local, 'job_id', None):
                            snapshot = _read(partial); coverage = snapshot.get('coverage', {})
                            expected = coverage.get('expected_windows' if mode == 'asr' else 'expected_frames', 0)
                            completed = len(snapshot.get('segments' if mode == 'asr' else 'frames', []))
                            if expected:
                                self._progress(self._local.job_id, mode, min(.99, completed / expected))
                    time.sleep(.1)
                token.checkpoint()
                if process.returncode:
                    raise RuntimeError('视频处理子进程失败：' + Path(log).name + '; exit=' + str(process.returncode))
            finally:
                if process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        process.wait()
                else:
                    process.wait()

    def _progress(self, job_id, stage, fraction):
        with self._mutex:
            row = _read(self._jobdir(job_id) / 'job.json')
            row['stages'][stage].update(progress=fraction, state='running')
            self._update(job_id, stages=row['stages'], progress=(STAGES.index(stage) + fraction) / len(STAGES))

    def _stage(self, job_id, stage, token, fn):
        token.checkpoint(); directory = self._jobdir(job_id); checkpoint = directory / (stage + '.done.json')
        row = _read(directory / 'job.json')
        if checkpoint.is_file():
            saved = _read(checkpoint)
            if all((directory / p).is_file() and _sha(directory / p) == sha for p, sha in saved['files'].items()):
                return saved['data']
            raise ValueError('阶段产物完整性校验失败，请重新分析')
        self._update(job_id, stage=stage)
        self._progress(job_id, stage, 0)
        self._event(job_id, '开始 ' + stage, stage=stage)
        data, files = fn()
        token.checkpoint()
        write_json_atomic(checkpoint, {'data': data, 'files': {p: _sha(directory / p) for p in files}})
        row = _read(directory / 'job.json'); row['stages'][stage].update(state='completed', progress=1, error=None)
        self._update(job_id, stages=row['stages'], progress=(STAGES.index(stage) + 1) / len(STAGES))
        self._event(job_id, '完成 ' + stage, stage=stage)
        return data

    def _run(self, job_id, token, handle):
        self._local.lock_fds = [handle.fileno()]
        self._local.job_id = job_id
        try:
            self._update(job_id, state='running', error=None)
            self._pipeline(job_id, token)
            token.checkpoint()
            self._update(job_id, state='completed', stage='completed', progress=1)
            self._event(job_id, '解析完成；采样覆盖不等于数学与语义全部核实')
        except Exception as exc:
            cancelled = isinstance(exc, Cancelled) or token.cancelled
            state = 'cancelled' if cancelled else 'failed'
            # Full diagnostics remain local, never expose arbitrary absolute paths.
            import traceback
            (self._jobdir(job_id) / 'failure.log').write_text(traceback.format_exc())
            message = '用户取消' if cancelled else type(exc).__name__ + ': ' + re.sub(r'/[^\s\"\']+', '[local-path]', str(exc))[:600]
            row = _read(self._jobdir(job_id) / 'job.json')
            stage = row.get('stage')
            if stage in row['stages']:
                row['stages'][stage].update(state=state, error=message)
            self._update(job_id, state=state, error=message, stages=row['stages'])
            self._event(job_id, message, stage=stage)
        finally:
            handle.close(); self._tokens.pop(job_id, None); self._threads.pop(job_id, None)

    def _pipeline(self, job_id, token):
        from .video_analysis_models import VideoModelSession
        d = self._jobdir(job_id); row = _read(d / 'job.json')
        source = d / ('source' + Path(row['source_filename']).suffix.lower())
        if not source.is_file():
            shutil.copyfile(self.uploads / (row['source_id'] + '.video'), source)
        if _sha(source) != row['source_sha256']:
            raise ValueError('Source integrity mismatch')
        self._register_artifacts(job_id, [source.name])
        run = lambda args, name, timeout=3600: self._process(args, d / name, token, timeout)
        def probe():
            run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', source], 'probe.json', 60)
            info = _read(d / 'probe.json')
            duration = float(info['format']['duration'])
            if not math.isfinite(duration) or not 0 < duration <= self.config['max_duration_seconds']:
                raise ValueError('Video duration exceeds configured range')
            types = {s['codec_type'] for s in info['streams']}
            if not {'video', 'audio'} <= types:
                raise ValueError('Teaching video requires video and audio streams')
            self._update(job_id, duration=duration)
            return {'duration': duration}, ['probe.json']
        info = self._stage(job_id, 'probe', token, probe); duration = info['duration']
        def audio():
            run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', source, '-map', '0:a:0', '-vn', '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', d / 'audio.wav'], 'audio.log')
            run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', source, '-map', '0:a:0', '-vn', '-ar', '48000', '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '96k', d / 'speech.mp3'], 'speech.log')
            run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', source, '-map', '0:v:0', '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', d / 'playback.mp4'], 'playback.log')
            self._register_artifacts(job_id, ['playback.mp4', 'speech.mp3'])
            return {}, ['audio.wav', 'speech.mp3', 'playback.mp4']
        self._stage(job_id, 'audio', token, audio)
        frames = self._stage(job_id, 'frames', token, lambda: self._extract_frames(job_id, source, duration, token))
        def asr():
            python, model = self.config['asr_python'], self.config['asr_model']
            if not python or not model:
                raise ValueError('Configure AIFORSTUDY_VIDEO_ASR_PYTHON and AIFORSTUDY_VIDEO_ASR_MODEL')
            # One GPU owner across jobs and server instances, inherited by ASR child.
            gpu = (self.root / 'gpu.lock').open('a+b')
            try:
                while True:
                    token.checkpoint()
                    try:
                        fcntl.flock(gpu, fcntl.LOCK_EX | fcntl.LOCK_NB); break
                    except BlockingIOError:
                        time.sleep(.2)
                self._local.lock_fds.append(gpu.fileno())
                run([python, '-m', 'aiforstudy.core.video_recognition_worker', '--mode', 'asr', '--input', d / 'audio.wav', '--output', d / 'asr.json', '--model', model, '--chunk-seconds', '20', '--overlap-seconds', '2', '--cancel-file', d / 'cancel.request'], 'asr.log', 14400)
            finally:
                if gpu.fileno() in self._local.lock_fds:
                    self._local.lock_fds.remove(gpu.fileno())
                gpu.close()
            data = _read(d / 'asr.json')
            if data.get('status') not in {'completed', 'completed_with_warnings'} or not data.get('segments'):
                raise ValueError('ASR did not complete all audio windows')
            return data, ['asr.json']
        transcript = self._stage(job_id, 'asr', token, asr)
        def ocr():
            python = self.config['ocr_python'] or self.config['asr_python']
            if not python:
                raise ValueError('Configure AIFORSTUDY_VIDEO_OCR_PYTHON')
            manifest = {'frames': [{**f, 'path': str(d / f['path'])} for f in frames]}
            write_json_atomic(d / 'ocr-input.json', manifest)
            run([python, '-m', 'aiforstudy.core.video_recognition_worker', '--mode', 'ocr', '--input', d / 'ocr-input.json', '--output', d / 'ocr.json', '--cancel-file', d / 'cancel.request'], 'ocr.log')
            data = _read(d / 'ocr.json')
            if data.get('status') not in {'completed', 'completed_with_warnings'} or {f['id'] for f in data['frames']} != {f['id'] for f in frames}:
                raise ValueError('OCR frames do not match sampled evidence')
            return data, ['ocr.json']
        recognized = self._stage(job_id, 'ocr', token, ocr)
        by_id = {f['id']: f for f in recognized['frames']}
        frames = [{**f, 'text': by_id[f['id']].get('text', ''), 'ocr_quality_warnings': by_id[f['id']].get('quality_warnings', []), 'ocr_observations': by_id[f['id']].get('observations', []), 'ocr_raw_output': by_id[f['id']].get('raw_output', {})} for f in frames]
        models = VideoModelSession(self, job_id, token)
        frames = self._stage(job_id, 'vision', token, lambda: models.vision(frames, transcript, duration))
        lesson = self._stage(job_id, 'lesson', token, lambda: models.lesson(frames, transcript, duration))
        review = self._stage(job_id, 'review', token, lambda: models.review(lesson, frames, transcript, duration))
        def export():
            result = {'schema_version': VERSION, 'job_id': job_id, 'title': row['title'], 'course_id': row['course_id'], 'duration': duration,
                'source': {'sha256': row['source_sha256'], 'path': source.name,
                    'playback': {'video_src': 'playback.mp4', 'audio': {'src': 'speech.mp3', 'data_base64': base64.b64encode((d / 'speech.mp3').read_bytes()).decode(), 'mime': 'audio/mpeg'}},
                    'timing_note': 'ASR为20秒重叠窗口；帧sampled_time为请求采样时间，非精确PTS；MP3编码可能有毫秒级偏移。'},
                'sections': lesson['sections'], 'transcript': _safe_public(transcript), 'frames': frames,
                'formulas': lesson.get('formulas', []), 'uncertainties': lesson.get('uncertainties', []),
                'coverage': {'audio': transcript.get('coverage', {}), 'visual': {'sampled_frames': len(frames), 'max_frames': self.config['max_frames'],
                    'strategy': 'uniform timestamps plus scene-change candidates, bounded; not every frame', 'requested_interval_seconds': self.config['frame_interval'],
                    'sampled_times': [f['sampled_time'] for f in frames]}, 'semantic_completeness_verified': False},
                'provenance': {'pipeline_version': VERSION, 'run_identity': row['identity'], 'dependency_digest': _digest(row['config'].get('dependencies', {})), 'asr': _safe_public(transcript.get('identity', {})), 'ocr': _safe_public(recognized.get('identity', {})), 'models': models.identities(), 'originals_preserved': True},
                'review': review, 'quality_state': 'candidate', 'production_accepted': False}
            write_json_atomic(d / 'result.json', result)
            lines = ['# ' + row['title'], '', '> 自动解析候选稿。画面为有上限采样；原始转写保留，数学尚需核对。', '']
            for section in lesson['sections']:
                seconds = int(section['start'])
                lines += [f"## {section['title']}（{seconds // 60:02}:{seconds % 60:02}）", '', section['markdown'], '',
                    '[回看原片](' + source.name + '#t=' + str(seconds) + ') · 来源：' + ', '.join(section['evidence_ids']), '']
            if lesson.get('uncertainties'):
                lines += ['## 尚待核对', ''] + ['- ' + (x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)) for x in lesson['uncertainties']]
            (d / 'lesson.md').write_text('\n'.join(lines), encoding='utf-8')
            write_json_atomic(d / 'transcript.json', _safe_public(transcript))
            write_json_atomic(d / 'frames.json', frames)
            self._register_artifacts(job_id, ['result.json', 'lesson.md', 'transcript.json', 'frames.json', 'review.json'])
            return {}, ['result.json', 'lesson.md', 'transcript.json', 'frames.json']
        self._stage(job_id, 'export', token, export)

    def _extract_frames(self, job_id, source, duration, token):
        d = self._jobdir(job_id); (d / 'frames').mkdir(exist_ok=True)
        maximum = self.config['max_frames']; regular_cap = max(2, maximum * 3 // 4)
        interval = max(self.config['frame_interval'], duration / (regular_cap - 1))
        regular = [min(i * interval, max(0, duration - .1)) for i in range(math.ceil(duration / interval))]
        regular.append(max(0, duration - .1))
        # Full-video downscaled scene scan records timestamps, never unlimited images.
        scene_log = d / 'scene.log'
        self._process(['ffmpeg', '-nostdin', '-hide_banner', '-i', source, '-an', '-vf',
            f"scale=320:-2,select='gt(scene,{self.config['scene_threshold']})',showinfo", '-fps_mode', 'vfr', '-f', 'null', '-'], scene_log, token)
        candidates = []
        with scene_log.open(errors='replace') as stream:
            for line in stream:
                match = re.search(r'pts_time:([0-9.]+)', line)
                if match:
                    t = float(match.group(1))
                    if 0 <= t < duration and all(abs(t - v) >= 3 for v in regular) and (not candidates or t - candidates[-1] >= 3):
                        candidates.append(t)
        room = max(0, maximum - len(regular))
        if len(candidates) > room and room:
            candidates = [candidates[int(i * len(candidates) / room)] for i in range(room)]
        elif not room:
            candidates = []
        times = sorted(set(regular + candidates))[:maximum]
        frames = []
        for index, t in enumerate(times):
            token.checkpoint(); frame_id = f'frame-{index + 1:04d}'; path = f'frames/{frame_id}.jpg'
            self._process(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', source, '-frames:v', '1', '-vf', 'scale=1600:-2', '-q:v', '2', d / path], d / 'extract-frame.log', token, 60)
            if not (d / path).is_file():
                raise ValueError('Frame extraction produced no image')
            frames.append({'id': frame_id, 'path': path, 'start': t, 'end': min(duration, times[index + 1] if index + 1 < len(times) else duration),
                           'sampled_time': t, 'sampling': 'scene_change' if t in candidates else 'periodic', 'sha256': _sha(d / path)})
            self._progress(job_id, 'frames', (index + 1) / len(times))
        write_json_atomic(d / 'frames-manifest.json', {'frames': frames})
        self._register_artifacts(job_id, [f['path'] for f in frames])
        return frames, ['frames-manifest.json'] + [f['path'] for f in frames]
