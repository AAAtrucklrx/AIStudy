# Task 2 fix round 5 — optional theorem proof consistency

Base: `4a07624`. Scoped fix for the remaining Important finding in `task-2-rereview-4.md`.

## Changes

- `src/aiforstudy/blocks/content/prompts/author.md`: formal proofs are optional; actually supplied theorem proofs still require every derivation step and justification. Mainline methods, conditions and reasons remain required. The first theorem explainable stores full conditions, conclusion, meaning and use; any supplied full proof belongs to that object and defaults to collapsed presentation.
- `src/aiforstudy/blocks/content/prompts/repair.md`: the same conditional proof-completeness rule replaces the unconditional theorem-proof requirement.
- `tests/test_reader_role_prompt_protocol.py`: nine real `build_content_messages` combinations cover author/repair/reviewer in balanced/json_only/full. They detect the three reviewed mandatory-proof formulations, retain the optional-proof/mainline requirements, and check full/json_only author/repair supplied-proof completeness. Existing transmitted-example schema validation, actual three-role presentation compilation and implicit-role omission compatibility tests remain intact.

No schema/compiler/renderer/review mode/audit gate/math validation changes. No paid calls. No edits to `tools/verify_live_unit.py` or `docs/live-generation.md`.

## TDD and validation

All commands ran from `/Users/huang/Documents/ChatGPT/ai for study项目的改进/work/2026-11-15/AIforStudy`.

RED, before production changes:

`PYTHONPATH=src:.:tests '/Users/huang/Documents/ChatGPT/ai for study项目的改进/.venv-linux/bin/python' -m pytest tests/test_reader_role_prompt_protocol.py -q`

Result: **4 failed, 17 passed in 0.74s**. Failing cases were `test_production_messages_do_not_require_optional_theorem_proofs[author-json_only]`, `[author-full]`, `[repair-json_only]`, `[repair-full]`, each because the real system message still contained its unconditional proof instruction.

GREEN, content-focused regression:

`PYTHONPATH=src:.:tests '/Users/huang/Documents/ChatGPT/ai for study项目的改进/.venv-linux/bin/python' -m pytest tests/test_reader_role_prompt_protocol.py tests/test_teaching_projection.py tests/test_balanced_teaching_guidance.py tests/test_reader_support_guidance.py tests/test_teaching_narrative_prompt_contract.py tests/test_content_prompt_v4.py tests/test_review_mode.py -q`

Result: **72 passed in 2.14s**, including all 21 role-protocol tests.

Broader targeted check also included `tests/contracts/test_prompt_asset_identity.py` in the same command:

`PYTHONPATH=src:.:tests '/Users/huang/Documents/ChatGPT/ai for study项目的改进/.venv-linux/bin/python' -m pytest tests/test_reader_role_prompt_protocol.py tests/test_teaching_projection.py tests/test_balanced_teaching_guidance.py tests/test_reader_support_guidance.py tests/test_teaching_narrative_prompt_contract.py tests/test_content_prompt_v4.py tests/test_review_mode.py tests/contracts/test_prompt_asset_identity.py -q`

Result: **3 failed, 79 passed in 2.39s**. The three media-side failures were reported to the parent agent, not changed in this task. The parent reports the same three test names already failed in the initial unmodified-source `baseline-python.log`; I did not independently reread that log and do not infer identical root causes from matching names:

- `tests/contracts/test_prompt_asset_identity.py::test_code_examples_in_final_messages_pass_real_code_validator[drawing]`: generated code request ID differs from synthetic frozen request `EXAMPLE-ONLY`.
- `tests/contracts/test_prompt_asset_identity.py::test_code_examples_in_final_messages_pass_real_code_validator[animation]`: same request-ID mismatch.
- `tests/contracts/test_prompt_asset_identity.py::test_static_review_final_transport_examples_satisfy_real_verdict_validator`: media capability and target-size frame coverage issues (`MEDIA_CAPABILITY`, `MEDIA_FRAME_COVERAGE`).

`git diff --check`: exit 0, no output. No full suite rerun; this task's requested verification is focused, with concurrent media work owned separately. These local results establish instruction delivery and compatibility, not compliance of a freshly generated paid-model lesson.
