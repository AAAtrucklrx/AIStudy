# Task 1 delivery: local and supported Harness account transports

Baseline: 8cec01c. Implementation reviewed against installed Harness 0.2.2-rc.1, not an assumed web API. Work confined to provider/gateway/configuration factory, package data, and transport tests.

## RED / GREEN

Initial worker baseline `tests/test_dsh_account_transport.py`: **8 failed**, all ModuleNotFoundError for missing dsh_account; 0.07 s. No production code existed at that point. New local endpoint/routing tests: **6 failed**, missing local_compatible/routing; 0.65 s. After implementation both suites: **14 passed**. Subsequent regression and coverage additions: **79 passed in 3.29 s** with:

`PYTHONPATH="$PWD/src:$PWD:$PWD/tests:$PWD/tests/integration:$PWD/tests/support" '/Users/huang/Documents/ChatGPT/ai for study项目的改进/.venv-linux/bin/python' -m pytest tests/test_dsh_account_transport.py tests/test_local_role_transport.py tests/test_transport_failure_diagnostics.py tests/test_unlimited_transport.py tests/contracts/test_m10_real_transport.py tests/test_json_only_gateway.py -q`

Broader transport selection: 97 passed, 2 failed. Both failures independently reproduced with unmodified `git archive 8cec01c` in `/tmp/aifs-task1-baseline`: (1) old `test_slow_socket_cancel_wraps_up_within_grace` forks into macOS urllib proxy lookup and triggers ObjC safety abort; (2) old `test_protocol_correction_keeps_labels_and_images_on_the_last_user_message` expects images on syntax repair although baseline strips them. Neither was changed to make this work green.

A live final-smoke run exposed NO_ADAPTER when querying capabilities immediately after mounting Cordis plugins. Fixed by awaiting public plugin mount thenables before capability checks; offline installed-SDK tests now cover complete initialization, missing-account failure, and invalid-image-before-account failure.

## Implemented behavior

- Explicit `local-compatible` endpoint needs no DEEPSEEK_API_KEY. Anonymous access restricted to numeric loopback / localhost; embedded URL credentials, query strings, fragments and non-HTTP(S) rejected. Explicit `api_key_ref: env:NAME` supports authenticated configured endpoints; missing declared credential fails closed. Local wire sends no Authorization when unauthenticated and no DeepSeek-only thinking/JSON fields.
- Per-role `provider`, `base_url`, and `api_key_ref` override top-level values in models.json; unknown providers and missing model/endpoints rejected by factory. `deepseek-account`, `local-compatible`, legacy `deepseek` supported. Homogeneous routes retain a single transport; mixed routes use RoleTransportRouter.for_role. Gateway binds the correct role without shared mutable current-role state. Endpoint/provider identities enter new cache fingerprints without credentials. Old injected transports lacking identity keep their prior fingerprint.
- Account route composes installed public Cordis, dsh-llm, attachment-local, credentials-local, authorization, deepseek-account-platform and llm-deepseek-account packages. Uses prepareCall and its bound stream (one attempt, no retry plugin), preserving structured system/user/assistant order. It does not use the headless CLI task string, browser cookies, or private inference HTTP implementation.
- Request validation rejects tool/audio/remote images, unknown fields, missing image files and inconsistent image_labels before account access. Actual local image bytes become SDK attachments; both bundled and prepared-model capabilities are checked before model dispatch, so text-only image placeholder fallback is prohibited. SDK validates/normalizes images and may create route-specific resized variants; original file hash evidence is not a claim that encoded wire bytes always equal original PNG bytes.
- Python controls a killable Electron Node worker. Input/response cross pipes; SDK stderr is discarded; errors expose stable uppercase codes only. A TemporaryDirectory (0700) holds only required account/device records (0600), no refs or browser-session record. DSH_HOME and credentials path point there. macOS sandbox-exec denies writes to original account home even on SDK 401 cleanup. Temporary storage is removed after success/failure/cancel. Original account stays out of project env/config/logs.
- Usage is SDK-supplied: prompt = inputTokens + cacheReadTokens + cacheWriteTokens; output = outputTokens; total is their sum only if both present. This matches installed adapter translation around usage.totalTokens. No token estimation, missing counters remain absent. Raw visible response text is preserved; terminal max-tokens maps to length. Other non-stop terminal results fail closed. Calls counts successful completed responses, matching legacy RealTransport; gateway owns attempts.
- `providers/*.cjs` added to wheel package data so installed Python package retains the bridge.

