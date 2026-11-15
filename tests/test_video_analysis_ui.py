"""HTTP boundaries for the video UI, with model work replaced by a service double."""
import io
import json
import threading
import urllib.error
import urllib.request

import pytest

from aiforstudy.core.workspace import Workspace
from aiforstudy.ui.server import ControlServer


class VideoService:
    def __init__(self, root):
        self.root = root
        self.job = {"job_id": "video-1", "state": "queued", "stage": "probe", "progress": 0}

    def capabilities(self):
        return {"available": True, "sample_available": True, "max_upload_bytes": 32}

    def register_upload(self, stream, length, filename):
        assert not isinstance(stream, (bytes, io.BytesIO)), "HTTP upload must be streamed"
        self.root.joinpath("received.mp4").write_bytes(stream.read(length))
        return {"id": "source-1", "filename": filename, "bytes": length}

    def sample(self):
        return {"id": "source-sample", "filename": "第一讲.mp4", "bytes": 12}

    def submit(self, body):
        assert body["source_id"] == "source-1"
        return self.job

    def list_jobs(self):
        return [self.job]

    def get(self, job_id):
        if job_id != "video-1":
            raise KeyError("missing job")
        return self.job

    def cancel(self, job_id):
        self.job["state"] = "cancelled"
        return self.get(job_id)

    def resume(self, job_id):
        self.job["state"] = "queued"
        return self.get(job_id)

    def artifact(self, job_id, relative):
        return self.root / "received.mp4" if job_id == "video-1" and relative == "source.mp4" else None


@pytest.fixture
def client(tmp_path):
    control = ControlServer(Workspace(root=tmp_path))
    control._video_service = VideoService(tmp_path)
    httpd = control.make_server()
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    def request(path, body=None, headers=None, method=None, authorized=True):
        head = {"Origin": control.origin}
        if authorized:
            head["X-Aifs-Token"] = control.token
        head.update(headers or {})
        if isinstance(body, dict):
            body = json.dumps(body).encode()
            head["Content-Type"] = "application/json"
        req = urllib.request.Request(control.origin + path, body, head, method=method)
        try:
            response = urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, response.headers, response.read()

    yield request, tmp_path
    httpd.shutdown()
    httpd.server_close()


def test_entry_and_assets_are_served(client):
    request, _ = client
    assert b'href="/video"' in request("/")[2]
    for path in ("/video", "/video-result.html", "/video.js", "/video-analysis/result.js",
                 "/video-assets/audible-audio.js", "/video-assets/katex.min.js", "/video-assets/katex.min.css"):
        assert request(path)[0] == 200, path


def test_upload_stream_and_submission(client):
    request, root = client
    status, _, data = request("/api/videos/upload", b"video-content", {"X-Video-Filename": "lesson.mp4"})
    assert status == 201
    assert json.loads(data)["id"] == "source-1"
    assert (root / "received.mp4").read_bytes() == b"video-content"
    assert request("/api/videos", {"source_id": "source-1"})[0] == 202
    assert json.loads(request("/api/videos")[2])["jobs"][0]["state"] == "queued"
    assert json.loads(request("/api/videos/video-1/cancel", {})[2])["state"] == "cancelled"
    assert json.loads(request("/api/videos/video-1/resume", {})[2])["state"] == "queued"
    assert request("/api/videos/missing")[0] == 404


@pytest.mark.parametrize("headers,authorized", [({}, False), ({"Origin": "https://foreign.example"}, True)])
def test_write_gate_covers_upload_and_sample(client, headers, authorized):
    request, root = client
    assert request("/api/videos/upload", b"video", {"X-Video-Filename": "x.mp4", **headers}, authorized=authorized)[0] == 400
    assert not (root / "received.mp4").exists()
    assert request("/api/videos/sample", {}, headers, authorized=authorized)[0] == 400


@pytest.mark.parametrize("filename,body", [("../evil.mp4", b"video"), ("%2fetc%2fvideo.mp4", b"video"), ("x.html", b"video"), ("x.mp4", b""), ("x.mp4", b"x" * 33)])
def test_upload_rejects_unsafe_or_invalid_input(client, filename, body):
    request, root = client
    assert request("/api/videos/upload", body, {"X-Video-Filename": filename})[0] == 400
    assert not (root / "received.mp4").exists()


@pytest.mark.parametrize("payload", [{}, {"source_path": "/etc/passwd"}, {"source_id": "source-1", "source_path": "/etc/passwd"}])
def test_submit_requires_registered_source_and_no_paths(client, payload):
    assert client[0]("/api/videos", payload)[0] == 400


def test_artifact_is_readonly_range_and_head(client):
    request, root = client
    (root / "received.mp4").write_bytes(b"0123456789")
    status, headers, data = request("/api/videos/video-1/artifacts/source.mp4", headers={"Range": "bytes=2-5"})
    assert (status, data, headers["Content-Range"]) == (206, b"2345", "bytes 2-5/10")
    assert "sandbox allow-scripts" in headers["Content-Security-Policy"]
    assert request("/api/videos/video-1/artifacts/source.mp4", method="HEAD")[2] == b""
    assert request("/api/videos/video-1/artifacts/source.mp4", {})[0] == 405
    assert request("/api/videos/video-1/artifacts/../outside")[0] == 404
