# Task7d — structured example disclosure ownership

## Result

Implemented generic Reader-only ownership repair. No schema, compiler, prompt, author JSON, source, audio, or media-generation changes. Four real generated examples now each have one effective example disclosure. Independent body worked_example, proof disclosures, pitfall controls and animation settings remain separate.

## Confirmed cause

Actual Edge DOM before repair: each example E-01..E-04 had `details.reader-example-disclosure > details.reader-group.reader-structured-example`, plus statement and step fields each containing `details.reader-teaching-disclosure[data-teaching-role=worked_example]`. Therefore both the legacy layout composition and explicit role field wrapping contributed. Removing roles still reproduced the outer/group duplicate.

`foldBodyExamples` now reuses a topic's sole structured example group as the example disclosure, preserving group anchor, identity and source nodes. It does not touch collection topics or alternatives with body steps. `render-core` passes the existing examples group role to Markdown; matching worked_example regions use a div retaining `data-teaching-role`, with the same token and media mount order. Other roles continue to create details. No global details unwrapping or click-to-open-all.

## RED / GREEN

Real content fixture copied exactly from `ROOT/research/2026-11-15/live-generation/ss02-roles/authored.json` content; no author bytes changed. Production generated record uses balanced normalization (source_example kinds, empty extra fields), so it is not strict-full V4. Initial strict-mode test failed schema validation and was corrected to the actual balanced production mode before behavioral RED. Strict legality is independently tested with `LessonContentV4.model_validate` on a small complete fixture.

- RED: `PY -m pytest -q tests/test_structured_example_disclosure.py --tb=short`: 2 failed. Both explicit roles and omitted roles failed `one click reveals field /examples/0/statement`, returning a closed HTMLDetailsElement.
- GREEN: same file after repair and strict-V4 addition: 3 passed. Real balanced content with/without roles, plus strict V4 content → project_reader → compile_teaching_presentation → production layout → actual render-core/Markdown → layout enhancement. Asserts single click reveals statements/approach/steps/basis, defaults closed, retained source nodes, preserved metadata, idempotence, a test-only mount resolved from production syntax blocks is closed initially and available after expansion, independent body worked_example/proof remain closed and body main remains visible.
- `PY -m pytest -q tests/test_structured_example_disclosure.py tests/test_teaching_projection.py --tb=short`: 15 passed in final run.
- `node --test tests/ui/reader_comparison_layout.test.cjs tests/ui/reader_disclosures.test.cjs tests/ui/teaching_projection.test.cjs`: 44 passed, 0 skipped; includes explicit-main protection, stale binding rejection, collections and alternative ownership.
- `node --test tests/ui/reader_book_interactions.test.cjs tests/ui/reader_disclosures.browser.test.cjs tests/ui/reader_media_lifecycle.test.cjs tests/ui/reader_markdown.test.cjs tests/ui/study_visuals.test.cjs`: 58 passed, 0 skipped, including actual Edge native visibility and media lifecycle tests.

PY is ROOT/.venv-linux/bin/python. W is ROOT/work/2026-11-15/AIforStudy.

## Actual generated Reader / Edge

Coordinated with verify_live_generation owner; copied existing reader to independent `ROOT/research/2026-11-15/live-generation/ss02-roles-disclosure-preview/reader`, then replaced only reader-layout.js, reader-markdown.js, render-core.js. No paid calls, no overwrite of owner's output, no changes to original model/raw/roles/data/media. The copy includes the owner's current actual generated image and animation; this validation does not claim independent media generation/review.

Evidence in independent preview directory:
- `browser-evidence.json`: 4 groups default `open=false`, exactly 1 closed ancestor each, 0 nested same-role details; after one native summary click per group, statement/step/basis paragraph hidden lists all empty. All 8 pitfall controls and animation-settings remain closed. E-04 actual media anchor MR-25297dc71caf161ddf68 visible after expansion. pageerrors=[], mathErrors=0.
- `reader-collapsed.png`, `reader-expanded-once.png`: actual Edge screenshots, expanded screenshot visually inspected; all four complete examples shown and example 5 animation beside its calculation. Original owner's before screenshots remain untouched in ss02-roles.
- Browser executable `/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge`; Playwright from W/node_modules/playwright. Native clicks used, no programmatic open-all.

## Remaining boundary

The old numbered body-example alternative expansion behavior is unchanged and tested. This task fixes same-owner standalone structured topics and same-owner explicit role regions; it does not flatten distinct example collections or optional supports. Actual media acceptance remains with live-generation owner.
