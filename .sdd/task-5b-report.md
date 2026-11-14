# Task 5b — automatic ordinary narration and two explicit speech revisions

## Automatic production path

Default `config/narration.json` AND `configured_backend()` now choose
`local-qwen`. `local-cache` remains strictly read-only. Automatic cache misses
invoke the package-local `aiforstudy.blocks.media.local_speech_worker` using an
explicit MLX interpreter and explicit package PYTHONPATH. The old tools entry is
only a wrapper, so installed packages need no checkout-only tools directory.

Environment requirements are `AIFORSTUDY_TTS_MODEL_DIR`,
`AIFORSTUDY_TTS_MODEL_MANIFEST`, `AIFORSTUDY_TTS_PYTHON`, and
`AIFORSTUDY_TTS_CACHE_DIR`. Explicit same-name lowercase configuration keys are
also supported. No personal path is hardcoded in production. Voice, weights,
revision, seed, instruction, token budget and native runtime identity are unchanged
from the verified 57-case run, permitting exact cache reuse. The worker rehashes
model files before inference and uses offline loading without remote code.
User/model narration text is serialized as data, never executable arguments or
model configuration. Edge remains explicitly selectable, never a fallback.

Completed cache hits are identity/hash/PCM validated before use and do not wait
for the GPU. Misses acquire a common cross-process flock, then recheck before
starting one model worker. A configurable bounded wait and process timeout apply;
subprocess.run kills/reaps a timed-out worker, and finally releases the lock.
The default global lock is ~/.cache/aiforstudy/tts-gpu.lock; all processes sharing
a GPU must share it. Missing dependencies, invalid completed cache, worker errors
and timeouts fail rather than synthesize through another provider. A result JSON
is published only after both WAV writes; partial attempts cannot become cache hits.

## Real previously unseen sentence

Actual configured_backend(config/narration.json) -> prepare_step_audio execution:
“现在检查一个全新的例子。取半径等于零点七的圆，先观察边界，再讨论圆心附近的函数值。”
An assertion verified its cache receipt was absent immediately before this call.
It automatically produced real Qwen WAV and returned measured PCM metadata;
no hand-filled cache or fixture audio was used. Evidence:
`tts-trials/auto-new-sentence/evidence.json`, its step-001.wav,
`logs/auto-new-sentence.log`, and the hash-keyed raw/PCM cache entry.
Measured PCM: 203520 samples at 24000 Hz, duration 8.48 seconds; native
model generation 2.868296 seconds. Measured end-to-end wall time was
5.969851 seconds.

The first actual attempt exposed a real integration bug: resolving the Python
venv entrypoint symlink selected the base interpreter and lost MLX dependencies.
Fixed by preserving its absolute symlink path, added a regression, and reran the
actual uncached request successfully. No package installation or fallback occurred.

## Two explicit revision records and preserved versions

Only these authored strings changed, with the mathematics and formulas unchanged:
- CH02-S05-SS07-S1: “指数阿尔法取三时” -> “指数阿尔法等于三的时候”.
- CH08-S04-SS03-S5: “半径零点九时” -> “当半径等于零点九的时候”.

Full before/after strings and reasons are in
`tts-trials/scripts/narration-disambiguation-v2.json`. Original corpus is retained;
active expected corpus is `scripts/narration-corpus-57-v2.json`. Revoice and
verification tools require explicit --overrides, matching complete before text
and IDs against original D. Expected text checks remain enabled. Only exact
matching display prose is replaced; formula display is preserved. No manuscript,
coverage or other authoring files changed. Trial14 remains untouched.

Both revised steps were actually generated via the automatic backend. The active
57-entry `wholebook-qwen-index.json` points to the two new outputs and 55 original
cache entries; the original index is retained as `wholebook-qwen-index-v1.json`.
All old raw/PCM entries remain. Complete previous stage is retained at
`revoiced-delivery-stage-before-disambiguation`; current stage is rebuilt atomically
per the established pipeline. Exactly two animation MP4 hashes changed:
CH02-S05-SS07 and CH08-S04-SS03; the other ten are unchanged. Exactly two audio
hashes changed; the other 55 are unchanged. Evidence:
`tts-trials/disambiguation-v2/change-verification.json`.
New PCM total is 671.04 seconds, movie total 708.533328 seconds. New per-step
WAVs are also at `disambiguation-v2/<case>/step-001.wav` for the parent's ASR audit.

## Validation

Meaningful test-first cache-miss dispatch tests initially failed on absent backend
(`.sdd/task-5b-red.log`), then passed. Coverage includes automatic protocol dispatch,
cache hits, concurrent same-text deduplication, different-text model serialization,
model revision cache isolation, bad cache rejection, worker failure/timeout,
venv interpreter preservation, and exact explicit script overrides. The protocol
fixture tests are scheduler tests, not claimed as actual model runs.
114 narration/provider/revoice tests passed in 3.41s (`.sdd/task-5b-green.log`).
The real new-sentence inference above separately proves model execution.

Actual final 12/57 delivery verification passed all resource hashes, byte counts,
exact PCM placements, expected revised scripts, display LaTeX, VTT clocks and
171 decoded seek/motion-end/hold-end comparisons. Each changed movie was fully
decoded and its video PTS coverage checked by the existing compositor. Saved
verification is `revoiced-delivery-stage/verification.json`.