## Live evidence (fixed non-sensitive prompts, no credentials printed)

All live requests used actual deepseek-account / deepseek-flash. The local HTTP test is an actual loopback socket against a controlled compatibility fixture, **not evidence of a resident local inference model**.

1. Local fixture: system/user sequence + labeled PNG data URL received; no Authorization, thinking, reasoning_effort or response_format; provider fixture usage 17+4=21 retained; calls=1/image_calls=1. Endpoint cache isolation and switched-role gateway cache test passed. Local cancellation returns in <2 s, remote_unconfirmed true, successful calls 0.
2. Initial account marker experiments returned literal `AIFS_SQuestion` (17 input, 5 output, total22), then literal `SDK_CON//` (19 input, 4 output, total23) despite requested markers. These are imperfect model outputs, **not marker-verification successes**; no substitution was made.
3. Multi-turn system → user 2+3 → assistant five → user multiply previous by4 returned exactly `The answer is twenty.`; input63/output31/total94, stop, proving useful semantic multi-turn output.
4. Final short text after awaited initialization: `What is 7 times 8?` returned `7 times 8 equals 56.`; input44/output20/total64, stop.
5. Controlled image 400×240 white canvas, red rectangle left, blue circle right; source PNG SHA-256 a2626eae79346f097d60035f473b6a0ab14cdb4c072eb8435fb2e0b64ecccf6a. First actual image response: `Based on the image, the two colored shapes from left to right are:\n\n1.  A **red rectangle** (or square)\n2.  A **blue circle**`; input290/output35/total325, calls2/image_calls1 on that shared text+image client. Labels supplied separately before image part.
6. Actual account cancellation at timer1.0 s on long max-effort prompt returned Cancelled after1.037 s; successful calls0, remote_unconfirmed=True. This proves local SDK worker termination, **not remote billing cancellation**.
7. Original `.credentials.yaml`, home patch, desktop patch and headless patch existence/hashes unchanged before/after first text+image run; original credential hash also unchanged after multi-turn/cancel. No credential contents or hashes printed. Final run results appended below.

## Reproduction (already installed Harness, saved account, no key needed)

From repository, set PYTHONPATH to its src plus repository root and run Python:

    from aiforstudy.providers.dsh_account import DshAccountTransport
    client = DshAccountTransport(model='deepseek-flash')
    text, usage = client(model='deepseek-flash', effort='high',
        messages=[{'role':'system','content':'Answer in a short sentence.'},
                  {'role':'user','content':'What is 7 times 8?'}],
        images=None, max_tokens=256, timeout=30)
    print(text, usage)  # fixed synthetic prompt/output only

For image: use a real PNG/JPEG/WebP/GIF path in images and a user image_labels list matching it; SDK admission rejects fake PNG bytes. Local route config example: top-level provider `deepseek-account`, lesson model `deepseek-flash`; media role provider `local-compatible`, model matching the local service, base_url `http://127.0.0.1:8000/v1`. No local inference service was discovered/tested at that example endpoint; do not advertise its existence.

## Limits

Account bridge currently requires macOS installed Harness plus sandbox-exec; other platforms fail ACCOUNT_BRIDGE_RUNTIME_UNAVAILABLE rather than handling credentials without write protection. Bound to installed SDK vocabulary; future upgrades need contract smoke verification. SDK may normalize/resize source images. Model output correctness and JSON formatting remain higher-level protocol concerns. Account auth state changes outside this process can still invalidate a future request. Mixed provider router intentionally has no single global network-health probe because endpoints differ; direct bounded worker calls/cancellation work, while homogeneous legacy cloud configurations retain old global probe behavior. Do not claim unlimited availability, free quota, or confirmed remote cancellation. No model config defaults were changed to point at an unverified local model.

Final image/cancel rerun after all bridge initialization changes: exact visible response `Red rectangle, blue circle.`; provider input316/output76/total392 (output counter includes provider reasoning, so it is not a count of the short visible sentence), finish stop; calls1/image_calls1 and matching source hash. Cancellation again1.037 s, remote_unconfirmed=True, calls0. All four original account/config files unchanged; temporary `aifs-account-*` homes remaining:0.
