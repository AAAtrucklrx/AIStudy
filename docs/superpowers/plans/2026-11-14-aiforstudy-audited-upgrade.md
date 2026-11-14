# AIforStudy audited upgrade implementation plan

> For agentic workers: use isolated file ownership and targeted review. User explicitly requested audit followed by implementation and authorized parallel agents. This directory is not a Git checkout; no commits or worktree creation are required.

Goal: connect the verified course materials to the real reader/build entry, add usable premium narration integration and finer timing records, and restore a genuinely runnable local generation environment.

Architecture: preserve the graph-8 production stages, GeneratedMediaCodeV1/ApprovedMathContext, current balanced review behavior and the specialized wholebook build. Extend existing entry points. Research artifacts provide input examples and evidence, not release status.

Tech stack: Python 3.12, native JS/CSS/KaTeX/Three.js, Manim, existing narration and media manifest APIs.

Spec: user requests in this chat plus research/2026-11-14/baseline-production.txt, baseline-delivery.txt, baseline-media-audio.txt and existing research reports. The three baseline files are one directory above this source checkout.

## Verified baseline
- Current static book: 76 units, 379+39 coverage items, 39 visual plans, 12 narrated videos, 57 steps; data SHA e99bb100aeda3ebcb49f4f9223a6afceaf9605cae26c1f145e0d8c07a24273b3.
- Wholebook source manifests and specialist build compose existing revisions. The normal run does not consume these manifests automatically.
- Graph8 contains source_format. New drawing and animation generation both use Manim code generation. Old DSL is compatibility code.
- Current review mode balanced. Rendered body success, review results and release_ready have distinct meanings.
- HTTP/Command TTS and Edge narration are already called by current runtime. Edge failures do not invoke Say automatically.
- Local capability check currently reports no animation backend. Configured model secret file and known service-key environment variables are absent.
- Current research imports 39 exam PDFs/51 sessions and one textbook/9 chapters/129 top-level exercise numbers. Actual assigned subset is unknown.

## Task A — Production course-material access
Own course library source/reader/build integration and its tests. Import the two verified research manifests through an explicit command, preserve source hashes/roles/course labels and copy appropriate assets to rebuilt book output. Add a useful entry from the real textbook reader. Use the existing source-material mechanism where it fits. Support PDF page links, course/year filtering, partial textbook answers and answer-only exam files. Keep unknown dates and assignments unknown.
Acceptance: all 40 source PDF hashes/pages and 133 existing locators validate; the rebuilt real book exposes the library; links work under its own server root; course/type filters are correct; no dependence on the research HTTP service. Invalid manifests fail clearly without overwriting valid output.

## Task B — Narration provider and timing upgrade
Own narration Python/runtime integration and narrowly related tests. Add premium provider adapters through existing configured_backend, using documented MiniMax and Eleven response formats and external key references. Preserve existing backend callers and legacy media. Keep display LaTeX, approved spoken text and directing notes distinct. Normalize time units explicitly and persist only usable timing records; uncertain or absent anchors remain explicit. Include provider/model/voice/script/dictionary identity in relevant cache keys. Never log credentials.
Acceptance: provider payload/response contract tests, malformed/error responses, binary audio validation, seconds/milliseconds handling and old caller compatibility. New-provider voice quality remains unverified until an authenticated live synthesis and listening pass. No silent provider fallback or fabricated word timestamps.

## Task C — macOS rendering readiness
Own capability configuration/probes and worker/bootstrap platform support plus targeted tests. First locate installed usable dependencies. Add a supported macOS path using properly isolated generated-code execution, or a verified existing compatible Linux runtime. Install only necessary recognized dependencies if needed. Keep Linux paths supported. Do not disable isolation, treat missing optional engines as mandatory, or rewrite historical run states.
Acceptance: current-host capability report reflects reality; a controlled small scene renders with Chinese text, a formula and audio/video metadata; isolation probes verify prohibited file/network actions fail. If a genuine platform/API access dependency remains, report it precisely and keep unrelated reader/material work deliverable.

## Root integration and verification
Update stale README facts only after corresponding code is confirmed. Review each change and targeted tests. Build the current wholebook from source into a new dated output, confirm lesson/knowledge/media counts, verify links and player behavior, preserve the previous delivery. Test offline behavior as applicable. Repackage source and reading output after checks. Report implemented functionality separately from unavailable live model/audio-quality validation. Do not mark the historical partial run as a new successful generation.