Additional media_code_runtime verification completed with the configured Manim,
Edge, package import paths and all four local TTS environment variables. With the
complete environment, 12 passed and four assertions exposed old test assumptions
(`.sdd/task-5b-media-runtime-configured.log`): socket creation versus real network
connection denial, two explicit Linux-only Landlock requests on macOS, and fixed
silent-animation times despite now-real Qwen speech. Parent authorized narrow
test-only portability corrections. The socket test now attempts actual connect
to TEST-NET and requires PermissionError. Linux-only requests on macOS must be
explicitly blocked without resources/fallback; Linux success/isolation checks
remain unchanged. The timing test retains real Qwen, validates WAV sample counts,
complete audio coverage, original motion minima, current subtitle clock and all
original decoded keyframe pixel checks. No production sandbox policy changed.

The corrected 16-test suite produced 15 passes plus a new assertion-fixture error:
reading a path from a deliberately path-redacted receipt. That fixture was fixed
to read the host's fixed step-001.wav naming and verify sample_count/sample_rate.
Only that changed test was rerun: 1 passed in 5.42s. Thus every one of the 16 tests
has now passed, including real seatbelt connect denial and actual Qwen narration.
Exact suite/focused logs are `.sdd/task-5b-media-runtime-green.log` and
`.sdd/task-5b-media-runtime-final.log`; preliminary failures are retained as evidence.

No human listening/naturalness approval is asserted. The parent audits the two
new clips with ASR separately; ASR is not a pronunciation or semantic guarantee.

## Independent review fix round 1 — outer cache and cancellation

Read `.superpowers/sdd/2026-11-15-teaching-upgrade/task-5b-review.md`.
Confirmed P1: literal configuration hashes left environment-selected manifest and
local implementation edits outside the resource reuse boundary. Animation-only
`CODE_NARRATION_COMPONENTS` now contains narration, provider, local backend and
packaged worker modules. Both resource-generation dependencies and compiler/runtime
identity bind these modules and the resolved effective backend identity. Local
identity validates current model-file SHA-256 against the manifest and includes
manifest hash, model/voice/settings and actual Python + mlx-audio/mlx/numpy/
soundfile/transformers/tokenizers/safetensors metadata from the configured MLX
interpreter. No model loads during identity inspection. File digests use the
existing stat-keyed fingerprint cache. Drawing and review closures remain separate;
Task 6's precise exam-reader dependency entry was not changed.

Confirmed P2: code_runtime now passes its cancellation object through
prepare_step_audio to the automatic backend. Cancellation is checked before
configuration, before every step, while waiting for the cross-process GPU lock,
and every 50 ms while communicating with an active worker. A cancelled or timed-out
active process group is killed, and the direct worker is reaped with communicate
before returning through the lock-release finally block. Cancelled is represented
as the existing cancelled runtime status; no later step starts. Cancellation never
publishes partial PCM cache receipts or switches providers. Completed cache hits
remain CPU-only. The introductory Edge-default sentence was corrected.

Exact RED command: `PYTHONPATH=src:tests <project-root>/.venv-linux/bin/python -m pytest tests/test_media_code_dependencies.py tests/test_auto_local_narration.py -k 'local_effective or cancel_' -q`.
Result: 3 failures, 35 deselected in 0.27s; `.sdd/task-5b-fix1-red.log`.

GREEN command: `PYTHONPATH=src:tests <project-root>/.venv-linux/bin/python -m pytest tests/test_auto_local_narration.py tests/test_local_narration.py tests/test_narration.py tests/test_narration_providers.py tests/test_natural_narration.py tests/test_revoice_textbook_lessons.py tests/test_media_code_dependencies.py tests/test_media_dependencies_v4.py -q`.
Result: 158 passed, 1 initially skipped in 5.19s; `.sdd/task-5b-fix1-green.log`.
The browser-only skipped test was then run with the actual Edge executable:
`tests/test_media_dependencies_v4.py::test_real_browser_lazy_animation_anchor_is_mounted_when_detail_opens`; 1 passed in 1.93s,
`.sdd/task-5b-fix1-browser.log`. No skipped test is counted as a pass.

Additional focused coverage added after that suite:
- Actual figures-stage outer reuse: repeated identical request generated once;
  changing the manifest through its environment reference generated/rendered again.
  Local backend/worker source mutations alter animation generation only. 1 passed
  in 0.27s, `.sdd/task-5b-fix1-outer-cache.log`.
- Actual CPU protocol process through prepare_step_audio and the automatic backend:
  cancel first active worker, assert PID gone, assert lock immediately acquirable,
  assert only one request and no completed receipt; 1 passed in 0.12s,
  `.sdd/task-5b-fix1-cancel-integration.log`. Separate tests cover queue cancellation
  while another real process owns the lock, active direct-process cleanup, and
  cancellation between steps. These are real process tests, not GPU inference.
- Actual configured Manim/Qwen media integration with measured PCM and decoded
  keyframes: focused runtime test passed in 7.24s,
  `.sdd/task-5b-fix1-runtime.log`.

Real model files and native runtime identity were inspected successfully; evidence
is `tts-trials/auto-new-sentence/effective-dependency-identity.json`. All 60 current
stage resources were rehashed against byte counts and manifest SHA-256 and passed.
No content, script, voice parameters or model inputs changed, so the 12/57
production artifacts were preserved without resynthesis. Future ordinary animation
cache identities intentionally invalidate older provenance boundaries. Existing
recorded generation receipts were not rewritten to pretend a historical run used
new code. Final source packages must include this fix.
