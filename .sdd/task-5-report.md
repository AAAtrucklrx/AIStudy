# Task 5 — actual local narration and complete revoice

Implemented an offline Qwen3-TTS CustomVoice worker and explicit `local-cache`
backend in the established narration factory. No Edge, macOS or network fallback.
The worker verifies all model files against the pinned download manifest, uses
Serena (model-supplied voice, no cloning), and retains raw float WAV plus PCM16.
Cache identity includes model repository/revision/all file SHA-256, exact text,
voice/language/instruction/seed/token budget/runtime/streaming settings. Read-side
identity, audio hash, bounded mono PCM and exact script are verified before use.

## Actual run and selection

Evidence root: `research/2026-11-15/tts-trials/` in the shared project root.
`wholebook-qwen-index.json` indexes all 57 actual outputs and raw/PCM hashes;
`wholebook-qwen-config.json` is the actual portable-schema, runtime-path config;
`logs/wholebook-qwen.log` records execution. Model:
`mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16`, revision
`52f4770fd9726457eae3d3b6aa92047a25a10776`, mlx-audio 0.6.5,
Serena, seed 20261115, nonstreaming, Chinese, 2304 token budget. All 57 finished
below budget. Total PCM 669.60 seconds; native generation 218.34 seconds; maximum
float amplitude 0.65630. No loudness change, time stretching, pitch change or
clipping was necessary. Model weights are excluded from source and delivery.

Parent-selected Qwen after actual same-script 14-case Qwen/MOSS comparison, plus
14 original Edge clips. Both candidates retained important numeric/negative
phrases in one independent ASR pass; ASR disagreement and homophones prevent
using character-error scores as semantic truth. Qwen had fewer long low-energy
intervals in this experiment, lower resident memory, faster generation and a
stable built-in voice. MOSS used only its own freshly synthesized no-reference
anchor; no teacher/Edge voice cloning. Fixed dBFS gaps are not VAD, and MOSS was
quieter. This is a technical selection, not proof of superior naturalness.
Human blind listening has not been completed. Parent retains same-script audio
and two independent ASR results, and is auditing the final 57 separately.

## Timing and artifacts

Independent output: `research/2026-11-15/revoiced-delivery-stage/`, containing
`book/assets/narrated/`, 12 rebuilt MP4/WAV/VTT/LaTeX transcripts, per-animation
receipts, `neural-media.json`, and `verification.json`. Original delivery D is
untouched. Final builder may use this stage as `--previous-delivery` while using
D/book as content source. All 12 animation and 57 step IDs remain unchanged;
frozen spoken scripts equal the corpus exactly. Display LaTeX remains separate.

Second retiming always uses the CURRENT input MP4's step.start/end. Older raw
source_start/end are retained only in `prior_clock_lineage`. For 10 animations,
the prior receipt from the textbook-continuity delivery has an MP4 output hash
matching current D, identical steps, and the explicit original-motion-then-hold
contract. Only its original interval LENGTH is applied at the current start;
old source starts are never positions in the current file. Proven old holds are
removed, then complete new PCM plus 0.25 seconds (rounded to whole frames) is
accommodated. Each step records receipt SHA, current video SHA, current input
window, current motion window and the derivation. Narration version is
`host-narration-1.4-proven-hold`, invalidating earlier movie caches.

Two current files (CH08-S04-SS01 and CH03-S02) do not match those prior receipt
MP4 hashes. Their full current intervals are retained with explicit reasons,
as authorized; their old holds cannot be inferred safely from those receipts.
CH08-S04-SS01 occupies 44.233333 seconds; CH03-S02 occupies 127.233332
seconds (combined 171.466665 seconds). Total new movie duration is 707.099994 seconds.

## Verification

- Meaningful tests were added first for cache identity, invalid/missing cache and
  current-clock lineage; red failures observed, then green.
- Hash-matched hold evidence test rejects changed input movies. Real FFmpeg test
  covers both short/long new PCM, current second-step start 3 versus raw start 1,
  preserved final motion frame, final hold and exact 33-frame output.
- 104 narration/provider/revoice regression tests pass.
- Every rebuilt movie is decoded on both tracks and checked against all video
  packet PTS/end durations by the established compositor.
- Whole-book verification checks every shipped resource SHA/size, original input
  SHA, receipt output hashes, exact PCM bytes at all 57 offsets, sample counts,
  frozen scripts, unchanged display LaTeX, VTT cue counts/clocks and text clocks.
- Actual decode/seek comparison checks current input action position, last motion
  frame and final output hold for all 57 steps. Results are in verification.json.

Technical validation does not certify naturalness, pronunciation, mathematical
meaning or pedagogical quality. No synthetic `spoken_review` approval was added.
